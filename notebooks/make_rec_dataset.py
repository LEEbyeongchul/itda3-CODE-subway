"""인식기 파인튜닝용 데이터 추출: 라벨된 이미지에서 날짜가 찍힌 크롭을 잘라 라벨 raw 텍스트와 짝짓는다.

    python notebooks/make_rec_dataset.py --blocks 6,7,9,10,14 --out data/rec_train
    python notebooks/make_rec_dataset.py --blocks 6,7,9,10,14 --out data/rec_train --max-dist 2   # 더 엄격하게

원리
- predict.ipynb 의 탐지·인식을 그대로 돌려 단어 박스와 줄 박스를 얻고, 각 박스를 원본 해상도에서 크롭해 다시 인식한다.
- 인식 텍스트와 라벨 raw(포장에 찍힌 그대로)를 정규화(대문자, 공백 제거)해 편집거리를 재고, 가장 가까운 크롭이 --max-dist 이내면 채택.
  이렇게 하면 모델이 조금 틀리게 읽은 크롭(2O27.O6.26)도 정답 텍스트(2027.06.26)로 라벨링된다 = hard sample.
- **블록 1~5 는 측정 전용이라 절대 넣지 않는다** (스크립트가 거부).

출력 (PaddleOCR SimpleDataSet 형식)
  <out>/imgs/<image_id>.jpg
  <out>/train_list.txt   imgs/000123.jpg<TAB>2027.06.26
  <out>/val_list.txt     (--val-blocks 의 블록)
  <out>/manifest.csv     image_id, block, label, ocr_text, dist, source(item|line), w, h, flag  — 검수용. flag: multiline? / extra_text / truncated? 는 검수 우선
  <out>/sheet_XX.jpg     크롭 40개씩 격자 + 라벨/OCR 텍스트. dist 큰 순서. 잘못 짝지어진 크롭은 train_list 에서 줄을 지운다
"""
import argparse, glob, json, os, sys, csv

import cv2
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAGS = {"2", "d", "b", "t", "e", "r"}


def clean_raw(raw):
    toks = raw.strip().split()
    while toks and toks[-1] in TAGS:
        toks.pop()
    return " ".join(toks)


def norm(s):
    return "".join(ch for ch in s.upper() if not ch.isspace())


