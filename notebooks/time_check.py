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
FLAGS = ["P2_KEEP", "RULE_SPAN", "RULE_COLON", "RULE_TRUNC", "P2_VOTE640", "KO_KEYWORD", "KO_LINE"]
DEFAULTS = {f: g.get(f, False) for f in FLAGS}
DEFAULTS["KO_LINE"] = DEFAULTS["KO_KEYWORD"] = DEFAULTS["P2_VOTE640"] = False   # 실험 플래그는 env 로 켜져 있어도 "cur" 에선 끈다 (인식기 로드용 env 와 분리)
J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
J = J[~J.block.isin(["1", "2", "3", "4", "5"])].sample(n=N, random_state=7)   # 판정용 2,852장에서 무작위
imgs = [load_image(f"images/{f}") for f in J.file]
res = {}
RULES4 = ["RULE_SEPMIX", "RULE_TAIL", "RULE_YMSEP", "RULE_REREAD"]   # (q)(r)(s)(t), 9/27
FLAGS += [f for f in RULES4 if f in g]; DEFAULTS.update({f: g[f] for f in RULES4 if f in g})
MODE0 = g.get("KO_LINE_MODE")
SETS = {"off": [], "keep": ["P2_KEEP"], "all4": FLAGS[:4], "cur": None, "kol": ["KO_LINE"],   # cur = 노트북 기본값, kol = 기본값 + 한국어 2차 의견
        "auto": ["KO_LINE", "KO_LINE_MODE=auto"],                       # 한국어 2차 의견 조건부 모드 (날짜 조각 2개 이상인 줄이 있는 장만 det960)
        "fin1": ["KO_LINE"] + RULES4,                                   # 네 규칙 + p1det
        "fin": ["KO_LINE", "KO_LINE_MODE=auto"] + RULES4}               # 네 규칙 + 조건부 모드 (9/28 최종 구성 후보)
STACK = ("kol", "auto", "fin1", "fin")   # 기본값 위에 얹는 구성
if os.environ.get("TC_SETS"): SETS = {k: v for k, v in SETS.items() if k in os.environ["TC_SETS"].split(",")}
def apply(name):
    on = SETS[name]
    for f in FLAGS: g[f] = DEFAULTS[f] if on is None else (DEFAULTS[f] or f in on) if name in STACK else (f in on)
    g["KO_LINE_MODE"] = next((x.split("=")[1] for x in (on or []) if x.startswith("KO_LINE_MODE=")), MODE0)
def one(img):
    t = time.time(); c1, seen = pass1(img); c2 = pass2(img, c1) if c1 else []
    if g["KO_LINE"]: c2 = g["keyword_line_reread"](img, c2, seen)
    if g.get("RULE_REREAD"): c2 = g["broken_line_reread"](img, c2, seen)
    select_date(c2); return time.time() - t
if os.environ.get("TC_INTERLEAVE") == "1":   # 사진마다 모든 구성을 번갈아 잰다 (시작 구성도 돌림). 중간에 끼는 다른 부하가 한 구성에만 몰리지 않는다 (9/28)
    names = list(SETS); acc = {n: [] for n in names}
    one(imgs[0])                                   # 첫 호출의 준비 비용은 버린다
    for k, img in enumerate(imgs):
        for name in names[k % len(names):] + names[:k % len(names)]:
            apply(name); acc[name].append(one(img))
        if k % 10 == 9: print(f"{k + 1}/{N}", flush=True)
    for name in names:
        s = pd.Series(acc[name]); res[name] = s
        print(f"{name:5s}: 장당 평균 {s.mean():.2f}s  p90 {s.quantile(.9):.2f}s  최대 {s.max():.1f}s  ({N}장 {s.sum():.0f}s)", flush=True)
else:
    for name in SETS:
        apply(name); secs = [one(img) for img in imgs]
        s = pd.Series(secs); res[name] = s
        print(f"{name:5s}: 장당 평균 {s.mean():.2f}s  p90 {s.quantile(.9):.2f}s  최대 {s.max():.1f}s  ({N}장 {s.sum():.0f}s)", flush=True)
base = res.get("off") if "off" in res else res.get("cur")
for name, s in res.items():
    if base is not None and name not in ("off", "cur"):
        d = s.mean() - base.mean(); print(f"{name} − off: 장당 {d:+.3f}s → 500장 환산 {d*500:+.0f}s")
