# -*- coding: utf-8 -*-
"""라벨 vs 예측 정확도 분석.

    python notebooks/eval.py --pred submission.csv [--debug debug.csv] [--labels "labels/labels_block*.csv"] [--out report.md]

출력: 완전일치 / 필드별 정확도 / 층·형식·태그·라벨러별 교차표 / NONE 혼동 / 정밀도-커버리지(신뢰도) / 오답 목록
"""
import csv, glob, argparse, collections, io, os

ap = argparse.ArgumentParser()
ap.add_argument("--pred", required=True)
ap.add_argument("--debug", default="")
ap.add_argument("--labels", default="labels/labels_block*.csv")
ap.add_argument("--sample", default="labels/sample.csv")
ap.add_argument("--out", default="")
ap.add_argument("--title", default="기준선")
args = ap.parse_args()

labels = {}
for f in sorted(glob.glob(args.labels)):
    for r in csv.DictReader(open(f, encoding="utf-8")):
        labels[r["image_id"]] = r
preds = {r["image_id"]: r for r in csv.DictReader(open(args.pred, encoding="utf-8"))}
sample = {r["image_id"]: r for r in csv.DictReader(open(args.sample, encoding="utf-8"))} if os.path.exists(args.sample) else {}
debug = {r["image_id"]: r for r in csv.DictReader(open(args.debug, encoding="utf-8"))} if args.debug and os.path.exists(args.debug) else {}

ids = [i for i in labels if i in preds]
missing = [i for i in labels if i not in preds]
out = io.StringIO()
P = lambda *a: print(*a, file=out)

P(f"# 정확도 분석 — {args.title}\n")
P(f"라벨 {len(labels)}장 중 예측 있는 {len(ids)}장 평가" + (f" (예측 없음 {len(missing)}장)" if missing else ""))
P()

def score(i):
    L, R = labels[i], preds[i]
    f = {k: (L[k] == R[k]) for k in ("year", "month", "day")}
    return f, (L["final_date"] == R["final_date"])

def summarize(subset, label=""):
    n = len(subset)
    if n == 0:
        return None
    ex = sum(score(i)[1] for i in subset)
    fy = sum(score(i)[0]["year"] for i in subset)
    fm = sum(score(i)[0]["month"] for i in subset)
    fd = sum(score(i)[0]["day"] for i in subset)
    part = (fy + fm + fd) / (3 * n)
    return n, ex / n, fy / n, fm / n, fd / n, part

def table(groups, title):
    P(f"## {title}\n")
    P("| 구분 | 장수 | 완전일치 | 연도 | 월 | 일 | 필드평균 |")
    P("| --- | --- | --- | --- | --- | --- | --- |")
    for g, subset in groups:
        s = summarize(subset)
        if s:
            n, ex, fy, fm, fd, part = s
            P(f"| {g} | {n} | {ex*100:.1f}% | {fy*100:.1f}% | {fm*100:.1f}% | {fd*100:.1f}% | {part*100:.1f}% |")
    P()

table([("전체", ids)], "전체")

# 층별
if sample:
    strata = collections.defaultdict(list)
    for i in ids:
        strata[sample.get(i, {}).get("stratum", "?")].append(i)
    table(sorted(strata.items(), key=lambda kv: {"small": 0, "mid": 1, "large": 2}.get(kv[0], 9)), "해상도 층별 (small ≤700px · mid · large ≥2000px)")

# 형식별
fmts = collections.defaultdict(list)
for i in ids:
    fmts[labels[i]["format"]].append(i)
table(sorted(fmts.items(), key=lambda kv: -len(kv[1])), "포장 표기 형식별 (라벨 format)")

# 태그별
names = {"2": "2 병기", "d": "d 일먼저", "r": "r 회전", "t": "t 작음", "b": "b 흐림", "e": "e 각인", "n": "n 키워드없음", "s": "s 판독불가", "?": "? 애매"}
tags = collections.defaultdict(list)
for i in ids:
    if labels[i]["tags"]:
        for t in labels[i]["tags"]:
            tags[t].append(i)
    else:
        tags["(태그 없음)"].append(i)
table([(names.get(k, k), v) for k, v in sorted(tags.items(), key=lambda kv: -len(kv[1]))], "태그별")

# 라벨러별 (라벨 품질 편차 확인)
labs = collections.defaultdict(list)
for i in ids:
    labs[labels[i]["labeler"]].append(i)
table(sorted(labs.items()), "라벨러별 (블록 난이도·라벨 편차 확인용)")

