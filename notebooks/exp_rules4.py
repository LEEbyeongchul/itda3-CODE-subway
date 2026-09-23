# 본선 규칙 4개 동시 측정 — 판정용 2,852장(블록 1~5 봉인 제외). base(전부 꺼짐) / keep(유지만) / all4(유지+범위가림+콜론+한자리확장).
#   .venv/Scripts/python notebooks/exp_rules4.py <K> <N>   → results/exp_rules4_2026-09-22_<K>.csv  (K번째/N분할, 병렬 실행용)
import json, os, sys, time, pandas as pd
os.environ.setdefault("ITDA_THREADS", "4")
K, N = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__exp__", "os": os}
for i in (1, 2, 3, 4, 5): exec(cells[i], g)
load_image, pass1, pass2, select_date = g["load_image"], g["pass1"], g["pass2"], g["select_date"]
FLAGS = ["P2_KEEP", "RULE_SPAN", "RULE_COLON", "RULE_TRUNC", "P2_VOTE640", "KO_KEYWORD"]
DEFAULTS = {f: g.get(f, False) for f in FLAGS}   # 노트북 기본값 (env 반영). 콤보에 없는 플래그는 기본값 유지
COMBOS = {"base": [], "keep": ["P2_KEEP"], "all4": FLAGS[:4], "cur": None, "v640": ["P2_VOTE640"], "ko": ["KO_KEYWORD"]}   # cur = 기본값 그대로, v640 = 기본값 + 640 표
if os.environ.get("EXP_COMBOS"):   # 예: EXP_COMBOS=all4 → 그 구성만 (base 는 results/join 의 old 예측으로 대신)
    COMBOS = {k: v for k, v in COMBOS.items() if k in os.environ["EXP_COMBOS"].split(",")}
def setf(on):
    for f in FLAGS: g[f] = DEFAULTS[f] if on is None else (f in on)
    if on is not None and on and on[0] in ("P2_VOTE640", "KO_KEYWORD"):   # v640·ko 는 기본값 위에 얹는다
        for f in FLAGS: g[f] = DEFAULTS[f] or f in on
def key(b):
    if not b: return "NONE"
    y = b["y"] if b["y"] is not None else "NONE"; d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"
J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
T = J[~J.block.isin(["1", "2", "3", "4", "5"])].iloc[K::N]
out = f"results/exp_rules4_{os.environ.get('EXP_TAG', '2026-09-22')}_{K}.csv"
rows = []
for n, (_, r) in enumerate(T.iterrows()):
    t = time.time(); img = load_image(f"images/{r.file}"); rec = dict(image_id=r.image_id, label=r.final_date, old=r.pred, tags=r.tags)
    for name, on in COMBOS.items():
        setf(on); c1, _ = pass1(img)
        c2 = pass2(img, list(c1)) if c1 else []
        if g["KO_KEYWORD"] and c2: c2 = g["keyword_filter"](img, c2)
        rec[name] = key(select_date(c2)) if c2 else "NONE"
    rec["sec"] = round(time.time() - t, 1); rows.append(rec)
    if n % 25 == 0:
        print(n, len(T), flush=True); pd.DataFrame(rows).to_csv(out, index=False)
D = pd.DataFrame(rows); D.to_csv(out, index=False)
if "base" not in D: D["base"] = D["old"]
for name in COMBOS:
    rec_ = ((D[name] == D.label) & (D.base != D.label)).sum(); reg = ((D[name] != D.label) & (D.base == D.label)).sum()
    print(f"{name}: 정답 {(D[name] == D.label).sum()}/{len(D)}  base 대비 회복 {rec_} / 퇴보 {reg}")
print("done")
