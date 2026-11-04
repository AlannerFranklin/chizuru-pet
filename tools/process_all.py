"""批量处理 raw\\ 下所有集：检测正片结束 -> 裁剪 -> 日文 ASR(word) -> 字幕 OCR -> out\\<ep>.jsonl

两段式，避免 GPU 争抢：
  --stage asr    只做 ASR，串行独占 GPU（~2 分钟/集）
  --stage full   OCR 段，可多进程并行（--shard i --shards n）

续跑规则：
  out\\<ep>.asr.json 存在 -> 跳过 ASR
  out\\<ep>.jsonl 存在   -> 整集跳过
"""
import argparse, json, pathlib, sys, time
import numpy as np
import av

REPO = pathlib.Path(r"E:\RentAGirl")
RAW = REPO / "raw"
OUT = REPO / "out"
LOG = OUT / "batch.log"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from detect_cut import scan as scan_pink, PINK_PER_FRAME, TAIL_PAD
from process_episode import decode, GLOSSARY

SR = 16000
CROP = [400, 950, 1520, 1080]
LINE_GAP = 0.5
MIN_LINE_CHARS = 2

_ocr = None
_model = None


def log(msg):
    line = f"{time.strftime('%H:%M:%S')}  {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_model(path):
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(path, device="cuda", compute_type="float16")
    return _model


def get_ocr():
    global _ocr
    if _ocr is None:
        from rapidocr import RapidOCR
        _ocr = RapidOCR()
    return _ocr


def split_lines(segments):
    lines = []
    for seg in segments:
        words = seg["words"]
        if not words:
            if seg["text"].strip():
                lines.append({"start": seg["start"], "end": seg["end"], "ja": seg["text"].strip()})
            continue
        cur = [words[0]]
        for w in words[1:]:
            if w["s"] - cur[-1]["e"] >= LINE_GAP:
                lines.append({"start": cur[0]["s"], "end": cur[-1]["e"],
                              "ja": "".join(x["w"] for x in cur).strip()})
                cur = [w]
            else:
                cur.append(w)
        lines.append({"start": cur[0]["s"], "end": cur[-1]["e"],
                      "ja": "".join(x["w"] for x in cur).strip()})
    return [l for l in lines if len(l["ja"]) >= MIN_LINE_CHARS]


def get_cut(src, ep):
    cache = OUT / f"{ep}.cut.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))["cut_s"]
    series = scan_pink(src, 1000.0)
    hits = [t for t, p in series if p >= PINK_PER_FRAME]
    cut = (hits[-1] + TAIL_PAD) if hits else 1470.0
    cache.write_text(json.dumps({"cut_s": round(cut, 1), "pink_hits": len(hits)}, ensure_ascii=False),
                     encoding="utf-8")
    return cut


def do_asr(ep, model_path):
    cache = OUT / f"{ep}.asr.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    src = RAW / f"{ep}.mp4"
    cut = get_cut(src, ep)
    log(f"{ep}: cut={cut:.1f}s")
    audio = decode(src, cut)
    model = get_model(model_path)
    t0 = time.time()
    segments, _ = model.transcribe(
        audio, language="ja", beam_size=5, vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300),
        condition_on_previous_text=False, initial_prompt=GLOSSARY,
        word_timestamps=True,
    )
    segs = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
             "words": [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2)}
                       for w in (s.words or [])]} for s in segments]
    lines = split_lines(segs)
    cache.write_text(json.dumps(lines, ensure_ascii=False), encoding="utf-8")
    log(f"{ep}: asr {len(segs)} segs -> {len(lines)} lines in {time.time()-t0:.0f}s")
    return lines


