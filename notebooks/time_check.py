# 속도 점검: 층화 표본(기본 60장)을 4스레드로 규칙 꺼짐/켜짐 두 번 돌려 장당 시간을 비교한다.
#   .venv/Scripts/python notebooks/time_check.py [장수]   (다른 CPU 작업이 없을 때 실행)
import json, os, sys, time, pandas as pd
os.environ.setdefault("ITDA_THREADS", "4")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__t__", "os": os}
for i in (1, 2, 3, 4, 5): exec(cells[i], g)
load_image, pass1, pass2, select_date = g["load_image"], g["pass1"], g["pass2"], g["select_date"]
FLAGS = ["P2_KEEP", "RULE_SPAN", "RULE_COLON", "RULE_TRUNC"]
J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
J = J[~J.block.isin(["1", "2", "3", "4", "5"])].sample(n=N, random_state=7)   # 판정용 2,852장에서 무작위
imgs = [load_image(f"images/{f}") for f in J.file]
res = {}
SETS = {"off": [], "keep": ["P2_KEEP"], "all4": FLAGS}
if os.environ.get("TC_SETS"): SETS = {k: v for k, v in SETS.items() if k in os.environ["TC_SETS"].split(",")}
for name, on in SETS.items():
    for f in FLAGS: g[f] = f in on
    t0 = time.time(); secs = []
    for img in imgs:
        t = time.time(); c1, _ = pass1(img); select_date(pass2(img, c1)) if c1 else None; secs.append(time.time() - t)
    s = pd.Series(secs); res[name] = s
    print(f"{name:5s}: 장당 평균 {s.mean():.2f}s  p90 {s.quantile(.9):.2f}s  최대 {s.max():.1f}s  ({N}장 {s.sum():.0f}s)", flush=True)
base = res.get("off")
for name, s in res.items():
    if base is not None and name != "off":
        d = s.mean() - base.mean(); print(f"{name} − off: 장당 {d:+.3f}s → 500장 환산 {d*500:+.0f}s")
