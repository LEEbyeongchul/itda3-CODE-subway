# 속도 점검 (s)(t): time_check.py 와 같은 60장(무작위, random_state=7)을 4스레드로 돌려 규칙 끔/켬 장당 시간을 비교한다.
#   .venv/Scripts/python notebooks/time_reread.py [장수]   (다른 CPU 작업이 없을 때 실행)
# 구성: cur = 현재 기본값(p1det) · t = + 연·월 사이 구분자 빠짐 · s = + 깨져 읽힌 줄 다시 읽기 · st = 둘 다 · cur2 = cur 를 한 번 더 (측정 잡음 크기)
import json, os, sys, time, pandas as pd
os.environ.setdefault("ITDA_THREADS", "4")
os.environ.setdefault("ITDA_KO_LINE", "1")
os.environ.setdefault("ITDA_KO_LINE_MODE", "p1det")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__t__", "os": os}
for i in (1, 2, 3, 4, 5): exec(cells[i], g)
load_image, pass1, pass2, select_date = g["load_image"], g["pass1"], g["pass2"], g["select_date"]
J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
J = J[~J.block.isin(["1", "2", "3", "4", "5"])].sample(n=N, random_state=7)
imgs = [load_image(f"images/{f}") for f in J.file]


def run(img):
    c1, seen = pass1(img); c2 = pass2(img, c1) if c1 else []
    if g["KO_LINE"]: c2 = g["keyword_line_reread"](img, c2, seen)
    if g["RULE_REREAD"]: c2 = g["broken_line_reread"](img, c2, seen)
    return select_date(c2)


for img in imgs[:3]: run(img)   # 예열
res, ans = {}, {}
for name, (t_on, s_on) in {"cur": (False, False), "t": (True, False), "s": (False, True), "st": (True, True), "cur2": (False, False)}.items():
    g["RULE_YMSEP"], g["RULE_REREAD"] = t_on, s_on
    secs, out = [], []
    for img in imgs:
        t = time.time(); b = run(img); secs.append(time.time() - t); out.append((b["y"], b["m"], b["d"]) if b else None)
    s = pd.Series(secs); res[name] = s; ans[name] = out
    print(f"{name:5s}: 장당 평균 {s.mean():.2f}s  p90 {s.quantile(.9):.2f}s  최대 {s.max():.1f}s  ({N}장 {s.sum():.0f}s)  cur 와 답이 다른 장 {sum(a != b for a, b in zip(out, ans['cur']))}", flush=True)
for name, s in res.items():
    print(f"{name:5s} − cur: 장당 {s.mean() - res['cur'].mean():+.2f}s", flush=True)
print("done")
