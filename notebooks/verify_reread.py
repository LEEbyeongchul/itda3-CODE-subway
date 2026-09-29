# -*- coding: utf-8 -*-
"""(s)(t) 검증 — 전체 측정에서 답이 바뀐 장과 (t) 가 발동한 장을 같은 프로세스에서 다시 돌리고, 안 바뀐 장 표본도 재현되는지 본다.

    .venv/Scripts/python notebooks/verify_reread.py <EXP_TAG> <출력 CSV> [표본 수=40]

열: cur(끔) · rvote((s) 둘 이상 일치) · ymsep((t)) · tv((t) + (s) 둘 이상 일치, 채택 후보 조합) · t_log((t) 가 고쳐 쓴 글)
전체 측정의 both 열은 (t) + (s) '하나라도' 조합이라 채택 후보 조합과 다르다. tv 는 여기서만 잰다.
"""
import csv, os, random, runpy, sys

TAG, OUT = sys.argv[1], sys.argv[2]
NS = int(sys.argv[3]) if len(sys.argv) > 3 else 40
full = list(csv.DictReader(open(f"results/exp_rules4_{TAG}_0.csv", encoding="utf-8-sig")))
changed = [r for r in full if r["t_fired"] == "1" or any(r[c] != r["cur"] for c in ("reread", "rvote", "ymsep", "both"))]
rest = [r for r in full if r not in changed]
sample = random.Random(0).sample(rest, min(NS, len(rest)))
print(f"바뀌었거나 (t) 발동 {len(changed)}장 + 안 바뀐 표본 {len(sample)}장", flush=True)

sys.argv = ["exp_reread.py", "0", "1"]
E = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exp_reread.py"), run_name="__lib__")
g, T, pipeline, reread, key, select_date = E["g"], E["T_RULE"], E["pipeline"], E["reread"], E["key"], E["select_date"]
J = {r["image_id"]: r for r in csv.DictReader(open("results/join_all3352_v6.csv", encoding="utf-8-sig"))}
sel = lambda cs: key(select_date(cs)) if cs else "NONE"
rows = []
for n, r in enumerate(changed + sample):
    img = E["load_image"]("images/" + J[r["image_id"]]["file"])
    T.update(on=False, fired=False, log=[])
    c2, seen = pipeline(img)
    v = reread(img, c2, seen)[1]
    T.update(on=True, fired=False, log=[])
    ct, seen_t = pipeline(img)
    vt = reread(img, ct, seen_t)[1]
    log = " ## ".join(f"'{a.strip()[:60]}' → '{b.strip()[:60]}'" for a, b in dict.fromkeys(T["log"]))
    T.update(on=False)
    rows.append(dict(image_id=r["image_id"], group="바뀜" if n < len(changed) else "표본", label=r["label"],
                     cur=sel(c2), rvote=sel(c2 + v), ymsep=sel(ct), tv=sel(ct + vt),
                     full_cur=r["cur"], full_rvote=r["rvote"], full_ymsep=r["ymsep"], t_log=log[:500]))
    if n % 10 == 0:
        print(n, flush=True)
        with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for grp in ("바뀜", "표본"):
    sub = [r for r in rows if r["group"] == grp]
    print(grp, len(sub), "| 재현: cur", sum(r["cur"] == r["full_cur"] for r in sub), "rvote", sum(r["rvote"] == r["full_rvote"] for r in sub), "ymsep", sum(r["ymsep"] == r["full_ymsep"] for r in sub))
print("done")