# 정답 유형별
def ltype(fd):
    if fd == "NONE":
        return "전부 NONE"
    y, m, d = fd.split("-")
    return "연도 NONE" if y == "NONE" else ("일 NONE" if d == "NONE" else "완전 날짜")
lt = collections.defaultdict(list)
for i in ids:
    lt[ltype(labels[i]["final_date"])].append(i)
table(sorted(lt.items(), key=lambda kv: -len(kv[1])), "정답 유형별")

# NONE 혼동
P("## NONE 혼동 (연도 기준)\n")
c = collections.Counter()
for i in ids:
    L, R = labels[i]["year"] == "NONE", preds[i]["year"] == "NONE"
    c[("정답 NONE" if L else "정답 있음", "예측 NONE" if R else "예측 있음")] += 1
P("| | 예측 NONE | 예측 있음 |")
P("| --- | --- | --- |")
for l in ("정답 NONE", "정답 있음"):
    P(f"| {l} | {c[(l, '예측 NONE')]} | {c[(l, '예측 있음')]} |")
P()
answered = [i for i in ids if preds[i]["final_date"] != "NONE"]
if answered:
    s = summarize(answered)
    P(f"답을 낸 {len(answered)}장의 완전일치(정밀도): **{s[1]*100:.1f}%**, 커버리지: **{len(answered)/len(ids)*100:.1f}%**\n")

# 정밀도-커버리지 (신뢰도)
if debug:
    P("## 신뢰도 임계값별 정밀도–커버리지\n")
    P("| 임계값 | 답한 장수 | 커버리지 | 완전일치(정밀도) | 필드평균 |")
    P("| --- | --- | --- | --- | --- |")
    for th in [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        sub = [i for i in ids if i in debug and debug[i]["conf"] not in ("", None) and float(debug[i]["conf"]) >= th]
        s = summarize(sub)
        if s:
            P(f"| ≥{th:.1f} | {s[0]} | {s[0]/len(ids)*100:.1f}% | {s[1]*100:.1f}% | {s[5]*100:.1f}% |")
    P()
    secs = [float(debug[i]["sec"]) for i in ids if i in debug and debug[i]["sec"]]
    if secs:
        secs.sort()
        P(f"소요 시간: 평균 {sum(secs)/len(secs):.2f}s · 중앙값 {secs[len(secs)//2]:.2f}s · p90 {secs[int(len(secs)*.9)]:.2f}s · 최대 {secs[-1]:.2f}s · 500장 환산 {sum(secs)/len(secs)*500:.0f}s\n")
    esc = sum(1 for i in ids if i in debug and "1024" in debug[i]["src"])
    P(f"1024px 사다리로 올라간 장수: {esc} ({esc/len(ids)*100:.1f}%)\n")

# 오답 목록
P("## 오답 목록 (완전일치 실패)\n")
P("| image_id | 층 | 정답 | 예측 | 형식 | 태그 | 원문 | 후보(y-m-d:패턴:출처:신뢰도) |")
P("| --- | --- | --- | --- | --- | --- | --- | --- |")
wrong = [i for i in ids if not score(i)[1]]
for i in wrong:
    L, R = labels[i], preds[i]
    cands = debug[i]["cands"][:80] if i in debug else ""
    P(f"| {i} | {sample.get(i, {}).get('stratum', '')} | {L['final_date']} | {R['final_date']} | {L['format']} | {L['tags']} | {L['raw']} | {cands} |")
P()

# 오답 유형 요약
P("## 오답 유형 요약\n")
et = collections.Counter()
for i in wrong:
    L, R = labels[i], preds[i]
    if R["final_date"] == "NONE" and L["final_date"] != "NONE":
        et["미인식 (정답 있는데 NONE)"] += 1
    elif L["final_date"] == "NONE":
        et["오탐 (정답 NONE 인데 답함)"] += 1
    elif L["year"] != R["year"] and L["month"] == R["month"] and L["day"] == R["day"]:
        et["연도만 틀림"] += 1
    elif L["year"] == R["year"] and (L["month"] != R["month"] or L["day"] != R["day"]):
        et["월/일 틀림 (연도 맞음)"] += 1
    elif L["month"] == R["day"] and L["day"] == R["month"]:
        et["월·일 뒤바뀜"] += 1
    else:
        et["전혀 다른 날짜"] += 1
for k, v in et.most_common():
    P(f"- {k}: {v}")
P()

text = out.getvalue()
print(text)
if args.out:
    open(args.out, "w", encoding="utf-8").write(text)
    print("→", args.out)