def do_ocr(ep, lines):
    src = RAW / f"{ep}.mp4"
    targets = {}
    for l in lines:
        mid = (l["start"] + l["end"]) / 2
        targets[round(mid, 2)] = mid
    engine = get_ocr()
    got = {}
    c = av.open(str(src))
    vs = c.streams.video[0]
    order = sorted(targets.items())
    idx = 0
    for frame in c.decode(vs):
        if frame.pts is None:
            continue
        t = float(frame.pts * vs.time_base)
        if t > order[-1][1] + 1.0:
            break
        while idx < len(order) and t >= order[idx][1]:
            key, mid = order[idx]
            if key not in got:
                got[key] = frame.to_ndarray(format="rgb24")[CROP[1]:CROP[3], CROP[0]:CROP[2], :].copy()
            idx += 1
    c.close()
    n = 0
    for l in lines:
        key = round((l["start"] + l["end"]) / 2, 2)
        img = got.get(key)
        zh, score = "", 0.0
        if img is not None:
            a = img.astype(int)
            r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
            ink = (((r > 210) & (g > 200) & (b > 200)) |
                   ((r > 190) & (g < 140) & (b < 180) & (r - g > 60)))
            if int(ink.sum()) >= 600:      # 没字幕的帧直接跳过 OCR
                # 只做识别，不做检测：字幕是单行居中，检测是最大开销（1051ms -> 57ms）
                res = engine(img, use_det=False, use_cls=False, use_rec=True)
                txts = getattr(res, "txts", None)
                scs = getattr(res, "scores", None)
                if isinstance(txts, str):
                    txts = (txts,)
                if txts is None:
                    txts = ()
                if scs is None:
                    scs = (1.0,) * len(txts)
                elif isinstance(scs, (int, float)):
                    scs = (float(scs),)
                pairs = [(x, y) for x, y in zip(txts, scs) if y >= 0.6]
                if pairs:
                    zh = "".join(p[0] for p in pairs).strip()
                    score = float(min(p[1] for p in pairs))
        l["zh"] = zh
        l["zh_score"] = round(score, 3)
        n += 1
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--stage", default="full", choices=["asr", "full"])
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--model", default=r"E:\test\rentagirl\models\faster-whisper-large-v3")
    ap.add_argument("--crop-top", type=int, default=950, help="字幕带顶部 y 坐标")
    args = ap.parse_args()
    CROP[1] = args.crop_top

    OUT.mkdir(parents=True, exist_ok=True)
    eps = [args.only] if args.only else sorted(p.stem for p in RAW.glob("S*E*.mp4"))
    if args.shards > 1:
        eps = [e for i, e in enumerate(eps) if i % args.shards == args.shard]

    if args.stage == "asr":
        todo = [e for e in eps if not (OUT / f"{e}.asr.json").exists()]
        log(f"=== ASR pass: shard {args.shard}/{args.shards}, {len(todo)} pending ===")
        for i, ep in enumerate(todo, 1):
            log(f"--- asr [{i}/{len(todo)}] {ep} ---")
            try:
                do_asr(ep, args.model)
            except Exception as e:
                log(f"!! {ep} ASR FAILED: {type(e).__name__}: {e}")
        log("=== ASR pass finished ===")
        return

    todo = [e for e in eps if not (OUT / f"{e}.jsonl").exists()]
    log(f"=== OCR pass: shard {args.shard}/{args.shards}, {len(todo)} pending ===")
    for i, ep in enumerate(todo, 1):
        if not (OUT / f"{ep}.asr.json").exists():
            continue          # 等 ASR pass 先跑完这一集
        log(f"--- [{i}/{len(todo)}] {ep} ---")
        try:
            t0 = time.time()
            lines = do_asr(ep, args.model)
            lines = do_ocr(ep, lines)
            with open(OUT / f"{ep}.jsonl", "w", encoding="utf-8") as f:
                for l in lines:
                    f.write(json.dumps(l, ensure_ascii=False) + "\n")
            meta = {"ep": ep, "lines": len(lines),
                    "with_zh": sum(1 for l in lines if l.get("zh")),
                    "ja_chars": sum(len(l["ja"]) for l in lines),
                    "elapsed_s": round(time.time() - t0, 1)}
            (OUT / f"{ep}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
            log(f"{ep}: DONE {json.dumps(meta, ensure_ascii=False)}")
        except Exception as e:
            log(f"!! {ep} FAILED: {type(e).__name__}: {e}")
    log("=== OCR pass finished ===")


if __name__ == "__main__":
    main()
