"""日系杂志风格的网页动画视频（米白纸感 + 衬线大字 + 垂直排版）。"""
import argparse
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(r"E:\RentAGirl")
OUT = ROOT / "out" / "videos"
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
PHOTO = ROOT / "assets_web" / "web_00.png"
SRT = OUT / "subs2.srt"
VOICE = OUT / "voice2.wav"
BGM = ROOT / "bgm"
W, H = 1920, 1080

HTML = r"""<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:#f6f1e7;
  font-family:"Yu Mincho","MS Mincho","Source Han Serif SC","SimSun",serif;color:#2a2622}
#stage{position:relative;width:1920px;height:1080px;background:
  radial-gradient(ellipse at 20% 10%, #fffaf0 0%, #f6f1e7 45%, #efe7d8 100%)}
.grain{position:absolute;inset:0;opacity:.05;mix-blend-mode:multiply;
  background-image:radial-gradient(#000 0.6px, transparent 0.7px);background-size:5px 5px}
.frame{position:absolute;right:150px;top:120px;width:600px;height:820px;
  background:#fff;padding:18px 18px 62px;box-shadow:0 30px 60px rgba(60,40,30,.18);
  transform-origin:50% 100%}
.frame img{width:100%;height:100%;object-fit:cover;object-position:50% 18%}
.cap{position:absolute;left:20px;bottom:20px;font-size:15px;letter-spacing:.28em;color:#8a7f74}
.masthead{position:absolute;left:130px;top:96px}
.masthead .jp{font-size:26px;letter-spacing:.9em;color:#b5475b}
.masthead .en{font-size:15px;letter-spacing:.42em;color:#8a7f74;margin-top:10px}
.rule{position:absolute;height:1.5px;background:#2a2622;opacity:.75}
.title{position:absolute;left:126px;top:210px;font-size:118px;line-height:1.05;font-weight:600;
  letter-spacing:.04em}
.title small{display:block;font-size:34px;letter-spacing:.5em;color:#8a7f74;margin-top:18px;font-weight:400}
.vert{position:absolute;right:20px;top:150px;writing-mode:vertical-rl;font-size:30px;
  letter-spacing:.42em;color:#3a342e;opacity:.9}
.num{position:absolute;right:130px;bottom:96px;font-size:16px;letter-spacing:.3em;color:#8a7f74}
.quote{position:absolute;left:130px;bottom:180px;max-width:1160px}
.quote .zh{font-size:50px;line-height:1.5;font-weight:600;letter-spacing:.01em;text-wrap:balance}
.quote .ja{font-size:26px;line-height:1.7;color:#6b625a;margin-top:22px;letter-spacing:.04em}
.quote .mark{position:absolute;left:-64px;top:-24px;font-size:110px;color:#b5475b;opacity:.35}
.cover{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;
  align-items:center;background:#f6f1e7}
.cover .big{font-size:190px;letter-spacing:.12em;font-weight:700}
.cover .sub{margin-top:28px;font-size:36px;letter-spacing:.62em;color:#b5475b}
.cover .line{width:340px;height:2px;background:#2a2622;opacity:.7;margin-top:52px}
.cover .tiny{position:absolute;bottom:90px;font-size:16px;letter-spacing:.4em;color:#8a7f74}
.bar{position:absolute;left:130px;bottom:120px;width:520px;height:2px;background:rgba(42,38,34,.18)}
.bar i{display:block;height:100%;background:#b5475b;width:0}
</style></head><body><div id="stage">
 <div class="grain"></div>
 <div class="frame" id="frame"><img id="photo" src="PHOTO_SRC"><div class="cap">MIZUHARA CHIZURU</div></div>
 <div class="masthead"><div class="jp">水原千鶴</div><div class="en">A QUIET ISSUE — 2026</div></div>
 <div class="rule" id="rule1" style="left:130px;top:190px;width:0"></div>
 <div class="title" id="titleBig">水原千鶴<small>MIZUHARA CHIZURU</small></div>
 <div class="vert" id="vert">千鶴の、ふつうの一日。</div>
 <div class="quote" id="quote"><div class="mark">“</div><div class="zh" id="qzh"></div><div class="ja" id="qja"></div></div>
 <div class="bar"><i id="barfill"></i></div>
 <div class="num" id="num">01 / 09</div>
 <div class="cover" id="cover"><div class="big">水原千鶴</div><div class="sub">はじめまして</div>
   <div class="line"></div><div class="tiny">RENT-A-GIRLFRIEND — A SHORT FILM</div></div>
</div>
<script>
const T = TIMELINE_JSON;
const E = id => document.getElementById(id);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const ease=t=>1-Math.pow(1-t,3);
function renderAt(t){
  const total=T.total, lines=T.lines, intro=2.0;
  const ci = clamp(t/intro,0,1);
  E('cover').style.opacity = t<intro ? (t<0.3? ci/0.3 : (t>intro-0.4? (intro-t)/0.4:1)) : 0;
  E('cover').style.display = t<intro ? 'flex':'none';
  E('cover').style.transform = `translateY(${(1-ease(ci))*24}px)`;

  let cur=null,idx=-1;
  for(let i=0;i<lines.length;i++){
    const L=lines[i], next=lines[i+1]?lines[i+1].start:total;
    if(t>=L.start-0.3 && t<next){cur=L;idx=i;break;}
  }
  const on = t>intro;
  const k = cur? clamp((t-(cur.start-0.3))/0.55,0,1) : 0;
  E('quote').style.opacity = on&&cur? ease(k):0;
  E('quote').style.transform = `translateY(${(1-ease(k))*26}px)`;
  if(cur){
    E('qzh').textContent = cur.zh;
    E('qja').textContent = cur.ja;
    E('num').textContent = String(idx+1).padStart(2,'0')+' / '+String(lines.length).padStart(2,'0');
  }
  E('masthead') && (E('masthead').style.opacity = on?1:0);
  E('titleBig').style.opacity = on? Math.max(0, 1-(t-2.2)*0.9) : 0;
  E('titleBig').style.transform = `translateY(${-Math.min(60,(t-2.2)*40)}px)`;
  E('rule1').style.width = (on? clamp((t-2.2)*420,0,760):0)+'px';
  E('vert').style.opacity = on? .9 : 0;
  E('vert').style.transform = `translateY(${Math.sin(t*0.5)*6}px)`;

  const zs = 1+0.02*Math.sin(t*0.35);
  E('frame').style.transform = `rotate(${(-1.2+0.5*Math.sin(t*0.3)).toFixed(2)}deg) scale(${zs})`;
  E('frame').style.opacity = t<1? clamp(t/0.9,0,1):1;

  E('barfill').style.width = clamp(t/total,0,1)*100+'%';
}
window.renderAt=renderAt; renderAt(0);
</script></body></html>
"""


