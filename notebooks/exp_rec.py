"""Phase 1 실험: 인식기만 교체해 본다. 탐지(EasyOCR CRAFT)·후처리는 predict.ipynb 그대로.
(결론: PP-OCRv5 채택, predict.ipynb 본체에 반영됨. 이 스크립트는 다른 인식 모델을 비교할 때 계속 쓴다.)

    python notebooks/exp_rec.py --rec easyocr  --input DIR --output pred_easy.csv
    python notebooks/exp_rec.py --rec en_PP-OCRv3_mobile_rec --input DIR --output pred_v3.csv
    python notebooks/exp_rec.py --rec en_PP-OCRv4_mobile_rec --input DIR --output pred_v4.csv

predict.ipynb 의 파라미터·파서·파이프라인 셀을 그대로 불러오고, `reader.recognize` 만 PaddleOCR 인식기로 바꿔 끼운다.
그래서 두 실행의 차이는 오직 인식기다. 결과 CSV 는 notebooks/eval.py 로 라벨과 대조한다.
PaddleOCR 모델은 첫 실행 때 ~/.paddlex/official_models/ 에 내려받는다 (인터넷 필요. 제출본은 weights/ 로 옮겨야 함).
"""
import argparse, glob, json, os, sys, time
from collections import Counter

import cv2
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB = os.path.join(ROOT, "predict.ipynb")