def lev(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def load_notebook_env():
    nb = json.load(open(os.path.join(ROOT, "predict.ipynb"), encoding="utf-8"))
    cells = [c["source"] if isinstance(c["source"], str) else "".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    g = {"__name__": "__mkds__", "os": os}
    os.chdir(ROOT)
    for i in (1, 2, 3, 4, 5):
        exec(cells[i], g)
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", required=True, help="예: 6,7,9,10,14  (1~5 금지)")
    ap.add_argument("--val-blocks", default="6", help="검증용으로 뺄 블록. 예: 6")
    ap.add_argument("--out", default="data/rec_train")
    ap.add_argument("--max-dist", type=int, default=3, help="정규화 편집거리 허용치")
    ap.add_argument("--min-len", type=int, default=5, help="정규화 raw 최소 길이 (10.14 같은 짧은 것 제외)")
    a = ap.parse_args()

    blocks = [int(b) for b in a.blocks.split(",")]
    if any(b <= 5 for b in blocks):
        sys.exit("블록 1~5 는 측정 전용. 학습 데이터에 넣지 않는다.")
    val_blocks = {int(b) for b in a.val_blocks.split(",") if b}

    labels = pd.concat([pd.read_csv(os.path.join(ROOT, f"labels/labels_block{b}.csv"), dtype=str, keep_default_na=False) for b in blocks])
    labels = labels[labels["final_date"] != "NONE"]
    print(f"라벨 {len(labels)}장 (NONE 제외)")

    g = load_notebook_env()
    reader, load_image, resize_long, group_lines, ocr_prioritized, crop_with_margin = (
        g["reader"], g["load_image"], g["resize_long"], g["group_lines"], g["ocr_prioritized"], g["crop_with_margin"])
    PASS1_LADDER, PASS2_MARGIN = g["PASS1_LADDER"], g["PASS2_MARGIN"]

    out_img = os.path.join(ROOT, a.out, "imgs")
    os.makedirs(out_img, exist_ok=True)
    rows, n_ok = [], 0
    for i, r in enumerate(labels.itertuples(index=False), 1):
        raw = clean_raw(r.raw)
        target = norm(raw)
        if len(target) < a.min_len:
            continue
        try:
            img = load_image(os.path.join(ROOT, "images", r.file))
        except Exception as e:
            print(f"[WARN] {r.image_id}: {e}")
            continue
        best = None
        for L in PASS1_LADDER:
            small, s = resize_long(img, L)
            lines = group_lines(ocr_prioritized(small))
            cands = []   # (bbox 원본좌표, source)
            for ln in lines:
                cands.append(((ln["x0"] / s, ln["y0"] / s, ln["x1"] / s, ln["y1"] / s), "line"))
                if len(ln["items"]) > 1:
                    for it in ln["items"]:
                        cands.append(((it["x0"] / s, it["y0"] / s, it["x1"] / s, it["y1"] / s), "item"))
            crops = [crop_with_margin(img, bb, PASS2_MARGIN) for bb, _ in cands]
            keep = [k for k, c in enumerate(crops) if c is not None and c.size]
            if not keep:
                continue
            texts = reader._rec_many([crops[k] for k in keep], None)
            for k, (t, conf) in zip(keep, texts):
                d = lev(norm(t), target)
                if best is None or d < best[0] or (d == best[0] and crops[k].size < best[2].size):
                    best = (d, t, crops[k], cands[k][1])
            if best and best[0] == 0:
                break
        allow = min(a.max_dist, len(target) // 3)      # 허용 거리는 라벨 길이에 비례: 8자 → 2, 10자 → 3, 5자 → 1
        if best is None or best[0] > allow:
            rows.append({"image_id": r.image_id, "block": r.block, "label": raw, "ocr_text": best[1] if best else "", "dist": best[0] if best else -1,
                         "source": "", "w": 0, "h": 0, "kept": 0, "flag": ""})
        else:
            d, t, crop, src = best
            fn = f"{r.image_id}.jpg"
            ok, buf = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 95])   # imwrite 는 Windows 에서 한글 경로에 조용히 실패한다
            if not ok:
                print(f"[WARN] {r.image_id}: JPEG 인코딩 실패"); continue
            buf.tofile(os.path.join(out_img, fn))
            flags = []
            if crop.shape[0] > 0.35 * crop.shape[1]:
                flags.append("multiline?")                     # 세로가 긴 크롭은 두 줄이 같이 잘렸을 가능성 (실측: 제조일자+소비기한)
            if len(norm(t)) - len(target) >= 3:
                flags.append("extra_text")                     # OCR 텍스트가 라벨보다 3자 이상 길면 날짜 외 글자가 섞인 크롭
            if d >= 2 and len(norm(t)) < len(target):
                flags.append("truncated?")                     # 짧게 읽혔으면 크롭이 잘렸을 가능성
            rows.append({"image_id": r.image_id, "block": r.block, "label": raw, "ocr_text": t, "dist": d, "source": src,
                         "w": crop.shape[1], "h": crop.shape[0], "kept": 1, "flag": " ".join(flags)})
            n_ok += 1
        if i % 50 == 0:
            print(f"[{i}/{len(labels)}] 채택 {n_ok}", flush=True)

    man = pd.DataFrame(rows)
    man.to_csv(os.path.join(ROOT, a.out, "manifest.csv"), index=False, encoding="utf-8-sig")
    kept = man[man.kept == 1]
    with open(os.path.join(ROOT, a.out, "train_list.txt"), "w", encoding="utf-8") as ftr, \
         open(os.path.join(ROOT, a.out, "val_list.txt"), "w", encoding="utf-8") as fva:
        for r in kept.itertuples(index=False):
            (fva if int(r.block) in val_blocks else ftr).write(f"imgs/{r.image_id}.jpg\t{r.label}\n")
    print(f"\n채택 {len(kept)}/{len(man)}  (거리 0: {(kept.dist == 0).sum()}, 1~{a.max_dist}: {(kept.dist > 0).sum()} = hard sample)")
    print(f"train {(~kept.block.astype(int).isin(val_blocks)).sum()} · val {kept.block.astype(int).isin(val_blocks).sum()}  → {a.out}/train_list.txt, val_list.txt")
    print("미채택 이유 상위:", man[man.kept == 0].dist.value_counts().head(5).to_dict(), "(-1 = 크롭 없음, 그 외 = 최소 편집거리)")
    make_sheets(kept, out_img, os.path.join(ROOT, a.out))


def make_sheets(kept, img_dir, out_dir, per=40, cols=4, cell_w=420, cell_h=110):
    """검수용 시트: 크롭과 라벨·OCR 텍스트를 격자로 그린다. dist 내림차순이라 앞 장부터 보면 의심스러운 것부터 본다."""
    from PIL import Image, ImageDraw
    rows = kept.assign(_f=(kept.flag != "").astype(int)).sort_values(["_f", "dist", "image_id"], ascending=[False, False, True]).reset_index(drop=True)
    for si in range(0, len(rows), per):
        chunk = rows.iloc[si:si + per]
        n_rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell_w, n_rows * cell_h), "white")
        d = ImageDraw.Draw(sheet)
        for k, r in enumerate(chunk.itertuples(index=False)):
            x, y = (k % cols) * cell_w, (k // cols) * cell_h
            try:
                im = Image.open(os.path.join(img_dir, f"{r.image_id}.jpg")).convert("RGB")
                im.thumbnail((cell_w - 10, cell_h - 34))
                sheet.paste(im, (x + 5, y + 5))
            except Exception:
                pass
            d.text((x + 5, y + cell_h - 28), f"{r.image_id} d={r.dist} L={r.label}  {r.flag}", fill=(200, 0, 0) if r.flag else "black")
            d.text((x + 5, y + cell_h - 15), f"ocr={str(r.ocr_text)[:40]}", fill=(120, 0, 0))
            d.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(200, 200, 200))
        sheet.save(os.path.join(out_dir, f"sheet_{si // per + 1:02d}.jpg"), quality=85)
    print(f"검수 시트 {(len(rows) + per - 1) // per}장 → {out_dir}/sheet_XX.jpg (dist 큰 것부터)")


if __name__ == "__main__":
    main()
