# -*- coding: utf-8 -*-
"""층화 샘플링: images/ 에서 라벨링 대상을 뽑아 labels/sample.csv 로 저장한다.

    python notebooks/make_sample.py                    # 기본: small 100 / large 100 / mid 50, 5블록
    python notebooks/make_sample.py --n small:60,large:60,mid:30 --blocks 3

층(stratum)은 EXIF 보정 후 긴 변 기준:
    small  ≤ 700px   (640x640 저화질 군집, 전체의 33%)
    large  ≥ 2000px  (스마트폰 원본)
    mid    그 사이
두 군집은 성격이 완전히 달라 섞어서 뽑으면 평균이 아무것도 말해주지 않는다.
블록은 층을 섞어 라운드로빈으로 배정한다 (사람마다 쉬운 것/어려운 것이 고르게).
"""
import os, csv, random, argparse
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--images", default="images")
ap.add_argument("--out", default="labels/sample.csv")
ap.add_argument("--n", default="small:100,large:100,mid:50")
ap.add_argument("--blocks", type=int, default=5)
ap.add_argument("--seed", type=int, default=42)
args = ap.parse_args()
random.seed(args.seed)

quota = {k: int(v) for k, v in (x.split(":") for x in args.n.split(","))}


def stratum(long_side):
    if long_side <= 700:
        return "small"
    if long_side >= 2000:
        return "large"
    return "mid"


rows = []
for fn in sorted(os.listdir(args.images)):
    p = os.path.join(args.images, fn)
    try:
        with Image.open(p) as im:           # 크기만 읽으므로 디코딩 없이 빠르다
            w, h = im.size
            if (im.getexif() or {}).get(274, 1) in (5, 6, 7, 8):
                w, h = h, w
    except Exception:
        continue
    rows.append({"image_id": os.path.splitext(fn)[0], "file": fn, "stratum": stratum(max(w, h)), "w": w, "h": h})

picked = []
for s, n in quota.items():
    pool = [r for r in rows if r["stratum"] == s]
    random.shuffle(pool)
    picked += pool[:n]
    print(f"{s:6s}: 모집단 {len(pool):5d} → 표본 {min(n, len(pool))}")

random.shuffle(picked)
for i, r in enumerate(picked):
    r["block"] = i % args.blocks + 1
picked.sort(key=lambda r: (r["block"], r["file"]))

os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, "w", newline="", encoding="utf-8") as f:
    wr = csv.DictWriter(f, fieldnames=["block", "image_id", "file", "stratum", "w", "h"])
    wr.writeheader()
    wr.writerows(picked)
print(f"총 {len(picked)}장 → {args.out}  (블록 {args.blocks}개, 블록당 {len(picked) // args.blocks}장 내외)")
