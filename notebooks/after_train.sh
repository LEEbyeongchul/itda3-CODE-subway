#!/usr/bin/env bash
# 파인튜닝 결과 검증: train_out/<name>/infer 를 weights/ 에 교체(백업 유지) → 측정용 500장 실행 → 평가 → 사전학습(73.6%) 대비 장별 회복·퇴보
#   bash notebooks/after_train.sh [train_out/itda_en_rec]
set -euo pipefail
cd "$(dirname "$0")/.."; export PYTHONUTF8=1
OUT="${1:-train_out/itda_en_rec}"; INF="$OUT/infer"
ls "$INF"
[ -d weights/en_PP-OCRv5_mobile_rec.pretrained.bak ] || cp -r weights/en_PP-OCRv5_mobile_rec weights/en_PP-OCRv5_mobile_rec.pretrained.bak
cp "$INF"/inference.* weights/en_PP-OCRv5_mobile_rec/
if [ ! -d data/val500 ]; then   # 측정용 500장(블록 1~5) 폴더가 없으면 라벨에서 만든다
  .venv/Scripts/python - <<'PY'
import pandas as pd, shutil, os
os.makedirs("data/val500", exist_ok=True)
for b in range(1, 6):
    for f in pd.read_csv(f"labels/labels_block{b}.csv", dtype=str, keep_default_na=False)["file"]:
        shutil.copy(os.path.join("images", f), "data/val500")
PY
fi
export ITDA_INPUT_DIR=./data/val500 ITDA_OUTPUT_PATH=./results/pred500_ft.csv
.venv/Scripts/python -m jupyter nbconvert --to notebook --execute predict.ipynb --output "$TEMP/run500_ft.ipynb" --ExecutePreprocessor.timeout=3600 2>&1 | grep -i "error\|Traceback" | head -3 || true
.venv/Scripts/python notebooks/eval.py --pred results/pred500_ft.csv --blocks 1-5 --out results/eval500_ft.csv | sed -n '/정확도/,/오답 유형/p'
.venv/Scripts/python - <<'PY'
import pandas as pd
a=pd.read_csv("results/eval500_2026-09-10_v2.csv",dtype=str,keep_default_na=False).set_index("image_id")
b=pd.read_csv("results/eval500_ft.csv",dtype=str,keep_default_na=False).set_index("image_id")
m=a[["raw","final_date","pred","ok"]].join(b[["pred","ok"]],rsuffix="_ft")
print(f"사전학습 {(a.ok=='True').mean()*100:.1f}% → 파인튜닝 {(b.ok=='True').mean()*100:.1f}%   회복 {((m.ok=='False')&(m.ok_ft=='True')).sum()}  퇴보 {((m.ok=='True')&(m.ok_ft=='False')).sum()}")
print("--- 퇴보:"); print(m[(m.ok=='True')&(m.ok_ft=='False')][["raw","final_date","pred","pred_ft"]].head(15).to_string())
print("--- 회복:"); print(m[(m.ok=='False')&(m.ok_ft=='True')][["raw","final_date","pred","pred_ft"]].head(15).to_string())
PY
echo "원래 가중치로 되돌리려면: cp weights/en_PP-OCRv5_mobile_rec.pretrained.bak/* weights/en_PP-OCRv5_mobile_rec/"
