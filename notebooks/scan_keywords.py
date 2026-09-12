# -*- coding: utf-8 -*-
"""라벨된 사진에서 '제조/포장' vs '소비/유통' 키워드를 한글 인식기로 훑어, 제조·포장일자만 있는 사진(정답 NONE, 운영진 9/12 확정) 후보를 뽑는다.

    python notebooks/scan_keywords.py --out labels/keyword_scan.csv          # 라벨 전체
    python notebooks/scan_keywords.py --blocks 1,2,3,4,5 --out labels/keyword_scan_1-5.csv

출력 열: image_id, block, label, 소비키워드, 제조키워드, 후보(제조만 있고 라벨이 NONE 아님), 읽힌_텍스트
후보 = 사람이 사진을 다시 봐야 하는 목록. 자동으로 라벨을 바꾸지 않는다.
한글 인식기(korean_PP-OCRv5_mobile_rec)는 첫 실행 때 내려받는다 (검토용 도구라 제출 파이프라인과 무관)."""
import os, re, csv, glob, argparse, time
import numpy as np
from PIL import Image, ImageOps

ap = argparse.ArgumentParser()
ap.add_argument("--blocks", default="", help="비우면 labels_block*.csv 전부")
ap.add_argument("--images", default="images")
ap.add_argument("--out", default="labels/keyword_scan.csv")
ap.add_argument("--threads", type=int, default=4)
ap.add_argument("--long", type=int, default=960, help="탐지 해상도 (긴 변). 한글 잔글씨라 640 보다 크게")
args = ap.parse_args()

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
import torch  # noqa: F401  (Windows: paddle 보다 먼저)
from paddleocr import TextDetection, TextRecognition

det = TextDetection(model_name="PP-OCRv5_mobile_det", device="cpu", cpu_threads=args.threads, enable_mkldnn=False)
rec = TextRecognition(model_name="korean_PP-OCRv5_mobile_rec", device="cpu", cpu_threads=args.threads)

SOBI = re.compile(r"소비|유통|까지|기한|EXP|BEST|BBE|BBD|USE\s*BY", re.I)
JEJO = re.compile(r"제조\s*(일|년|연)|포장\s*(일|년)|생산\s*(일|년)|MFD|MFG|PRD|PROD\.?\s*DATE|PACK(ED|ING)?\s*(ON|DATE)", re.I)   # 제조원·제조사 는 제외

rows = []
files = sorted(glob.glob("labels/labels_block*.csv"), key=lambda s: int(re.search(r"block(\d+)", s).group(1)))
want = {int(b) for b in args.blocks.split(",") if b} if args.blocks else None
for f in files:
    b = int(re.search(r"block(\d+)", f).group(1))
    if want and b not in want:
        continue
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        rows.append((b, r["image_id"], r["file"], r["final_date"]))
print(f"{len(rows)}장 스캔")

out = open(args.out, "w", newline="", encoding="utf-8")
w = csv.writer(out); w.writerow(["image_id", "block", "label", "소비키워드", "제조키워드", "후보", "읽힌_텍스트"])
t0 = time.time(); n_cand = 0
for i, (b, iid, fn, label) in enumerate(rows, 1):
    with Image.open(os.path.join(args.images, fn)) as im:
        if im.format in ("JPEG", "MPO"):
            im.draft("RGB", (args.long, args.long))
        im = ImageOps.exif_transpose(im).convert("RGB")
        s = args.long / max(im.size)
        if s < 1:
            im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))))
        img = np.asarray(im)[:, :, ::-1].copy()
    texts = []
    try:
        polys = det.predict(img)[0]["dt_polys"]
        crops = []
        for poly in polys:
            xs, ys = [p[0] for p in poly], [p[1] for p in poly]
            x0, x1, y0, y1 = int(max(0, min(xs))), int(min(img.shape[1], max(xs))), int(max(0, min(ys))), int(min(img.shape[0], max(ys)))
            if x1 - x0 >= 4 and y1 - y0 >= 4:
                crops.append(img[y0:y1, x0:x1])
        for k in range(0, len(crops), 8):
            for res in rec.predict(input=crops[k:k + 8], batch_size=8):
                if res["rec_score"] >= 0.5:
                    texts.append(res["rec_text"])
    except Exception as e:
        texts.append(f"[ERR {type(e).__name__}]")
    joined = " | ".join(texts)
    has_s, has_j = bool(SOBI.search(joined)), bool(JEJO.search(joined))
    cand = has_j and not has_s and label != "NONE"
    n_cand += cand
    w.writerow([iid, b, label, int(has_s), int(has_j), int(cand), joined[:300]])
    if i % 50 == 0 or i == len(rows):
        out.flush(); print(f"[{i}/{len(rows)}] {time.time() - t0:.0f}s · 후보 {n_cand}")
out.close()
print(f"완료 → {args.out}  후보 {n_cand}/{len(rows)} ({100 * n_cand / max(1, len(rows)):.1f}%)")
