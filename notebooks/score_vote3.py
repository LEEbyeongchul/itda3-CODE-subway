# -*- coding: utf-8 -*-
"""(u) 인식기 셋 다수결 채점 — exp_vote3.py 결과의 v3(미리 정한 규칙)를 fin(통합본 기본값)과 비교. 라벨은 9/27 수정 후(labels/labels_block*.csv).
    .venv/Scripts/python notebooks/score_vote3.py [EXP_TAG]"""
import csv, glob, sys
TAG = sys.argv[1] if len(sys.argv) > 1 else "2026-09-28"
cur = {}
for f in glob.glob("labels/labels_block*.csv"):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        cur[r["image_id"]] = r
R = []
for f in sorted(glob.glob(f"results/exp_vote3_{TAG}_[0-9].csv")):
    R += list(csv.DictReader(open(f, encoding="utf-8-sig")))
lab = lambda r: cur[r["image_id"]]["final_date"] if r["image_id"] in cur else r["label"]
tg = lambda r: (cur[r["image_id"]]["tags"] if r["image_id"] in cur else r["tags"]) or ""
n = len(R)
print(f"측정 {n}/2852장 · 통합본 fin 정답 {sum(r['fin'] == lab(r) for r in R)} ({sum(r['fin'] == lab(r) for r in R) / n:.1%}) → v3 정답 {sum(r['v3'] == lab(r) for r in R)} ({sum(r['v3'] == lab(r) for r in R) / n:.1%})")
ch = [r for r in R if r["v3"] != r["fin"]]
for grp, isd in (("병기", True), ("비병기", False)):
    S = [r for r in ch if ("2" in tg(r)) == isd]
    rec = [r for r in S if r["v3"] == lab(r)]; reg = [r for r in S if r["fin"] == lab(r)]; oth = [r for r in S if r["v3"] != lab(r) and r["fin"] != lab(r)]
    print(f"{grp}: 회복 {len(rec)} / 퇴보 {len(reg)} / 오답→다른 오답 {len(oth)}")
    for tag, L in (("+", rec), ("-", reg), ("~", oth)):
        for r in L:
            print(f"   {tag} {r['image_id']} 정답 {lab(r)} 지금 {r['fin']} → {r['v3']} | 파인튜닝 '{r['ft_full'][:24]}' / '{r['ft_mid'][:24]}' · 한국어 '{r['ko_full'][:24]}' / '{r['ko_mid'][:24]}'")
sv = [float(r["sec_vote"]) for r in R if r.get("sec_vote")]; s = [float(r["sec"]) for r in R if r.get("sec")]
print(f"추가 읽기 시간 장당 평균 {sum(sv) / len(sv):.3f}s (본 처리 {sum(s) / len(s):.2f}s, 다른 프로세스가 같이 돌면 부풀어 있음)")
