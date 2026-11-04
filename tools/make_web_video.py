"""用网页动画渲染视频：HTML/CSS/JS 时间线 → Playwright 逐帧截图 → ffmpeg 合成。
用法: python make_web_video.py [--out x.mp4] [--fps 30]
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(r"E:\RentAGirl")
OUT = ROOT / "out" / "videos"
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
ART = ROOT / "assets_v3" / "chizuru_main.png"
SRT = OUT / "subs.srt"
VOICE = OUT / "voice.wav"
BGM = ROOT / "bgm"
W, H, FPS = 1920, 1080, 30


def parse_srt(p):
    txt = p.read_text(encoding="utf-8")
    blocks = [b.strip() for b in txt.split("\n\n") if b.strip()]
    out = []

    def sec(s):
        hh, mm, rest = s.split(":")
        ss, ms = rest.split(",")
        return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000

    for b in blocks:
        lines = b.splitlines()
        m = re.match(r"(\S+)\s*-->\s*(\S+)", lines[1])
        if not m:
            continue
        start, end = sec(m.group(1)), sec(m.group(2))
        zh = lines[2] if len(lines) > 2 else ""
        ja = lines[3] if len(lines) > 3 else ""
        out.append({"start": start, "end": end, "zh": zh, "ja": ja})
    return out


HTML = r"""<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:#0b0a0e;
  font-family:"Microsoft YaHei","Yu Gothic UI",sans-serif}
#stage{position:relative;width:1920px;height:1080px;overflow:hidden}
.bg{position:absolute;inset:-10%;background:radial-gradient(circle at 30% 25%,#3a2230 0%,#17121a 55%,#0a090c 100%);
  transition:none}
.blob{position:absolute;border-radius:50%;filter:blur(90px);opacity:.55}
#b1{width:900px;height:900px;background:#8a3d55}
#b2{width:700px;height:700px;background:#3f3a6b}
#b3{width:600px;height:600px;background:#5c2f46}
.grid{position:absolute;inset:0;opacity:.10;
  background-image:linear-gradient(rgba(255,255,255,.25) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(255,255,255,.25) 1px,transparent 1px);
  background-size:80px 80px}
#art{position:absolute;right:60px;bottom:-30px;height:1000px;transform-origin:50% 100%}
#name{position:absolute;left:110px;top:110px;letter-spacing:.06em}
#name .zh{font-size:70px;font-weight:700;color:#fff}
#name .en{font-size:24px;color:#e0b8c4;margin-top:6px;letter-spacing:.28em}
#line{position:absolute;left:110px;top:250px;height:4px;background:#e696aa;border-radius:2px}
#card{position:absolute;left:110px;bottom:150px;max-width:1150px}
#czh{font-size:52px;line-height:1.5;color:#fff;font-weight:600;text-shadow:0 4px 30px #000}
#cja{font-size:30px;line-height:1.6;color:#e3c9d2;margin-top:14px;opacity:.92}
#title{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
#title .big{font-size:170px;font-weight:800;color:#fff;letter-spacing:.08em;
  text-shadow:0 0 60px rgba(230,150,170,.55)}
#title .sub{margin-top:26px;font-size:40px;color:#e6c2ce;letter-spacing:.5em}
#title .rule{margin-top:44px;height:3px;background:#e696aa}
#vignette{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,transparent 40%,rgba(0,0,0,.62) 100%)}
#progress{position:absolute;left:110px;bottom:70px;width:640px;height:3px;background:rgba(255,255,255,.16)}
#progress i{display:block;height:100%;background:#e696aa;width:0}
</style></head><body><div id="stage">
 <div class="bg"></div>
 <div class="blob" id="b1"></div><div class="blob" id="b2"></div><div class="blob" id="b3"></div>
 <div class="grid"></div>
 <img id="art" src="ART_SRC">
 <div id="name"><div class="zh">水原千鶴</div><div class="en">MIZUHARA CHIZURU</div></div>
 <div id="line"></div>
 <div id="card"><div id="czh"></div><div id="cja"></div></div>
 <div id="title"><div class="big">水原千鶴</div><div class="sub">はじめまして</div><div class="rule"></div></div>
 <div id="progress"><i></i></div>
 <div id="vignette"></div>
