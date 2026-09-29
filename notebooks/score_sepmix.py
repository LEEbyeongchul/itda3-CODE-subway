"""(q) SEPMIX 중간·최종 채점. 기준선 = 현재 기본값(p1det, kolp1det_merged 의 kol 열). 병기·비병기 따로."""
import csv, glob, sys
base = {r["image_id"]: r for r in csv.DictReader(open("results/exp_rules4_2026-09-26_kolp1det_merged.csv", encoding="utf-8-sig"))}
rows = []
for f in sorted(glob.glob("results/exp_rules4_2026-09-27_sepmix_[0-9].csv")):
    rows += list(csv.DictReader(open(f, encoding="utf-8-sig")))
print(f"측정 {len(rows)}/2852장")
rec = {"병기": [], "비병기": []}; reg = {"병기": [], "비병기": []}; other = []
for r in rows:
    b = base[r["image_id"]]; grp = "병기" if "2" in (b["tags"] or "") else "비병기"
    if r["sep"] == b["kol"]:
        continue
    item = (r["image_id"], "정답 " + b["label"], "기준 " + b["kol"], "→ " + r["sep"])
    if r["sep"] == b["label"]:
        rec[grp].append(item)
    elif b["kol"] == b["label"]:
        reg[grp].append(item)
    else:
        other.append(item)
for grp in ("병기", "비병기"):
    print(f"{grp}: 회복 {len(rec[grp])} / 퇴보 {len(reg[grp])}")
    for it in rec[grp]: print("   +", *it)
    for it in reg[grp]: print("   -", *it)
print(f"합계: +{sum(map(len, rec.values()))} / −{sum(map(len, reg.values()))}, 오답→다른 오답 {len(other)}")
for it in other: print("   ~", *it)
n = len(rows); ok_b = sum(base[r["image_id"]]["kol"] == base[r["image_id"]]["label"] for r in rows); ok_s = sum(r["sep"] == base[r["image_id"]]["label"] for r in rows)
print(f"측정분 정답: 기준 {ok_b} → sep {ok_s} (/{n})")
