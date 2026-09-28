"""규칙 실험 중간·최종 채점 (exp_rules4.py 결과). 기준선 = 현재 기본값(p1det, kolp1det_merged 의 kol 열). 병기·비병기 따로.
  .venv/Scripts/python notebooks/score_rule.py <EXP_TAG> <구성 열>      예: score_rule.py 2026-09-27_tail tail"""
import csv, glob, sys
TAG, COL = sys.argv[1], sys.argv[2]
base = {r["image_id"]: r for r in csv.DictReader(open("results/exp_rules4_2026-09-26_kolp1det_merged.csv", encoding="utf-8-sig"))}
rows = []
for f in sorted(glob.glob(f"results/exp_rules4_{TAG}_[0-9].csv")):
    rows += list(csv.DictReader(open(f, encoding="utf-8-sig")))
nd = sum("2" in (base[r["image_id"]]["tags"] or "") for r in rows)
print(f"측정 {len(rows)}/2852장 (병기 {nd} · 비병기 {len(rows) - nd})")
rec = {"병기": [], "비병기": []}; reg = {"병기": [], "비병기": []}; other = []
for r in rows:
    b = base[r["image_id"]]; grp = "병기" if "2" in (b["tags"] or "") else "비병기"
    if r[COL] == b["kol"]:
        continue
    item = (grp, r["image_id"], "정답 " + b["label"], "기준 " + b["kol"], "→ " + r[COL])
    if r[COL] == b["label"]:
        rec[grp].append(item)
    elif b["kol"] == b["label"]:
        reg[grp].append(item)
    else:
        other.append(item)
for grp in ("병기", "비병기"):
    print(f"{grp}: 회복 {len(rec[grp])} / 퇴보 {len(reg[grp])}")
    for it in rec[grp]: print("   +", *it[1:])
    for it in reg[grp]: print("   -", *it[1:])
print(f"합계: +{sum(map(len, rec.values()))} / −{sum(map(len, reg.values()))}, 오답→다른 오답 {len(other)}")
for it in other: print("   ~", *it)
ok_b = sum(base[r["image_id"]]["kol"] == base[r["image_id"]]["label"] for r in rows); ok_s = sum(r[COL] == base[r["image_id"]]["label"] for r in rows)
print(f"측정분 정답: 기준 {ok_b} → {COL} {ok_s} (/{len(rows)})")

# 9/27 재라벨 점검 반영: 현재 labels/labels_block*.csv (수정 후 라벨·태그) 로 같은 비교를 한 번 더
cur = {}
for f in glob.glob("labels/labels_block*.csv"):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        cur[r["image_id"]] = r
for i, b in base.items():   # 블록 CSV 에 없는 장(003347 등)은 기준선의 라벨·태그를 그대로 쓴다
    cur.setdefault(i, {"final_date": b["label"], "tags": b["tags"]})
moved = [i for i, b in base.items() if cur[i]["final_date"] != b["label"]]
print(f"\n[수정 후 라벨 기준] 기준선과 라벨이 다른 장 {len(moved)} (전체 2,852장 중)")
for grp, isd in (("병기", True), ("비병기", False)):
    sel = [r for r in rows if ("2" in (cur[r["image_id"]]["tags"] or "")) == isd]
    a = sum(base[r["image_id"]]["kol"] == cur[r["image_id"]]["final_date"] for r in sel); b_ = sum(r[COL] == cur[r["image_id"]]["final_date"] for r in sel)
    rc = sum(r[COL] == cur[r["image_id"]]["final_date"] != base[r["image_id"]]["kol"] for r in sel)
    rg = sum(base[r["image_id"]]["kol"] == cur[r["image_id"]]["final_date"] != r[COL] for r in sel)
    print(f"{grp}: 측정 {len(sel)}장, 기준 {a} → {COL} {b_}, 회복 {rc} / 퇴보 {rg}")
