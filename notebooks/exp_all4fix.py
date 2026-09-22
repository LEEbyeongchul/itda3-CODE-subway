# 규칙 4개(유지+범위가림[왼쪽우선 수정]+콜론+한자리확장[0? 제거]) 동시 켠 all4 만 2,852장 재측정. base=v6(old), keep 은 exp_p2keep 결과와 비교.
import json, os, sys, time, pandas as pd
os.environ.setdefault("ITDA_THREADS", "4")
K, N = int(sys.argv[1]), int(sys.argv[2])
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__exp__", "os": os}
for i in (1, 2, 3, 4, 5): exec(cells[i], g)
for f in ["P2_KEEP", "RULE_SPAN", "RULE_COLON", "RULE_TRUNC"]: g[f] = True
load_image, pass1, pass2, select_date = g["load_image"], g["pass1"], g["pass2"], g["select_date"]
def key(b):
    if not b: return "NONE"
    y = b["y"] if b["y"] is not None else "NONE"; d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"
J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
T = J[~J.block.isin(["1", "2", "3", "4", "5"])].iloc[K::N]
out = f"results/exp_all4fix2_2026-09-23_{K}.csv"
rows = []
for n, (_, r) in enumerate(T.iterrows()):
    t = time.time(); img = load_image(f"images/{r.file}")
    c1, _ = pass1(img); a4 = key(select_date(pass2(img, list(c1)))) if c1 else "NONE"
    rows.append(dict(image_id=r.image_id, label=r.final_date, base=r.pred, tags=r.tags, all4=a4, sec=round(time.time() - t, 1)))
    if n % 25 == 0:
        print(n, len(T), flush=True); pd.DataFrame(rows).to_csv(out, index=False)
D = pd.DataFrame(rows); D.to_csv(out, index=False)
rec_ = ((D.all4 == D.label) & (D.base != D.label)).sum(); reg = ((D.all4 != D.label) & (D.base == D.label)).sum()
print(f"all4: 정답 {(D.all4 == D.label).sum()}/{len(D)}  base 대비 회복 {rec_} / 퇴보 {reg}  장당 {D.sec.mean():.1f}s")
print("done")
