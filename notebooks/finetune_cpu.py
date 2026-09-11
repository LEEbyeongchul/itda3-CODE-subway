"""로컬 CPU 로 PP-OCRv5 영문 인식기 파인튜닝 → inference 모델 내보내기 → weights/ 교체본 준비.
GPU 가 없어도 데이터가 수백 장이면 돌아간다 (14코어 기준 샘플당 약 1초). Colab 이 안 될 때의 대안.

    python notebooks/finetune_cpu.py --paddleocr <PaddleOCR 저장소 경로> --pretrained <..._pretrained.pdparams> \
        --data data/rec_train --epochs 10 --out train_out/itda_en_rec

끝나면 <out>/infer/ 에 inference.json / inference.pdiparams / inference.yml 이 생긴다.
파이프라인에 넣으려면:
    cp -r weights/en_PP-OCRv5_mobile_rec weights/en_PP-OCRv5_mobile_rec.pretrained.bak
    cp <out>/infer/inference.* weights/en_PP-OCRv5_mobile_rec/       # config.json 은 그대로
그 뒤 500장에서 eval.py 로 73.6% 와 비교. (주의: torch 를 paddle 보다 먼저 import 해야 Windows 에서 DLL 충돌이 없다.)
"""
import argparse, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRAPPER = os.path.join(ROOT, "notebooks", "_run_paddle_tool.py")
WRAPPER_SRC = '''import sys, runpy
import torch  # noqa: F401  torch 먼저 (Windows DLL 충돌 방지)
script = sys.argv[1]; sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
'''

ap = argparse.ArgumentParser()
ap.add_argument("--paddleocr", required=True, help="git clone 한 PaddleOCR 저장소 경로")
ap.add_argument("--pretrained", required=True, help="en_PP-OCRv5_mobile_rec_pretrained.pdparams 경로")
ap.add_argument("--data", default="data/rec_train")
ap.add_argument("--train-list", default="train_clean.txt")
ap.add_argument("--val-list", default="val_clean.txt")
ap.add_argument("--epochs", type=int, default=10)
ap.add_argument("--lr", type=float, default=0.0001)
ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--warmup", type=int, default=1, help="warmup epoch 수 (기본 config 는 5 → 짧은 학습에선 학습률이 안 오름)")
ap.add_argument("--out", default="train_out/itda_en_rec")
ap.add_argument("--skip-train", action="store_true", help="이미 학습된 best_accuracy 로 내보내기만")
a = ap.parse_args()

open(WRAPPER, "w", encoding="utf-8").write(WRAPPER_SRC)
data = os.path.abspath(os.path.join(ROOT, a.data))
out = os.path.abspath(os.path.join(ROOT, a.out))
cfg = os.path.join(a.paddleocr, "configs", "rec", "PP-OCRv5", "multi_language", "en_PP-OCRv5_mobile_rec.yaml")
py = sys.executable

def run(tool, extra):
    cmd = [py, WRAPPER, os.path.join(a.paddleocr, "tools", tool), "-c", cfg, "-o",
           "Global.use_gpu=False", "Global.distributed=False", f"Global.save_model_dir={out}",
           f"Train.dataset.data_dir={data}/", f"Train.dataset.label_file_list=[{data}/{a.train_list}]",
           "Train.loader.num_workers=0", f"Train.loader.batch_size_per_card={a.batch}",
           f"Eval.dataset.data_dir={data}/", f"Eval.dataset.label_file_list=[{data}/{a.val_list}]",
           "Eval.loader.num_workers=0", "Eval.loader.batch_size_per_card=64"] + extra
    print(">>", tool, " ".join(extra)[:200], flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, cwd=a.paddleocr)
    print(f"<< {tool} exit={r.returncode} {time.time() - t0:.0f}s", flush=True)
    if r.returncode != 0:
        sys.exit(r.returncode)

n_train = sum(1 for _ in open(os.path.join(data, a.train_list), encoding="utf-8"))
n_val = sum(1 for _ in open(os.path.join(data, a.val_list), encoding="utf-8"))
print(f"train {n_train} · val {n_val} · epochs {a.epochs} · lr {a.lr} · batch {a.batch} → {out}")

if not a.skip_train:
    run("train.py", [f"Global.pretrained_model={os.path.abspath(a.pretrained)}", f"Global.epoch_num={a.epochs}",
                     "Global.eval_batch_step=[0,6]", "Global.print_batch_step=1", "Global.save_epoch_step=1",
                     f"Optimizer.lr.learning_rate={a.lr}", f"Optimizer.lr.warmup_epoch={a.warmup}"])

best = os.path.join(out, "best_accuracy")
if not os.path.exists(best + ".pdparams"):
    best = os.path.join(out, "latest")
    print("[WARN] best_accuracy 없음 → latest 사용")
run("eval.py", [f"Global.pretrained_model={best}"])
run("eval.py", [f"Global.pretrained_model={os.path.abspath(a.pretrained)}"])   # 비교 기준: 사전학습 모델의 val 성능
run("export_model.py", [f"Global.pretrained_model={best}", f"Global.save_inference_dir={out}/infer/"])
print("내보내기 완료:", os.listdir(os.path.join(out, "infer")))
