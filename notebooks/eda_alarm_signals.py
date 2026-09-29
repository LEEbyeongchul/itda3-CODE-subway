# -*- coding: utf-8 -*-
"""경고 신호 EDA — 답을 바꾸지 않고 "이 답은 사람이 확인하세요" 라고 표시할 신호가 오답을 얼마나 잡는지 본다.

    python notebooks/eda_alarm_signals.py

OCR 을 새로 돌리지 않는다. 이미 있는 파일만 읽는다 (1스레드, 1분 안쪽).
  예측   results/exp_rules4_2026-09-26_kolp1det_merged.csv 의 kol 열 (현 기본값 p1det, 판정용 2,852장)
  라벨   labels/labels_block*.csv (9/27 재라벨 점검 반영)
  키워드 labels/keyword_scan.csv (한국어 인식기 전수 스캔, 9/12)
  반사   results/eda_imgq_2026-09-26.csv 의 clip_hi (250 이상 픽셀 비율, 사진 전체)
  촬영일 images/ 의 EXIF DateTimeOriginal

신호
  (1) 제조 키워드만 보임  제조·포장 키워드는 읽혔는데 소비·유통 키워드는 안 읽힌 사진
  (2) 촬영일보다 이른 날짜  읽은 날짜가 사진 찍은 날보다 앞 (운영에서는 '오늘'을 아니까 모든 사진에 적용 가능)
  (3) 반사  clip_hi 가 큰 사진
각 신호에 대해: 해당 장수, 그 안의 오답률(전체 오답률과 비교), 답을 NONE 으로 바꿨을 때의 회복/퇴보.
"""
import re, csv, glob, datetime as dt
from PIL import Image

PRED, COL = "results/exp_rules4_2026-09-26_kolp1det_merged.csv", "kol"
lab = {r["image_id"].zfill(6): r for p in glob.glob("labels/labels_block*.csv") for r in csv.DictReader(open(p, encoding="utf-8"))}
ks = {r["image_id"].zfill(6): r for r in csv.DictReader(open("labels/keyword_scan.csv", encoding="utf-8"))}
iq = {r["image_id"].zfill(6): r for r in csv.DictReader(open("results/eda_imgq_2026-09-26.csv", encoding="utf-8-sig"))}
rows = []
for r in csv.DictReader(open(PRED, encoding="utf-8-sig")):
    i = r["image_id"].zfill(6)
    rows.append({"id": i, "pred": r[COL], "label": lab[i]["final_date"], "tags": lab[i]["tags"], "file": lab[i]["file"]})


def as_date(s):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return None
    try:
        return dt.date(*map(int, s.split("-")))
    except ValueError:
        return None


def capture_date(file):
    try:
        with Image.open("images/" + file) as im:
            e = im.getexif()
            d = e.get_ifd(0x8769).get(36867) or e.get(306)
        return dt.date(int(d[:4]), int(d[5:7]), int(d[8:10])) if d else None
    except Exception:
        return None


def report(name, hit, pool):
    """hit: 신호가 켜진 행, pool: 신호를 계산할 수 있었던 행."""
    wrong = [r for r in hit if r["pred"] != r["label"]]
    pool_wrong = [r for r in pool if r["pred"] != r["label"]]
    rec = sum(r["label"] == "NONE" for r in wrong)            # NONE 으로 바꾸면 맞게 되는 것
    print(f"\n[{name}]  대상 {len(pool)}장 (오답 {len(pool_wrong)}, {len(pool_wrong) / len(pool):.1%})")
    print(f"  신호 켜짐 {len(hit)}장 · 그중 오답 {len(wrong)}장 ({len(wrong) / max(len(hit), 1):.0%}) · 대상 오답의 {len(wrong) / max(len(pool_wrong), 1):.0%} 를 잡음")
    print(f"  답을 NONE 으로 바꾸면: 회복 {rec} / 퇴보 {len(hit) - len(wrong)}")


print(f"판정용 {len(rows)}장, 오답 {sum(r['pred'] != r['label'] for r in rows)}장")
m = [r for r in rows if "m" in r["tags"]]
print(f"제조·포장일자만 있는 사진(태그 m) {len(m)}장 중 NONE 으로 답한 것 {sum(r['pred'] == 'NONE' for r in m)}장")

kw = [r for r in rows if r["id"] in ks]
report("(1) 제조 키워드만 보임", [r for r in kw if ks[r["id"]]["제조키워드"] != "0" and ks[r["id"]]["소비키워드"] == "0"], kw)

for r in rows:
    r["cap"] = capture_date(r["file"])
ex = [r for r in rows if r["cap"]]
report("(2) 읽은 날짜가 촬영일보다 이름", [r for r in ex if as_date(r["pred"]) and as_date(r["pred"]) <= r["cap"]], ex)

gl = [r for r in rows if r["id"] in iq]
for th in (0.01, 0.05, 0.10):
    report(f"(3) 반사 clip_hi ≥ {th:.0%} (사진 전체)", [r for r in gl if float(iq[r["id"]]["clip_hi"]) >= th], gl)
