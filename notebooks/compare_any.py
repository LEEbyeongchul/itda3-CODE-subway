# -*- coding: utf-8 -*-
"""두 예측 CSV 를 라벨 전체(labels_block*.csv)와 대조해 회복/퇴보를 센다. 어떤 이미지 부분집합이든 됨 (병기 349장, 2,852장 등).

    python notebooks/compare_any.py "기준=base_sub.csv|base_dbg.csv" "실험=exp_sub.csv|exp_dbg.csv" [--show 8]

디버그 CSV 는 선택 (있으면 퇴보 예시에 후보를 같이 보여줌). 공통 image_id 만 평가."""
import csv, glob, sys, argparse

ap = argparse.ArgumentParser()
ap.add_argument("runs", nargs=2, help='이름=예측csv[|디버그csv]')
ap.add_argument("--show", type=int, default=8)
ap.add_argument("--labels", default="labels/labels_block*.csv")
a = ap.parse_args()

gold, tags, blk = {}, {}, {}
for f in glob.glob(a.labels):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        gold[r["image_id"]] = r["final_date"]; tags[r["image_id"]] = r["tags"]; blk[r["image_id"]] = int(r["block"])

def load(spec):
    name, paths = spec.split("=", 1); p = paths.split("|")
    pred = {r["image_id"]: r["final_date"] for r in csv.DictReader(open(p[0], encoding="utf-8-sig"))}
    dbg = {r["image_id"]: r for r in csv.DictReader(open(p[1], encoding="utf-8-sig"))} if len(p) > 1 else {}
    return name, pred, dbg

(n1, p1, d1), (n2, p2, d2) = load(a.runs[0]), load(a.runs[1])
ids = sorted(set(p1) & set(p2) & set(gold))
def fields(p, g):
    ps, gs = p.split("-"), g.split("-")
    return sum(x == y for x, y in zip(ps, gs)) / 3 if len(ps) == 3 and len(gs) == 3 else float(p == g)
def stats(p):
    ok = sum(p[i] == gold[i] for i in ids); fa = sum(fields(p[i], gold[i]) for i in ids)
    none = sum(p[i] == "NONE" and gold[i] != "NONE" for i in ids); ans = [i for i in ids if p[i] != "NONE"]
    prec = sum(p[i] == gold[i] for i in ans) / max(1, len(ans))
    return ok, fa, none, prec
s1, s2 = stats(p1), stats(p2)
print(f"공통 {len(ids)}장 (측정용 블록 1~5: {sum(blk[i] <= 5 for i in ids)}, 병기 태그: {sum('2' in tags[i] for i in ids)})")
print(f"| 지표 | {n1} | {n2} |\n| --- | --- | --- |")
print(f"| 완전일치 | {s1[0]} ({100*s1[0]/len(ids):.1f}%) | {s2[0]} ({100*s2[0]/len(ids):.1f}%) |")
print(f"| 필드평균 | {100*s1[1]/len(ids):.1f}% | {100*s2[1]/len(ids):.1f}% |")
print(f"| 미인식(정답 있는데 NONE) | {s1[2]} | {s2[2]} |")
print(f"| 답한 것의 정밀도 | {100*s1[3]:.1f}% | {100*s2[3]:.1f}% |")
for name, d in ((n1, d1), (n2, d2)):
    if d:
        secs = [float(d[i]["sec"]) for i in ids if i in d and d[i].get("sec")]
        if secs: print(f"| 장당 시간 {name} | 평균 {sum(secs)/len(secs):.2f}s |")
rec = [i for i in ids if p1[i] != gold[i] and p2[i] == gold[i]]
reg = [i for i in ids if p1[i] == gold[i] and p2[i] != gold[i]]
print(f"\n{n1} → {n2}: 새로 맞춘 {len(rec)}장, 새로 틀린 {len(reg)}장")
for title, lst in (("새로 맞춘", rec), ("새로 틀린", reg)):
    print(f"\n{title} 예시:")
    for i in lst[:a.show]:
        extra = f"  src={d2[i]['src']} cands={d2[i]['cands'][:90]}" if i in d2 else ""
        print(f"  {i} b{blk[i]} 정답 {gold[i]}  {n1}={p1[i]}  {n2}={p2[i]}{extra}")
