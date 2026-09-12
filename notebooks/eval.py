"""파이프라인 정확도 평가 + 라벨 분포 EDA.

    python notebooks/eval.py --pred submission.csv                 # labels/labels_block*.csv 전부와 대조
    python notebooks/eval.py --pred submission.csv --blocks 1-5    # 1차 라벨(측정용)만
    python notebooks/eval.py --eda                                 # 예측 없이 라벨 분포만

정답 기준: final_date 완전 일치 (NONE, NONE-MM-DD, YYYY-MM-NONE 도 정답 값).
출력: 전체 정확도, 블록·format·태그·해상도별 정확도, 오답 목록 (--out 으로 CSV 저장).
"""
import argparse, glob, os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG_DESC = {"b": "흐림", "t": "작음", "e": "각인", "r": "회전", "d": "일먼저", "2": "날짜2개+"}


def parse_blocks(spec):
    if not spec:
        return None
    out = set()
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


def load_labels(blocks=None):
    files = sorted(glob.glob(os.path.join(ROOT, "labels", "labels_block*.csv")))
    if not files:
        sys.exit("labels/labels_block*.csv 없음")
    df = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False) for f in files], ignore_index=True)
    df["block"] = df["block"].astype(int)
    if blocks:
        df = df[df["block"].isin(blocks)]
    # 해상도 층(stratum)은 sample.csv 에서 가져온다
    sp = os.path.join(ROOT, "labels", "sample.csv")
    if os.path.exists(sp):
        s = pd.read_csv(sp, dtype=str, keep_default_na=False)[["image_id", "stratum", "w", "h"]]
        df = df.merge(s, on="image_id", how="left")
    else:
        df["stratum"] = ""
    df["tags"] = df["tags"].fillna("").str.replace(" ", "")
    return df.drop_duplicates("image_id")


def rate(sub):
    n = len(sub)
    return f"{sub['ok'].mean() * 100:5.1f}%  ({int(sub['ok'].sum())}/{n})" if n else "   -"


def eda(df):
    print(f"\n라벨 {len(df)}장 · 블록 {sorted(df['block'].unique())}")
    print("\n[format 분포]")
    print(df["format"].value_counts().to_string())
    print("\n[final_date 유형]")
    kind = df["final_date"].map(lambda s: "NONE" if s == "NONE" else
                                "NONE-MM-DD" if s.startswith("NONE") else
                                "YYYY-MM-NONE" if s.endswith("NONE") else "YYYY-MM-DD")
    print(kind.value_counts().to_string())
    print("\n[태그 분포]  (한 장에 여러 태그 가능)")
    for t, desc in TAG_DESC.items():
        n = df["tags"].str.contains(t).sum()
        print(f"  {t} {desc:6s} {n:4d}  ({n / len(df) * 100:.1f}%)")
    if "stratum" in df:
        print("\n[해상도 층]")
        print(df["stratum"].value_counts().to_string())
    yrs = df["year"][df["year"].str.isdigit()].astype(int)
    if len(yrs):
        print("\n[연도 분포]")
        print(yrs.value_counts().sort_index().to_string())


def evaluate(df, pred_path, out_path=None):
    pred = pd.read_csv(pred_path, dtype=str, keep_default_na=False)
    pred["image_id"] = pred["image_id"].str.strip()
    m = df.merge(pred[["image_id", "final_date"]].rename(columns={"final_date": "pred"}), on="image_id", how="left")
    missing = m["pred"].isna().sum()
    if missing:
        print(f"[WARN] 예측이 없는 라벨 {missing}장 → 오답 처리")
    m["pred"] = m["pred"].fillna("(없음)")
    m["ok"] = m["pred"] == m["final_date"]

    print(f"\n========== 정확도 ==========")
    print(f"전체            {rate(m)}")
    print("\n[블록별]")
    for b, g in m.groupby("block"):
        print(f"  block {b:2d}      {rate(g)}")
    if "stratum" in m and m["stratum"].astype(bool).any():
        print("\n[해상도별]")
        for s, g in m.groupby("stratum"):
            print(f"  {s:12s}  {rate(g)}")
    print("\n[format별]  (건수 내림차순)")
    for f, g in sorted(m.groupby("format"), key=lambda x: -len(x[1])):
        print(f"  {f:16s}  {rate(g)}")
    print("\n[태그별]")
    print(f"  {'태그없음':8s}  {rate(m[m['tags'] == ''])}")
    for t, desc in TAG_DESC.items():
        g = m[m["tags"].str.contains(t)]
        if len(g):
            print(f"  {t} {desc:6s}  {rate(g)}")

    wrong = m[~m["ok"]]
    print(f"\n[오답 유형]  총 {len(wrong)}")
    typ = wrong.apply(lambda r: "미검출(NONE)" if r["pred"] == "NONE" else
                      "정답이 NONE인데 검출" if r["final_date"] == "NONE" else
                      "연도만 틀림" if r["pred"][5:] == r["final_date"][5:] else
                      "월/일 틀림" if r["pred"][:4] == r["final_date"][:4] else "전부 틀림", axis=1)
    if len(wrong):
        print(typ.value_counts().to_string())
        print(f"\n[오답 목록]")
        cols = ["image_id", "block", "raw", "final_date", "pred", "format", "tags", "stratum"]
        cols = [c for c in cols if c in wrong]
        print(wrong[cols].to_string(index=False))
    if out_path:
        m.assign(err_type=typ.reindex(m.index).fillna("")).to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"\n→ {out_path} 저장")
    return m


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", help="predict.ipynb 출력 CSV (image_id, final_date)")
    ap.add_argument("--blocks", help="평가할 블록. 예: 1-5 또는 2,7")
    ap.add_argument("--eda", action="store_true", help="라벨 분포만 출력")
    ap.add_argument("--out", help="장별 대조 결과 CSV 저장 경로")
    a = ap.parse_args()
    df = load_labels(parse_blocks(a.blocks))
    eda(df)
    if a.pred:
        evaluate(df, a.pred, a.out)
    elif not a.eda:
        print("\n--pred 를 주면 정확도를 계산합니다.")
