# -*- coding: utf-8 -*-
"""YOLO 날짜 영역 검출기 학습 데이터셋 조립.

    python notebooks/make_yolo_dataset.py            # labels/boxes/boxes.csv + images/ → yolo_ds/ (gitignore)
    zip -r yolo_ds.zip yolo_ds                         # Colab 에 업로드

박스 출처: v3 파이프라인이 정답을 맞힌 이미지에서 선택된 후보의 줄 박스 (자동 생성, 사람 손 안 탐).
클래스 하나 'date'. 제조·소비 병기는 둘 다 날짜 영역이지만 자동 박스는 선택된 것 하나뿐 → 학습 시 다른 날짜가
'배경'으로 들어가는 약점이 있음. 시간 되면 병기 이미지(태그 2)만 손으로 박스 추가 권장.
"""
import os, csv, random, shutil, argparse
from PIL import Image, ImageOps

ap = argparse.ArgumentParser()
ap.add_argument("--boxes", default="labels/boxes/boxes.csv")
ap.add_argument("--images", default="images")
ap.add_argument("--out", default="yolo_ds")
ap.add_argument("--val", type=float, default=0.1)
ap.add_argument("--pad", type=float, default=0.08, help="박스 여백 비율 (줄 박스가 빡빡해서 약간 키움)")
ap.add_argument("--seed", type=int, default=42)
args = ap.parse_args()
random.seed(args.seed)

rows = list(csv.DictReader(open(args.boxes, encoding="utf-8")))
random.shuffle(rows)
n_val = int(len(rows) * args.val)
split = {"val": rows[:n_val], "train": rows[n_val:]}
for s in split:
    os.makedirs(f"{args.out}/images/{s}", exist_ok=True); os.makedirs(f"{args.out}/labels/{s}", exist_ok=True)

n = 0
for s, rs in split.items():
    for r in rs:
        src = os.path.join(args.images, r["file"])
        # 파이프라인은 EXIF 보정 + (큰 JPEG 은 draft 축소) 된 좌표계에서 박스를 냈다. 학습 이미지도 같은 방식으로 저장해 좌표를 맞춘다.
        with Image.open(src) as im:
            w0, h0 = im.size
            if im.format in ("JPEG", "MPO"):
                sc = 2000 / max(w0, h0)
                if sc < 1.0:
                    im.draft("RGB", (max(1, int(w0 * sc)), max(1, int(h0 * sc))))
            im = ImageOps.exif_transpose(im).convert("RGB")
            W, H = im.size
            iw, ih = map(int, r["img_wh"].split("x"))
            if (W, H) != (iw, ih):          # 좌표계 불일치 시 비율로 보정
                fx, fy = W / iw, H / ih
            else:
                fx = fy = 1.0
            stem = os.path.splitext(r["file"])[0]
            im.save(f"{args.out}/images/{s}/{stem}.jpg", quality=90)
        x0, y0, x1, y1 = [float(v) for v in r["bbox"].split(",")]
        x0, x1 = x0 * fx, x1 * fx; y0, y1 = y0 * fy, y1 * fy
        bw, bh = x1 - x0, y1 - y0
        x0 = max(0, x0 - bw * args.pad); x1 = min(W, x1 + bw * args.pad)
        y0 = max(0, y0 - bh * args.pad); y1 = min(H, y1 + bh * args.pad)
        cx, cy, bw, bh = (x0 + x1) / 2 / W, (y0 + y1) / 2 / H, (x1 - x0) / W, (y1 - y0) / H
        with open(f"{args.out}/labels/{s}/{stem}.txt", "w") as f:
            f.write(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
        n += 1

with open(f"{args.out}/data.yaml", "w", encoding="utf-8") as f:
    f.write(f"path: {os.path.abspath(args.out)}\ntrain: images/train\nval: images/val\nnames:\n  0: date\n")
print(f"{n}장 → {args.out}/  (train {len(split['train'])}, val {len(split['val'])})")
print("Colab: !yolo detect train model=yolov8n.pt data=yolo_ds/data.yaml imgsz=640 epochs=50 batch=32   (data.yaml 의 path 를 /content/yolo_ds 로 바꿀 것)")
