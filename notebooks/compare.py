# -*- coding: utf-8 -*-
"""여러 버전의 예측을 나란히 비교.  python notebooks/compare.py v3=v3_sub.csv|v3_debug.csv 새모델=new_sub.csv|new_debug.csv   (debug 는 ITDA_DEBUG_CSV 로 생성, 생략 가능)"""
import csv, glob, sys, collections, os

labels = {r["image_id"]: r for f in glob.glob("labels/labels_block*.csv") for r in csv.DictReader(open(f, encoding="utf-8"))}
sample = {r["image_id"]: r for r in csv.DictReader(open("labels/sample.csv", encoding="utf-8"))}
runs = []
for arg in sys.argv[1:]:
    name, paths = arg.split("=", 1)
    pred, *dbg = paths.split("|")
    P = {r["image_id"]: r for r in csv.DictReader(open(pred, encoding="utf-8"))}
    D = {r["image_id"]: r for r in csv.DictReader(open(dbg[0], encoding="utf-8"))} if dbg and os.path.exists(dbg[0]) else {}
    runs.append((name, P, D))
ids = sorted(set.intersection(*[set(P) for _, P, _ in runs]) & set(labels))
print(f"공통 평가 {len(ids)}장\n")

def stats(P, subset):
    n = len(subset)
    if not n: return None
    ex = sum(P[i]["final_date"] == labels[i]["final_date"] for i in subset) / n
    fa = sum(P[i][k] == labels[i][k] for i in subset for k in ("year", "month", "day")) / (3 * n)
    none_wrong = sum(P[i]["final_date"] == "NONE" and labels[i]["final_date"] != "NONE" for i in subset) / n
    ans = [i for i in subset if P[i]["final_date"] != "NONE"]
    prec = sum(P[i]["final_date"] == labels[i]["final_date"] for i in ans) / len(ans) if ans else 0
    return n, ex, fa, none_wrong, prec, len(ans) / n

def row(label, subset):
    cells = [f"{label}", f"{len(subset)}"]
    for name, P, _ in runs:
        s = stats(P, subset)
        cells.append(f"{s[1]*100:.1f} / {s[2]*100:.1f}" if s else "-")
    print("| " + " | ".join(cells) + " |")

hdr = ["구분", "장수"] + [f"{n} (완전일치 / 필드평균 %)" for n, _, _ in runs]
print("| " + " | ".join(hdr) + " |"); print("|" + " --- |" * len(hdr))
row("전체", ids)
for st in ("small", "mid", "large"):
    row(f"층 {st}", [i for i in ids if sample.get(i, {}).get("stratum") == st])
fm = collections.Counter(labels[i]["format"] for i in ids)
for f, n in fm.most_common(9):
    row(f"형식 {f}", [i for i in ids if labels[i]["format"] == f])
for t, nm in (("2", "태그 병기"), ("d", "태그 일먼저"), ("b", "태그 흐림")):
    row(nm, [i for i in ids if t in labels[i]["tags"]])
print()
print("| 지표 | " + " | ".join(n for n, _, _ in runs) + " |"); print("|" + " --- |" * (len(runs) + 1))
for label, idx in (("미인식률 (정답 있는데 NONE)", 3), ("답한 것의 정밀도", 4), ("커버리지", 5)):
    print(f"| {label} | " + " | ".join(f"{stats(P, ids)[idx]*100:.1f}%" for _, P, _ in runs) + " |")
for name, P, D in runs:
    if D:
        secs = sorted(float(D[i]["sec"]) for i in ids if i in D and D[i]["sec"])
        if secs: print(f"| 장당 시간 {name} | 평균 {sum(secs)/len(secs):.2f}s · p90 {secs[int(len(secs)*.9)]:.2f}s · 500장 {sum(secs)/len(secs)*500:.0f}s |")
print()
# 버전 간 전이: 맞음→틀림 / 틀림→맞음
if len(runs) >= 2:
    a, b = runs[0], runs[-1]
    ok = lambda P, i: P[i]["final_date"] == labels[i]["final_date"]
    gain = [i for i in ids if not ok(a[1], i) and ok(b[1], i)]; loss = [i for i in ids if ok(a[1], i) and not ok(b[1], i)]
    print(f"{a[0]} → {b[0]}: 새로 맞춘 {len(gain)}장, 새로 틀린 {len(loss)}장")
    print("새로 틀린 예시:")
    for i in loss[:12]:
        print(f"  {i} 정답 {labels[i]['final_date']}  {a[0]}={a[1][i]['final_date']}  {b[0]}={b[1][i]['final_date']}  raw={labels[i]['raw']!r}  {b[2].get(i, {}).get('cands', '')[:80]}")