def load_cells():
    nb = json.load(open(NB, encoding="utf-8"))
    code = [c["source"] if isinstance(c["source"], str) else "".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    # 0: CONFIG, 1: import+파라미터, 2: 이미지 유틸, 3: 파서, 4: reader 생성, 5: 파이프라인 함수, 6: 루프, 7: 저장
    return code


class PaddleRecProxy:
    """EasyOCR Reader 인터페이스를 흉내 낸다. detect 는 원래 reader 로, recognize 는 PaddleOCR 인식기로."""

    def __init__(self, real_reader, model_name, threads, torch_threads=None):
        from paddleocr import TextRecognition
        import torch
        self.real = real_reader
        # 실측: Paddle 인식기가 첫 predict 에서 torch 의 intra-op 스레드를 1로 떨어뜨린다 (OpenMP 전역 설정 공유).
        # 그대로 두면 CRAFT 탐지가 2.5s → 8.9s. 탐지 직전마다 torch 스레드를 되돌린다.
        self._torch = torch
        self.torch_threads = torch_threads or torch.get_num_threads()
        kw = {"model_name": model_name, "device": "cpu"}
        try:
            self.rec = TextRecognition(**kw, cpu_threads=threads)
        except TypeError:
            self.rec = TextRecognition(**kw)
        self.n_calls = self.t_rec = self.t_det = self.n_det = 0.0

    def detect(self, *a, **k):
        self._torch.set_num_threads(self.torch_threads)
        t0 = time.time()
        r = self.real.detect(*a, **k)
        self.t_det += time.time() - t0
        self.n_det += 1
        return r

    def _rec_one(self, crop, allowlist):
        if crop is None or crop.size == 0 or min(crop.shape[:2]) < 2:
            return "", 0.0
        if crop.ndim == 2:
            crop = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        t0 = time.time()
        res = list(self.rec.predict(input=crop, batch_size=1))
        self.t_rec += time.time() - t0
        self.n_calls += 1
        if not res:
            return "", 0.0
        r = res[0]
        text, conf = r["rec_text"], float(r["rec_score"])
        if allowlist:
            # Paddle 은 allowlist 를 지원하지 않으므로 사후 필터. 삭제하면 '2021(3)'→'20213' 처럼 숫자가 붙어 버리니 공백으로 치환.
            text = "".join(c if c in allowlist else " " for c in text)
        return text, conf

    def recognize(self, img, horizontal_list=None, free_list=None, allowlist=None, reformat=True, **k):
        out = []
        if horizontal_list:
            for (x0, x1, y0, y1) in horizontal_list:
                text, conf = self._rec_one(img[y0:y1, x0:x1], allowlist)
                out.append(([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], text, conf))
        else:
            h, w = img.shape[:2]
            text, conf = self._rec_one(img, allowlist)
            out.append(([[0, 0], [w, 0], [w, h], [0, h]], text, conf))
        return out


class TimedReader:
    """EasyOCR 모드에서도 탐지·인식 시간을 따로 잰다 (Paddle 모드와 공정 비교용)."""

    def __init__(self, real):
        self.real = real
        self.n_calls = self.t_rec = self.t_det = self.n_det = 0.0

    def detect(self, *a, **k):
        t0 = time.time()
        r = self.real.detect(*a, **k)
        self.t_det += time.time() - t0
        self.n_det += 1
        return r

    def recognize(self, *a, **k):
        t0 = time.time()
        r = self.real.recognize(*a, **k)
        self.t_rec += time.time() - t0
        self.n_calls += 1
        return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rec", default="easyocr", help="easyocr | PaddleOCR 인식 모델명 (en_PP-OCRv3_mobile_rec 등)")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 4, help="Paddle 인식기 스레드")
    ap.add_argument("--torch-threads", type=int, default=0, help="탐지기(torch) 스레드. 0이면 노트북 기본값(cpu_count)")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()

    os.chdir(ROOT)                      # WEIGHTS_DIR="./weights" 상대경로
    os.environ["ITDA_DEBUG"] = "1" if a.debug else ""
    os.environ["ITDA_REC"] = "easyocr"  # 노트북이 기본으로 만드는 Paddle 인식기 대신 순수 EasyOCR reader 를 받아, 여기서 인식기를 골라 끼운다
    cells = load_cells()
    g = {"__name__": "__exp__", "os": os}   # CONFIG 셀(cells[0])은 건너뛰므로 os 만 직접 넣는다
    exec(cells[1], g)                   # import + 파라미터 (torch 스레드 설정 포함)
    exec(cells[2], g)                   # load_image, resize_long, crop_with_margin
    exec(cells[3], g)                   # parse_dates 등 + 자가검증
    exec(cells[4], g)                   # reader = easyocr.Reader(...)  (offline)
    if a.rec != "easyocr":
        g["reader"] = PaddleRecProxy(g["reader"], a.rec, a.threads, a.torch_threads or None)
        print(f"인식기 교체: {a.rec}")
    else:
        g["reader"] = TimedReader(g["reader"])
    if a.torch_threads:
        g["torch"].set_num_threads(a.torch_threads)
    exec(cells[5], g)                   # group_lines, ocr_prioritized, pass1, pass2, select_date

    load_image, pass1, pass2, select_date = g["load_image"], g["pass1"], g["pass2"], g["select_date"]
    IMG_EXT, DEBUG = g["IMG_EXT"], g["DEBUG"]
    files = [p for p in sorted(glob.glob(os.path.join(a.input, "*.*"))) if os.path.splitext(p)[1].lower() in IMG_EXT]
    print(f"입력 {len(files)}장 · 인식기 {a.rec} · 스레드 {a.threads}")

    rows, kinds = [], Counter()
    n_none = 0
    t_all = time.time()
    for i, path in enumerate(files, 1):
        img_id = os.path.splitext(os.path.basename(path))[0]
        best, cands = None, []
        t0 = time.time()
        try:
            img = load_image(path)
            cands, p1_lines = pass1(img)
            if cands:
                cands = pass2(img, cands)
            best = select_date(cands)
        except Exception as e:
            print(f"[WARN] {img_id}: {type(e).__name__}: {e}")
        if DEBUG:
            fmt = lambda c: f"{c['y'] or 'NONE'}-{c['m']:02d}-" + ("NONE" if c["d"] is None else f"{c['d']:02d}")
            print(f"  {img_id}: {time.time() - t0:.1f}s → {fmt(best) if best else 'NONE'}")
            for c in cands:
                print(f"      cand {fmt(c)} {c['kind']:8s} {c['src']:7s} conf={c['conf']:.2f}  text='{c['text'][:80]}'")
            if not cands:
                for L, lines in p1_lines:
                    print(f"      p1@{L}: {[(ln['text'][:30], round(ln['conf'], 2)) for ln in lines[:8]]}")
        if best is None:
            n_none += 1
            y, m, d = None, None, None
        else:
            y, m, d = best["y"], best["m"], best["d"]
            kinds[best["kind"]] += 1
        ys = f"{y:04d}" if y is not None else "NONE"
        ms = f"{m:02d}" if m is not None else "NONE"
        ds = f"{d:02d}" if d is not None else "NONE"
        fd = "NONE" if (y is None and m is None and d is None) else f"{ys}-{ms}-{ds}"
        rows.append({"image_id": img_id, "year": ys, "month": ms, "day": ds, "final_date": fd})
        if i % 25 == 0 or i == len(files):
            el = time.time() - t_all
            print(f"[{i}/{len(files)}] {el:.0f}s · 장당 {el / i:.2f}s · 후보없음 {n_none}", flush=True)

    pd.DataFrame(rows).to_csv(a.output, index=False)
    total = time.time() - t_all
    print(f"Saved → {a.output}  총 {total:.0f}s · 장당 {total / max(1, len(files)):.2f}s · 후보없음 {n_none}")
    print("패턴 분포:", dict(kinds))
    r = g["reader"]
    if isinstance(r, PaddleRecProxy):
        print(f"Paddle 인식 호출 {int(r.n_calls)}회 · 인식 총 {r.t_rec:.0f}s · 호출당 {r.t_rec / max(1, r.n_calls) * 1000:.0f}ms")
        print(f"CRAFT 탐지 호출 {int(r.n_det)}회 · 탐지 총 {r.t_det:.0f}s · 호출당 {r.t_det / max(1, r.n_det) * 1000:.0f}ms")
    elif isinstance(r, TimedReader):
        print(f"EasyOCR 인식 호출 {int(r.n_calls)}회 · 인식 총 {r.t_rec:.0f}s · 호출당 {r.t_rec / max(1, r.n_calls) * 1000:.0f}ms")
        print(f"CRAFT 탐지 호출 {int(r.n_det)}회 · 탐지 총 {r.t_det:.0f}s · 호출당 {r.t_det / max(1, r.n_det) * 1000:.0f}ms")


if __name__ == "__main__":
    main()
