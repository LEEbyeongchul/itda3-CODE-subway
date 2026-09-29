"""이미지 품질 지표 EDA — 사진 자체의 선명도·밝기·크기가 오답률과 어떻게 얽히는지 본다.

용도
  1) measure : images/ 3,352장을 1스레드로 읽어 장당 지표를 CSV 로 저장 (OCR 없음, 몇 분)
       .venv/Scripts/python notebooks/eda_image_quality.py measure
       → results/eda_imgq_<날짜>.csv
  2) analyze : 지표 CSV 를 라벨 대조(join_all3352_v6)·오답 진단(diag_errors)과 합쳐
       지표 5분위별 오답률, 단계(A/B/C/D)별 지표 중앙값을 출력
       .venv/Scripts/python notebooks/eda_image_quality.py analyze [results/eda_imgq_<날짜>.csv]

지표 (파이프라인과 같은 조건: 긴 변 1024 로 축소한 회색조에서 계산)
  long_px   원본 긴 변(px) — small/mid/large 층 기준
  file_kb   파일 크기 — JPEG 압축 강도의 대리
  lapvar    라플라시안 분산 — 클수록 선명 (블러 지표)
  tenengrad 소벨 기울기 제곱 평균 — 두 번째 선명도 지표
  mean      평균 밝기 0~255
  std       명암 대비 (표준편차)
  clip_hi   255 근처(>=250) 픽셀 비율 — 반사·과노출
  clip_lo   0 근처(<=5) 픽셀 비율 — 어두움
  orient    EXIF Orientation 값 (없으면 1)

CPU 배려: cv2.setNumThreads(1). 다른 세션 속도 측정 중에는 돌리지 않는다.
"""
import sys, os, csv, time
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageOps

cv2.setNumThreads(1)
ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "images"
RES = ROOT / "results"
WORK_LONG = 1024


def load_gray(path):
    with Image.open(path) as im:
        w, h = im.size
        orient = 1
        try:
            orient = int((im.getexif() or {}).get(274, 1))
        except Exception:
            pass
        if im.format in ("JPEG", "MPO"):
            s = WORK_LONG / max(w, h)
            if s < 1.0:
                im.draft("L", (max(1, int(w * s)), max(1, int(h * s))))
        im = ImageOps.exif_transpose(im).convert("L")
        g = np.array(im)
    H, W = g.shape
    s = WORK_LONG / max(H, W)
    if s < 1.0:
        g = cv2.resize(g, (round(W * s), round(H * s)), interpolation=cv2.INTER_AREA)
    return g, max(w, h), orient


def metrics(g):
    g32 = g.astype(np.float32)
    lap = cv2.Laplacian(g32, cv2.CV_32F, ksize=3)
    gx = cv2.Sobel(g32, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g32, cv2.CV_32F, 0, 1, ksize=3)
    return dict(
        lapvar=float(lap.var()),
        tenengrad=float((gx * gx + gy * gy).mean()),
        mean=float(g32.mean()),
        std=float(g32.std()),
        clip_hi=float((g >= 250).mean()),
        clip_lo=float((g <= 5).mean()),
    )


def measure():
    out = RES / f"eda_imgq_{time.strftime('%Y-%m-%d')}.csv"
    files = sorted(p for p in IMG_DIR.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    cols = ["image_id", "file", "long_px", "file_kb", "orient",
            "lapvar", "tenengrad", "mean", "std", "clip_hi", "clip_lo"]
    t0 = time.time()
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, p in enumerate(files, 1):
            try:
                g, long_px, orient = load_gray(p)
                m = metrics(g)
            except Exception as e:  # 깨진 파일은 빈 행으로 남긴다
                m = {}
                long_px, orient = -1, -1
                print("skip", p.name, e)
            row = dict(image_id=p.stem, file=p.name, long_px=long_px,
                       file_kb=round(p.stat().st_size / 1024, 1), orient=orient)
            row.update({k: round(v, 4) for k, v in m.items()})
            w.writerow(row)
            if i % 250 == 0:
                print(f"{i}/{len(files)}  {time.time()-t0:.0f}s", flush=True)
    print("saved", out, f"{time.time()-t0:.0f}s")
    return out


def analyze(path):
    import pandas as pd
    q = pd.read_csv(path, dtype={"image_id": str}); q["image_id"] = q["image_id"].str.zfill(6)
    j = pd.read_csv(RES / "join_all3352_v6.csv", dtype=str)
    j["ok"] = j["ok"].isin(["True", "true", "1"])
    d = pd.read_csv(RES / "diag_errors_2026-09-22.csv", dtype=str)[["image_id", "stage"]]
    d["stage"] = d["stage"].str[0]
    m = q.merge(j[["image_id", "ok", "block", "two", "format"]], on="image_id", how="inner") \
         .merge(d, on="image_id", how="left")
    m["stage"] = m["stage"].fillna("정답")
    m["strat"] = pd.cut(m["long_px"], [0, 1024, 2048, 10**6], labels=["small", "mid", "large"])
    pd.set_option("display.width", 200)

    print(f"\n대상 {len(m)}장, 전체 오답률 {100-100*m.ok.mean():.1f}%\n")
    print("== 단계별 지표 중앙값 (정답 vs A/B/C/D)")
    print(m.groupby("stage")[["long_px", "file_kb", "lapvar", "tenengrad", "mean", "std", "clip_hi", "clip_lo"]]
           .median().round(1).to_string())

    for col in ["lapvar", "tenengrad", "std", "mean", "clip_hi", "file_kb"]:
        print(f"\n== {col} 5분위별 오답률 (Q1=가장 낮음)")
        try:
            m["_q"] = pd.qcut(m[col].rank(method="first"), 5, labels=[f"Q{i}" for i in range(1, 6)])
        except ValueError:
            continue
        g = m.groupby("_q", observed=True).agg(n=("ok", "size"),
                                              err=("ok", lambda s: round(100 - 100 * s.mean(), 1)),
                                              lo=(col, "min"), hi=(col, "max"))
        print(g.to_string())

    print("\n== 층(strat) × lapvar 5분위 오답률 — 크기 효과와 선명도 효과 분리")
    m["_q"] = pd.qcut(m["lapvar"].rank(method="first"), 5, labels=[f"Q{i}" for i in range(1, 6)])
    print(pd.crosstab(m["strat"], m["_q"], values=~m["ok"], aggfunc="mean").mul(100).round(1).to_string())
    print(pd.crosstab(m["strat"], m["_q"]).to_string())

    print("\n== 오답 단계 × 층")
    print(pd.crosstab(m["stage"], m["strat"]).to_string())
    print("\n== EXIF orient 별 오답률")
    print(m.groupby("orient").agg(n=("ok", "size"), err=("ok", lambda s: round(100 - 100 * s.mean(), 1))).to_string())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "measure"
    if cmd == "measure":
        measure()
    elif cmd == "analyze":
        p = sys.argv[2] if len(sys.argv) > 2 else sorted(RES.glob("eda_imgq_*.csv"))[-1]
        analyze(p)
    else:
        print(__doc__)
