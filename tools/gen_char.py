"""生成"千鹤在场景里"的插画（按台词配图）。
用法: python gen_char.py [--n 6]
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request
import uuid

HOST = "http://127.0.0.1:8188"
OUT = pathlib.Path(r"E:\RentAGirl\out\ai_char")
OUT.mkdir(parents=True, exist_ok=True)
CKPT = "Counterfeit-V2.5_fp16.safetensors"

CHAR = ("mizuhara chizuru, 1girl, solo, long brown hair, brown eyes, "
        "white summer dress, looking at viewer, upper body")

SCENES = [
    "on a theater stage, red curtains behind, spotlight, standing",
    "walking on a japanese street at night, lanterns, warm light",
    "sitting in a cozy cafe, window light, coffee cup",
    "in a japanese tatami room, warm lamp, evening",
    "at a train station platform at dusk, cherry blossoms",
    "on a rooftop at sunset, city skyline behind",
]

NEG = ("lowres, bad anatomy, bad hands, extra fingers, missing fingers, text, watermark, "
       "signature, worst quality, low quality, multiple girls, 2girls, blurry, deformed")


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
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 640, "height": 960, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 30, "cfg": 7.5,
            "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0,
            "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0]}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "chizuru_char"}},
    }


def main():
    n = 6
    seed_base = 771122
    for i in range(n):
        prompt = CHAR + ", " + SCENES[i % len(SCENES)] + ", anime style, masterpiece, highly detailed, depth of field"
        cid = str(uuid.uuid4())
        try:
            r = post("/prompt", {"prompt": build(prompt, seed_base + i), "client_id": cid})
            pid = r["prompt_id"]
        except Exception as e:
            print("提交失败", e)
            continue
        print(f"[{i+1}/{n}] {SCENES[i % len(SCENES)][:34]}", flush=True)
        img = None
        for _ in range(150):
            time.sleep(2)
            try:
                h = get(f"/history/{pid}")
            except Exception:
                continue
            if pid in h:
                for node in h[pid].get("outputs", {}).values():
                    for im in node.get("images", []):
                        img = im
                break
        if not img:
            print("  超时/失败", flush=True)
            continue
        q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img.get("subfolder", ""),
                                    "type": img.get("type", "output")})
        with urllib.request.urlopen(f"{HOST}/view?{q}", timeout=60) as r:
            (OUT / f"char_{i:02d}.png").write_bytes(r.read())
        print("  保存 char_%02d.png" % i, flush=True)


if __name__ == "__main__":
    if "--n" in sys.argv:
        pass
    main()
