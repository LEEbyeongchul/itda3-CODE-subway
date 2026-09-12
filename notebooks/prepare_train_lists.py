"""make_rec_dataset.py 결과에서 학습 목록을 정리한다: 검수 플래그(multiline?/extra_text/truncated?)가 붙은 크롭을 뺀 clean 목록을 만든다.

    python notebooks/prepare_train_lists.py --dir data/rec_train
→ <dir>/train_clean.txt, <dir>/val_clean.txt  (사람이 시트를 보고 더 지우려면 이 파일을 편집)
"""
import argparse, os
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default="data/rec_train")
ap.add_argument("--val-blocks", default="6")
ap.add_argument("--max-dist", type=int, default=3)
a = ap.parse_args()
m = pd.read_csv(os.path.join(a.dir, "manifest.csv"), dtype=str, keep_default_na=False)
m["dist"] = m["dist"].astype(int)
k = m[(m.kept == "1") & (m.flag == "") & (m.dist <= a.max_dist)]
val = {int(b) for b in a.val_blocks.split(",") if b}
tr = k[~k.block.astype(int).isin(val)]; va = k[k.block.astype(int).isin(val)]
for name, df in (("train_clean.txt", tr), ("val_clean.txt", va)):
    with open(os.path.join(a.dir, name), "w", encoding="utf-8") as f:
        for r in df.itertuples(index=False):
            f.write(f"imgs/{r.image_id}.jpg\t{r.label}\n")
print(f"채택 {int((m.kept=='1').sum())} → 플래그 제외 {len(k)} (train {len(tr)}, val {len(va)}). dist 0: {(k.dist==0).sum()}, hard 1~{a.max_dist}: {(k.dist>0).sum()}")
