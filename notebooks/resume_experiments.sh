#!/usr/bin/env bash
# 9/11 21:56 중단 지점에서 이어 가는 실험 체인. 각 단계는 독립적으로도 실행 가능.
#   bash notebooks/resume_experiments.sh 803      # 나머지 803장을 현재 파이프라인으로 → 라벨 1,303장 전체 정확도·신뢰구간 (약 25분)
#   bash notebooks/resume_experiments.sh vote     # 2패스 다수결(ITDA_P2VOTE=1) 튜닝 300장 → 회복/퇴보 (약 13분)
#   bash notebooks/resume_experiments.sh extra    # 폴백 확장(ITDA_DOTFIX_EXTRA=1) 튜닝 300장 (약 15분)
#   bash notebooks/resume_experiments.sh vote500  # 300 에서 회복>퇴보 였을 때만: 500장 확인 (약 20분)
#   bash notebooks/resume_experiments.sh extra500
# 채택 기준: 500장에서 회복 > 퇴보, 4코어 시간(ITDA_THREADS=4 + cpu_affinity) 장당 4초 이내. 채택하면 predict.ipynb 의 기본값(ITDA_P2VOTE / ITDA_DOTFIX_EXTRA 의 "0")을 "1" 로.
set -euo pipefail
cd "$(dirname "$0")/.."; export PYTHONUTF8=1
PY=.venv/Scripts/python; [ -x "$PY" ] || PY=python
mkval() {  # $1 = 폴더, $2.. = 블록
  local d=$1; shift; [ -d "$d" ] && return
  $PY - "$d" "$@" <<'PY'
import sys, pandas as pd, shutil, os
d, blocks = sys.argv[1], sys.argv[2:]; os.makedirs(d, exist_ok=True)
for b in blocks:
    for f in pd.read_csv(f"labels/labels_block{b}.csv", dtype=str, keep_default_na=False)["file"]:
        shutil.copy(os.path.join("images", f), d)
PY
}
run() {  # $1 이름, $2 입력폴더, $3 블록, $4 비교 기준 eval csv
  local N=$1 IN=$2 BL=$3 REF=$4; export ITDA_INPUT_DIR="$IN" ITDA_OUTPUT_PATH="results/pred_$N.csv"
  local S=$(date +%s)
  $PY -m jupyter nbconvert --to notebook --execute predict.ipynb --output "${TEMP:-/tmp}/run_$N.ipynb" --ExecutePreprocessor.timeout=3600 2>&1 | grep -i "error\|Traceback" | head -2 || true
  echo "$N: $(( $(date +%s) - S ))s"; $PY notebooks/eval.py --pred "results/pred_$N.csv" --blocks "$BL" --out "results/eval_$N.csv" | grep "전체 "
  $PY - "$REF" "results/eval_$N.csv" <<'PY'
import sys, pandas as pd
a=pd.read_csv(sys.argv[1],dtype=str,keep_default_na=False).set_index("image_id"); b=pd.read_csv(sys.argv[2],dtype=str,keep_default_na=False).set_index("image_id")
m=a[["raw","final_date","pred","ok"]].join(b[["pred","ok"]],rsuffix="_b")
print("회복", ((m.ok=="False")&(m.ok_b=="True")).sum(), "퇴보", ((m.ok=="True")&(m.ok_b=="False")).sum())
print("--- 퇴보:"); print(m[(m.ok=="True")&(m.ok_b=="False")][["raw","final_date","pred","pred_b"]].head(10).to_string())
print("--- 회복:"); print(m[(m.ok=="False")&(m.ok_b=="True")][["raw","final_date","pred","pred_b"]].head(10).to_string())
PY
}
case "${1:-}" in
  803)
    mkval data/val_rest 6 7 9 10 14
    export ITDA_INPUT_DIR=data/val_rest ITDA_OUTPUT_PATH=results/pred_rest803_2026-09-11_v3_dotfix.csv
    $PY -m jupyter nbconvert --to notebook --execute predict.ipynb --output "${TEMP:-/tmp}/run_rest_v3.ipynb" --ExecutePreprocessor.timeout=3600 2>&1 | grep -i "error\|Traceback" | head -2 || true
    $PY notebooks/eval.py --pred results/pred_rest803_2026-09-11_v3_dotfix.csv --blocks 6,7,9,10,14 --out results/eval_rest803_2026-09-11_v3_dotfix.csv | sed -n '/정확도/,/해상도별/p'
    $PY - <<'PY'
import pandas as pd
a=pd.read_csv("results/eval500_2026-09-11_v3_dotfix.csv",dtype=str,keep_default_na=False); b=pd.read_csv("results/eval_rest803_2026-09-11_v3_dotfix.csv",dtype=str,keep_default_na=False)
n=len(a)+len(b); k=(a.ok=="True").sum()+(b.ok=="True").sum(); p=k/n; se=(p*(1-p)/n)**0.5
print(f"라벨 전체 {n}장: {p*100:.1f}% ({k}/{n})  95% CI ±{1.96*se*100:.1f}%p → {(p-1.96*se)*100:.1f}~{(p+1.96*se)*100:.1f}%")
PY
    ;;
  vote)     mkval data/val300 6 9 10; export ITDA_P2VOTE=1 ITDA_DOTFIX_EXTRA=0; run 300_vote  data/val300 6,9,10 results/eval300_tune_2026-09-11_v3_dotfix.csv ;;
  extra)    mkval data/val300 6 9 10; export ITDA_P2VOTE=0 ITDA_DOTFIX_EXTRA=1; run 300_extra data/val300 6,9,10 results/eval300_tune_2026-09-11_v3_dotfix.csv ;;
  vote500)  mkval data/val500 1 2 3 4 5; export ITDA_P2VOTE=1 ITDA_DOTFIX_EXTRA=0; run 500_vote  data/val500 1-5 results/eval500_2026-09-11_v3_dotfix.csv ;;
  extra500) mkval data/val500 1 2 3 4 5; export ITDA_P2VOTE=0 ITDA_DOTFIX_EXTRA=1; run 500_extra data/val500 1-5 results/eval500_2026-09-11_v3_dotfix.csv ;;
  *) echo "usage: $0 {803|vote|extra|vote500|extra500}"; exit 1 ;;
esac