def parse_srt(p):
    blocks = [b.strip() for b in p.read_text(encoding="utf-8").split("\n\n") if b.strip()]
    out = []

    def sec(s):
        hh, mm, rest = s.split(":")
        ss, ms = rest.split(",")
        return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000

    for b in blocks:
        ls = b.splitlines()
        m = re.match(r"(\S+)\s*-->\s*(\S+)", ls[1]) if len(ls) > 1 else None
        if not m:
            continue
        out.append({"start": sec(m.group(1)), "end": sec(m.group(2)),
                    "zh": ls[2] if len(ls) > 2 else "", "ja": ls[3] if len(ls) > 3 else ""})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()

    lines = parse_srt(SRT)
    total = max(l["end"] for l in lines) + 1.2
    html = HTML.replace("PHOTO_SRC", PHOTO.as_uri())
    html = html.replace("TIMELINE_JSON", json.dumps({"lines": lines, "total": total}, ensure_ascii=False))
    p = OUT / "magazine.html"
    p.write_text(html, encoding="utf-8")

    out = pathlib.Path(args.out) if args.out else OUT / "intro_magazine.mp4"
    frames = OUT / "frames_m"
    frames.mkdir(exist_ok=True)
    for f in frames.glob("*.png"):
        f.unlink()

    from playwright.sync_api import sync_playwright
    n = int(total * args.fps)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(p.as_uri())
        page.wait_for_timeout(800)
        for i in range(n):
            page.evaluate(f"window.renderAt({i/args.fps})")
            page.screenshot(path=str(frames / f"f{i:05d}.png"))
            if i % 200 == 0:
                print("frame", i, "/", n, flush=True)
        browser.close()

    bgm = sorted(BGM.glob("*.mp3"))
    fc = "[1:a]adelay=2000:all=1,volume=1.0[vo]"
    cmd = [FFMPEG, "-y", "-framerate", str(args.fps), "-i", str(frames / "f%05d.png"), "-i", str(VOICE)]
    if bgm:
        cmd += ["-stream_loop", "-1", "-i", str(bgm[0])]
        fc += (f";[2:a]volume=0.26,afade=t=in:st=0:d=1.2,"
               f"afade=t=out:st={max(0,total-4):.2f}:d=4[bg];[vo][bg]amix=inputs=2:duration=first[a]")
    else:
        fc += ";[vo]anull[a]"
    cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}", "-vsync", "cfr", "-r", str(args.fps),
            "-c:v", "h264_mf", "-b:v", "10M", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", str(out)]
    print("编码中…", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="ignore", creationflags=0x08000000)
    if r.returncode != 0:
        print("ffmpeg 失败", (r.stderr or "")[-800:])
        return
    print("完成:", out, flush=True)


if __name__ == "__main__":
    main()
