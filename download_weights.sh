#!/usr/bin/env bash
# EasyOCR 가중치를 ./weights 에 사전 다운로드한다.
# 채점 서버는 오프라인이므로 predict.ipynb 실행 전에 (인터넷이 되는 상태에서) 1회 실행해야 한다.
#
#   bash download_weights.sh
#
# 필요 파일 (EasyOCR 1.7.1, lang=['en']):
#   weights/craft_mlt_25k.pth   검출기 (CRAFT)
#   weights/english_g2.pth      영문 인식기
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p weights
export PYTHONUTF8=1   # Windows 콘솔(cp949)에서 EasyOCR 진행바 출력이 깨지는 것 방지. Linux 엔 무해.

PY="${PYTHON:-$(command -v python3 || command -v python)}"   # PYTHON=경로 로 인터프리터 지정 가능

"$PY" - <<'PYEOF'
import os
import easyocr

# download_enabled=True 로 Reader 를 한 번 만들면 EasyOCR 이 알아서 필요한 파일을 model_storage_directory 에 받는다.
easyocr.Reader(["en"], gpu=False, model_storage_directory="./weights", download_enabled=True)

need = ["craft_mlt_25k.pth", "english_g2.pth"]
missing = [f for f in need if not os.path.exists(os.path.join("weights", f))]
if missing:
    raise SystemExit(f"[ERROR] 누락된 가중치: {missing}")
for f in need:
    mb = os.path.getsize(os.path.join("weights", f)) / 1024 / 1024
    print(f"  OK  weights/{f}  ({mb:.1f} MB)")
print("가중치 준비 완료. 이제 predict.ipynb 는 오프라인으로 실행 가능하다.")
PYEOF