</div>
<script>
const T = TIMELINE_JSON;
const E = id => document.getElementById(id);
const clamp = (v,a,b)=>Math.max(a,Math.min(b,v));
const ease = t => 1-Math.pow(1-t,3);
function renderAt(t){
  const total = T.total;
  // 片头
  const introEnd = 2.0;
  const ti = clamp(t/introEnd,0,1);
  E('title').style.opacity = t < introEnd ? (t<0.4? ti/0.4 : (t>introEnd-0.35? (introEnd-t)/0.35 : 1)) : 0;
  E('title').style.transform = `translateY(${(1-ease(ti))*40}px)`;
  E('title').style.display = t < introEnd ? 'flex' : 'none';

  // 逐句
  const lines = T.lines;
  let cur = null, idx = -1;
  for (let i=0;i<lines.length;i++){
    const L = lines[i];
    const next = lines[i+1] ? lines[i+1].start : total;
    if (t >= L.start - 0.25 && t < next) { cur = L; idx = i; break; }
  }
  const showCard = !!cur && t > introEnd;
  E('card').style.opacity = showCard ? 1 : 0;
  if (cur){
    const k = clamp((t - (cur.start-0.25))/0.5, 0, 1);
    E('czh').textContent = cur.zh;
    E('cja').textContent = cur.ja;
    E('card').style.transform = `translateY(${(1-ease(k))*28}px)`;
    E('czh').style.opacity = ease(k);
    E('cja').style.opacity = ease(k)*0.95;
  }
  // 名字与线
  const nk = clamp((t-0.2)/0.8,0,1);
  E('name').style.opacity = t < introEnd ? 0 : nk;
  E('line').style.width = (t<introEnd?0:(120 + 60*Math.sin(t*1.4))) + 'px';
  E('line').style.opacity = t < introEnd ? 0 : 1;

  // 立绘：轻微呼吸 + 视差
  const breathe = 1 + 0.006*Math.sin(t*1.5);
  const drift = Math.sin(t*0.6)*10;
  E('art').style.transform = `translate(${drift}px, ${Math.sin(t*1.5)*6}px) scale(${breathe})`;
  E('art').style.opacity = t < 1.2 ? clamp((t-0.6)/0.8,0,1) : 1;

  // 背景色相缓慢漂移
  const hue = 320 + 40*Math.sin(t*0.18);
  E('b1').style.transform = `translate(${Math.sin(t*0.5)*120}px, ${Math.cos(t*0.4)*80}px)`;
  E('b2').style.transform = `translate(${Math.cos(t*0.33)*140}px, ${Math.sin(t*0.45)*100}px)`;
  E('b3').style.transform = `translate(${Math.sin(t*0.27)*90}px, ${Math.cos(t*0.37)*120}px)`;
  document.querySelector('.bg').style.filter = `hue-rotate(${hue-320}deg)`;

  // 进度条
  const p = clamp(t/total,0,1);
  document.querySelector('#progress i').style.width = (p*100)+'%';
}
window.renderAt = renderAt;
renderAt(0);
</script></body></html>
"""


def build_html(lines, total):
    html = HTML.replace("ART_SRC", ART.as_uri())
    html = html.replace("TIMELINE_JSON", json.dumps({"lines": lines, "total": total}, ensure_ascii=False))
    p = OUT / "webvideo.html"
    p.write_text(html, encoding="utf-8")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--lead", type=float, default=0.4)
    args = ap.parse_args()

    lines = parse_srt(SRT)
    total = max(l["end"] for l in lines) + 1.2
    html = build_html(lines, total)
    out = pathlib.Path(args.out) if args.out else OUT / "intro_web.mp4"

    from playwright.sync_api import sync_playwright
    frames_dir = OUT / "frames"
    frames_dir.mkdir(exist_ok=True)
    for f in frames_dir.glob("*.png"):
        f.unlink()

    n = int(total * args.fps)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(html.as_uri())
        page.wait_for_timeout(600)
        for i in range(n):
            t = i / args.fps
            page.evaluate(f"window.renderAt({t})")
            page.screenshot(path=str(frames_dir / f"f{i:05d}.png"))
            if i % 150 == 0:
                print(f"frame {i}/{n}", flush=True)
        browser.close()

    bgm_files = sorted(BGM.glob("*.mp3"))
    bgm = bgm_files[0] if bgm_files else None
    fc = f"[1:a]volume=1.0[vo]"
    if bgm:
        fc += (f";[2:a]volume=0.16,afade=t=in:st=0:d=2.5,"
               f"afade=t=out:st={max(0,total-4):.2f}:d=4[bg];[vo][bg]amix=inputs=2:duration=first[a]")
    else:
        fc += ";[vo]anull[a]"
    cmd = [FFMPEG, "-y", "-framerate", str(args.fps), "-i", str(frames_dir / "f%05d.png"),
           "-i", str(VOICE)]
    if bgm:
        cmd += ["-stream_loop", "-1", "-i", str(bgm)]
    cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]",
            "-t", f"{total:.2f}", "-c:v", "h264_mf", "-b:v", "10M",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", str(out)]
    print("编码中…", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="ignore", creationflags=0x08000000)
    if r.returncode != 0:
        print("ffmpeg 失败", (r.stderr or "")[-800:])
        return
    print("完成:", out, flush=True)


if __name__ == "__main__":
    main()
