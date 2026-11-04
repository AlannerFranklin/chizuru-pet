import sys
import av
import numpy as np

path = sys.argv[1]
start = float(sys.argv[2]) if len(sys.argv) > 2 else 1200
end = float(sys.argv[3]) if len(sys.argv) > 3 else 2000
BAND = (940, 1080, 200, 1700)   # y0,y1,x0,x1

c = av.open(path)
s = c.streams.video[0]
fps = float(s.average_rate)
last = -1
buckets = {}
for f in c.decode(s):
    if f.pts is None:
        continue
    t = float(f.pts * s.time_base)
    if t < start:
        continue
    if t > end:
        break
    sec = int(t)
    if sec == last:
        continue
    last = sec
    a = f.to_ndarray(format="rgb24")[BAND[0]:BAND[1], BAND[2]:BAND[3], :].astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    pink = int(((r > 190) & (g < 140) & (b < 180) & (r - g > 60)).sum())
    white = int(((r > 225) & (g > 225) & (b > 225)).sum())
    buckets[sec] = (pink, white)

secs = sorted(buckets)
for i in range(0, len(secs), 10):
    chunk = secs[i:i + 10]
    p = sum(buckets[s][0] for s in chunk)
    w = sum(buckets[s][1] for s in chunk)
    print(f"{chunk[0]:5d}-{chunk[-1]:5d}  pink={p:6d}  white={w:6d}")
