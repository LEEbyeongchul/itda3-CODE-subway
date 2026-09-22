# -*- coding: utf-8 -*-
"""직접 촬영한 사진을 라벨링 블록으로 등록한다 (본선 추가 수집 데이터).

    python notebooks/register_photos.py --name 승아 --src "C:/Users/me/Pictures/소비기한"   # 처음 한 번
    python notebooks/label.py --block 16 --name 승아 --images custom_photos                  # 그다음 라벨링

하는 일
  1) --src 폴더의 사진(jpg/jpeg/png/heic 제외)을 custom_photos/ 로 복사하면서 긴 변 2,000px 로 축소하고 EXIF 회전을 적용,
     파일명을 x<이름약자><번호>.jpg 로 통일 (예: xSA0001.jpg). 원본은 건드리지 않는다.
  2) labels/sample.csv 에 블록 번호와 함께 추가 (이미 등록된 파일은 건너뜀 → 여러 번 실행해도 됨).
블록 번호: 승아 16 · 서현 17 · 민섭 18 · 서영 19 · 병철 20 (그 외 이름은 --block 으로 지정)
custom_photos/ 는 git 에 안 올라간다 (용량). 사진은 드라이브 공유 폴더에도 같이 올린다. 라벨 CSV(labels/labels_block16.csv 등)만 git 에 올린다."""
import os, csv, glob, argparse, re
from PIL import Image, ImageOps

BLOCK = {"승아": 16, "서현": 17, "민섭": 18, "서영": 19, "병철": 20}
ABBR = {"승아": "SA", "서현": "SH", "민섭": "MS", "서영": "SY", "병철": "BC"}
LONG = 2000

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--src", required=True, help="촬영 원본 폴더")
ap.add_argument("--block", type=int, default=None)
ap.add_argument("--dst", default="custom_photos")
ap.add_argument("--sample", default="labels/sample.csv")
a = ap.parse_args()
block = a.block or BLOCK.get(a.name)
if block is None:
    raise SystemExit("--block 을 지정하세요 (승아 16 · 서현 17 · 민섭 18 · 서영 19 · 병철 20 외의 이름)")
abbr = ABBR.get(a.name, re.sub(r"[^A-Za-z]", "", a.name)[:2].upper() or "XX")
os.makedirs(a.dst, exist_ok=True)

rows = list(csv.DictReader(open(a.sample, encoding="utf-8-sig")))
known = {r["file"] for r in rows}
# 같은 사람의 기존 번호 다음부터
nums = [int(m.group(1)) for r in rows if (m := re.match(rf"x{abbr}(\d+)\.jpg$", r["file"]))]
n = max(nums, default=0)

src_files = sorted(f for f in glob.glob(os.path.join(a.src, "*")) if f.lower().endswith((".jpg", ".jpeg", ".png")))
if not src_files:
    raise SystemExit(f"{a.src} 에 jpg/png 가 없습니다 (HEIC 는 폰에서 '호환성 우선' 또는 jpg 변환 후)")
added = []
for f in src_files:
    n += 1
    out_name = f"x{abbr}{n:04d}.jpg"
    if out_name in known:
        continue
    with Image.open(f) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        s = LONG / max(w, h)
        if s < 1:
            im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
        im.save(os.path.join(a.dst, out_name), quality=92)
        W, H = im.size
    strat = "small" if max(W, H) <= 700 else ("large" if max(W, H) >= 2000 else "mid")
    added.append({"block": block, "image_id": out_name[:-4], "file": out_name, "stratum": strat, "w": W, "h": H})

if added:
    with open(a.sample, "a", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, fieldnames=["block", "image_id", "file", "stratum", "w", "h"])
        w.writerows(added)
print(f"{a.name}: {len(added)}장 등록 → 블록 {block}, {a.dst}/x{abbr}0001.jpg ~ (원본 {len(src_files)}장)")
print(f"다음: python notebooks/label.py --block {block} --name {a.name} --images {a.dst}")
