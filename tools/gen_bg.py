"""用本地 ComfyUI 生成千鹤视频用的场景背景（无人物的二次元场景）。
用法: python gen_bg.py [--n 6]
"""
import json
import pathlib
import sys
import time
import urllib.request
import uuid

HOST = "http://127.0.0.1:8188"
OUT = pathlib.Path(r"E:\RentAGirl\out\ai_bg")
OUT.mkdir(parents=True, exist_ok=True)
CKPT = "Counterfeit-V2.5_fp16.safetensors"

POS = [
    "empty japanese city street at night, neon signs, wet asphalt reflections, no people, anime background, cinematic lighting, highly detailed",
    "theater stage with red curtains and a single spotlight, empty stage, anime background, dramatic lighting, detailed",
    "cozy cafe interior, warm afternoon sunlight through windows, empty tables, anime background, detailed",
    "small japanese apartment room in the evening, warm lamp light, bookshelf and window, anime background, detailed",
    "train station platform at dusk, cherry blossom petals falling, no people, anime background, soft light",
    "rooftop at sunset, city skyline, warm orange sky, no people, anime background, detailed",
    "backstage dressing room with mirrors and lights, no people, anime background, detailed",
    "quiet river bank at night, distant city lights, no people, anime background, detailed",
]
NEG = ("people, human, 1girl, 1boy, text, watermark, signature, letters, lowres, blurry, "
       "bad anatomy, extra limbs, deformed, worst quality")


def post(path, data):
    req = urllib.request.Request(HOST + path, data=json.dumps(data).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def get(path):
    with urllib.request.urlopen(HOST + path, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def build(prompt, seed):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 832, "height": 480, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 28, "cfg": 7.0,
            "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0,
            "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0]}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "chizuru_bg"}},
    }


def main():
    n = 6
    if "--n" in sys.argv:
        n = int(sys.argv[sys.argv.index("--n") + 1])
    done = []
    for i, p in enumerate(POS[:n]):
        cid = str(uuid.uuid4())
        seed = int(time.time()) % 100000 + i * 37
        wf = build(p, seed)
        try:
            r = post("/prompt", {"prompt": wf, "client_id": cid})
            pid = r["prompt_id"]
        except Exception as e:
            print("提交失败:", e)
            continue
        print(f"[{i+1}/{n}] 生成中… {p[:40]}", flush=True)
        img = None
        for _ in range(120):
            time.sleep(2)
            try:
                h = get(f"/history/{pid}")
            except Exception:
                continue
            if pid in h:
                outs = h[pid].get("outputs", {})
                for node in outs.values():
                    for im in node.get("images", []):
                        img = im
                break
        if not img:
            print("  失败/超时", flush=True)
            continue
        q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img.get("subfolder", ""),
                                    "type": img.get("type", "output")})
        try:
            with urllib.request.urlopen(f"{HOST}/view?{q}", timeout=60) as r:
                data = r.read()
            p2 = OUT / f"bg_{i:02d}.png"
            p2.write_bytes(data)
            print("  保存:", p2.name, flush=True)
            done.append(str(p2))
        except Exception as e:
            print("  下载失败:", e, flush=True)
    print("DONE:", len(done))


if __name__ == "__main__":
    import urllib.parse
    main()
