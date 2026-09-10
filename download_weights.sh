#!/usr/bin/env bash
# 추론에 필요한 가중치를 ./weights 에 사전 다운로드한다.
# 채점 서버는 오프라인이므로 predict.ipynb 실행 전에 (인터넷이 되는 상태에서) 1회 실행해야 한다.
#
#   bash download_weights.sh
#
# 필요 파일:
#   weights/craft_mlt_25k.pth                    탐지기 (EasyOCR CRAFT, 1.7.1)
#   weights/english_g2.pth                       EasyOCR 영문 인식기 (Reader 초기화에 필요. ITDA_REC=easyocr 일 때 실제 사용)
#   weights/PP-OCRv5_mobile_det/                 PaddleOCR 텍스트 탐지기 (기본 탐지기, 약 5MB)
#   weights/en_PP-OCRv5_mobile_rec/              PaddleOCR 영문 인식기 (기본 인식기, 약 8MB)
#       각 폴더: inference.json / inference.pdiparams / inference.yml / config.json
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p weights
export PYTHONUTF8=1   # Windows 콘솔(cp949)에서 진행바 출력이 깨지는 것 방지. Linux 엔 무해.

PY="${PYTHON:-$(command -v python3 || command -v python)}"   # PYTHON=경로 로 인터프리터 지정 가능

"$PY" - <<'PYEOF'
import os, shutil
import torch          # paddle 보다 먼저 import (Windows DLL 충돌 방지)
import easyocr

# ---- EasyOCR: download_enabled=True 로 Reader 를 한 번 만들면 필요한 파일을 model_storage_directory 에 받는다.
easyocr.Reader(["en"], gpu=False, model_storage_directory="./weights", download_enabled=True)

# ---- PaddleOCR 탐지기·인식기: 공식 모델을 캐시(~/.paddlex/official_models)에 받은 뒤 weights/ 로 복사한다.
from paddleocr import TextDetection, TextRecognition
FILES = ["inference.json", "inference.pdiparams", "inference.yml", "config.json"]
need = ["craft_mlt_25k.pth", "english_g2.pth"]
for name, cls, kw in [("PP-OCRv5_mobile_det", TextDetection, {"enable_mkldnn": False}),
                      ("en_PP-OCRv5_mobile_rec", TextRecognition, {})]:
    dst = os.path.join("weights", name)
    if not os.path.exists(os.path.join(dst, "inference.pdiparams")):
        cls(model_name=name, device="cpu", **kw)            # 다운로드 트리거
        src = os.path.join(os.path.expanduser("~"), ".paddlex", "official_models", name)
        os.makedirs(dst, exist_ok=True)
        for f in FILES:
            shutil.copy(os.path.join(src, f), dst)
    need += [f"{name}/{f}" for f in FILES]
missing = [f for f in need if not os.path.exists(os.path.join("weights", f))]
if missing:
    raise SystemExit(f"[ERROR] 누락된 가중치: {missing}")
for f in need:
    mb = os.path.getsize(os.path.join("weights", f)) / 1024 / 1024
    print(f"  OK  weights/{f}  ({mb:.1f} MB)")
print("가중치 준비 완료. 이제 predict.ipynb 는 오프라인으로 실행 가능하다.")
PYEOF
