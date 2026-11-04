"""单集处理：解码 -> 裁掉片尾 B 站过审片段 -> 日文 ASR。
用法: python process_episode.py S01E01 [--cut 1470] [--model DIR]
输出: work/<ep>/audio16k.npy, asr.jsonl, meta.json
"""
import argparse, json, pathlib, sys, time
import numpy as np
import av
from faster_whisper import WhisperModel

SR = 16000
GLOSSARY = ("水原千鶴、木ノ下和也、七海麻美、更科瑠夏、八重森弥妮、"
            "彼女、お借りします、レンタル彼女、練馬大学、Diamond")

REPO = pathlib.Path(r"E:\RentAGirl")


def decode(path, cut_s):
    container = av.open(str(path))
    stream = container.streams.audio[0]
    resampler = av.AudioResampler(format="flt", layout="mono", rate=SR)
    chunks = []
    limit = int(cut_s * SR)
    for frame in container.decode(stream):
        for rf in resampler.resample(frame):
            chunks.append(rf.to_ndarray().reshape(-1))
    audio = np.concatenate(chunks).astype(np.float32)
    if limit < audio.size:
        audio = audio[:limit]
    return audio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--cut", type=float, default=None)
    ap.add_argument("--model", default=r"E:\test\rentagirl\models\faster-whisper-large-v3")
    args = ap.parse_args()

    work = REPO / "work" / args.ep
    work.mkdir(parents=True, exist_ok=True)
    src = REPO / "raw" / f"{args.ep}.mp4"
    meta_path = REPO / "raw" / ".meta" / f"{args.ep}.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8-sig")) if meta_path.exists() else {}
    if args.cut:
        cut = args.cut
        cut_src = "cli"
    else:
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        from detect_cut import scan, PINK_PER_FRAME, TAIL_PAD
        series = scan(src, 1000.0)
        hits = [t for t, p in series if p >= PINK_PER_FRAME]
        if hits:
            cut = hits[-1] + TAIL_PAD
            cut_src = f"auto(pink_sub={hits[-1]:.1f})"
        else:
            cut = meta.get("cut_s") or 1470
            cut_src = "fallback"
    print(f"cut={cut:.1f}s ({cut_src})", flush=True)

    t0 = time.time()
    audio = decode(src, cut)
    np.save(work / "audio16k.npy", audio)
    print(f"decoded {audio.size/SR:.1f}s (cut at {cut}s) in {time.time()-t0:.1f}s", flush=True)

    model = WhisperModel(args.model, device="cuda", compute_type="float16")
    t0 = time.time()
    segments, _ = model.transcribe(
        audio, language="ja", beam_size=5, vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300),
        condition_on_previous_text=False, initial_prompt=GLOSSARY,
    )
    rows = []
    with open(work / "asr.jsonl", "w", encoding="utf-8") as f:
        for s in segments:
            r = {"start": round(s.start, 2), "end": round(s.end, 2),
                 "text": s.text.strip(), "avg_logprob": round(s.avg_logprob, 3)}
            rows.append(r)
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    elapsed = time.time() - t0
    last_end = rows[-1]["end"] if rows else 0
    summary = {
        "ep": args.ep, "cut_s": cut, "audio_s": round(audio.size / SR, 1),
        "segments": len(rows), "last_speech_end": last_end,
        "asr_elapsed_s": round(elapsed, 1),
        "rtf": round(audio.size / SR / elapsed, 1) if elapsed else None,
    }
    (work / "meta.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
