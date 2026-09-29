# 확인 측정: 채택 후보 조합 = 유지(P2_KEEP) + 콜론(COLON) + 한자리확장(TRUNC), SPAN 꺼짐. 판정용 2,852장.
#   kct      : 현재 노트북 유지 규칙 (2패스 출력에 같은 연·월이 있으면 1패스 후보를 안 살림)
#   kct_tier : 유지 규칙의 등급 인식 변형 — 1패스 후보와 등급이 같거나 더 높은 2패스 출력만 "같은 연·월을 다시 읽음"으로 인정
#              (MDY4 등급 2 가 같은 연·월을 차지해 등급 1 정답이 안 살아나는 001522·001818·002815 유형)
# pass1·pass2 는 한 번만 돌리고 유지 규칙만 두 가지로 적용한다 (P2_KEEP 은 노트북에서 끄고 여기서 재현).
import json, os, sys, time, pandas as pd
os.environ.setdefault("ITDA_THREADS", "4")
K, N = int(sys.argv[1]), int(sys.argv[2])
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__exp__", "os": os}
for i in (1, 2, 3, 4, 5): exec(cells[i], g)
g["P2_KEEP"] = False; g["RULE_SPAN"] = False; g["RULE_COLON"] = True; g["RULE_TRUNC"] = True
load_image, pass1, pass2, select_date, TIER = g["load_image"], g["pass1"], g["pass2"], g["select_date"], g["KIND_TIER"]
def tier(c): return TIER.get(c["kind"], 9)
def keep_plain(cands, out):
    have = {(o["y"], o["m"]) for o in out}; res = list(out)
    for c in cands:
        if (c["y"], c["m"]) not in have:
            res.append({**c, "src": "p1keep/" + c["src"]}); have.add((c["y"], c["m"]))
    return res
def keep_tier(cands, out):
    res = list(out); added = set()
    for c in cands:
        if any((o["y"], o["m"]) == (c["y"], c["m"]) and tier(o) <= tier(c) for o in out) or (c["y"], c["m"]) in added:
            continue
        res.append({**c, "src": "p1keep/" + c["src"]}); added.add((c["y"], c["m"]))
    return res
def key(b):
    if not b: return "NONE"
    y = b["y"] if b["y"] is not None else "NONE"; d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"
J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
T = J[~J.block.isin(["1", "2", "3", "4", "5"])].iloc[K::N]
out = f"results/exp_kct_2026-09-23_{K}.csv"
rows = []
for n, (_, r) in enumerate(T.iterrows()):
    t = time.time(); img = load_image(f"images/{r.file}")
    c1, _ = pass1(img)
    if c1:
        p2 = pass2(img, [dict(c) for c in c1])
        a, b = key(select_date(keep_plain(c1, p2))), key(select_date(keep_tier(c1, p2)))
    else:
        a = b = "NONE"
    rows.append(dict(image_id=r.image_id, label=r.final_date, old=r.pred, tags=r.tags, kct=a, kct_tier=b, sec=round(time.time() - t, 1)))
    if n % 25 == 0:
        print(n, len(T), flush=True); pd.DataFrame(rows).to_csv(out, index=False)
D = pd.DataFrame(rows); D.to_csv(out, index=False)
for col in ["kct", "kct_tier"]:
    rec_ = ((D[col] == D.label) & (D.old != D.label)).sum(); reg = ((D[col] != D.label) & (D.old == D.label)).sum()
    print(f"{col:9s}: 정답 {(D[col] == D.label).sum()}/{len(D)}  base 대비 회복 {rec_} / 퇴보 {reg}")
print("done")
