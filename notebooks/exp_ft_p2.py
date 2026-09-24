# 실험: 파인튜닝 인식기를 **2패스 전용**으로 쓴다 (본선계획 §4.1-4). 1패스는 사전학습으로 후보 줄을 찾고, 크롭 재인식만 파인튜닝 인식기로.
#   base     : 사전학습만 (9/23 최종 기본값: P2_KEEP 등급 인식 + COLON + TRUNC, SPAN 꺼짐)
#   ft_p2    : 2패스 크롭 재인식만 파인튜닝 인식기 (단독)
#   ft_union : 사전학습 2패스 후보 ∪ 파인튜닝 2패스 후보 → 선택 규칙 (다수결 대신 합집합)
#   ft_fb    : ft_p2 가 NONE 이면 base 로 (안전판)
# 사용: .venv/Scripts/python notebooks/exp_ft_p2.py <K> <N> [가중치 폴더]   → results/exp_ft_p2_<날짜>_<K>.csv
#   가중치 폴더 기본값 weights/en_PP-OCRv5_mobile_rec_ft (Colab full 가중치, 크롭 정확도 89.8%). 판정용 2,852장(블록 1~5 제외).
import json, os, sys, time, datetime, pandas as pd
os.environ.setdefault("ITDA_THREADS", "4")
K, N = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
FT_DIR = sys.argv[3] if len(sys.argv) > 3 else os.path.join("weights", "en_PP-OCRv5_mobile_rec_ft")
LIMIT = int(os.environ.get("EXP_LIMIT", "0"))          # 스모크 테스트용: 앞 n장만
assert os.path.exists(os.path.join(FT_DIR, "inference.pdiparams")), f"파인튜닝 가중치 없음: {FT_DIR}"
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__exp__", "os": os}
for i in (1, 2, 3, 4, 5): exec(cells[i], g)
g["P2_KEEP"] = True; g["RULE_SPAN"] = False; g["RULE_COLON"] = True; g["RULE_TRUNC"] = True   # 기준선 = 9/23 최종 기본값 (SPAN 은 기각)
load_image, pass1, pass2, select_date, reader = g["load_image"], g["pass1"], g["pass2"], g["select_date"], g["reader"]
from paddleocr import TextRecognition
ft_rec = TextRecognition(model_name="en_PP-OCRv5_mobile_rec", model_dir=FT_DIR, device="cpu", cpu_threads=int(os.environ["ITDA_THREADS"]))
print(f"파인튜닝 인식기 로드: {FT_DIR}")
def key(b):
    if not b: return "NONE"
    y = b["y"] if b["y"] is not None else "NONE"; d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"
def pass2_ft(img, cands):
    reader.rec, old = ft_rec, reader.rec
    try:
        out = pass2(img, cands)
    finally:
        reader.rec = old
    for c in out:
        if c["src"] == "p2": c["src"] = "ft-p2"
    return out
J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
T = J[~J.block.isin(["1", "2", "3", "4", "5"])].iloc[K::N]
if LIMIT: T = T.head(LIMIT)
out = f"results/exp_ft_p2_{datetime.date.today()}_{K}.csv"
rows = []
for n, (_, r) in enumerate(T.iterrows()):
    t = time.time(); img = load_image(f"images/{r.file}"); rec = dict(image_id=r.image_id, label=r.final_date, old=r.pred, tags=r.tags)
    c1, _ = pass1(img)
    if c1:
        a = pass2(img, [dict(c) for c in c1]); b = pass2_ft(img, [dict(c) for c in c1])
        rec["base"] = key(select_date(a)); rec["ft_p2"] = key(select_date(b))
        seen, u = set(), []
        for c in a + b:
            k = (c["y"], c["m"], c["d"], c["kind"])
            if k not in seen: seen.add(k); u.append(c)
        rec["ft_union"] = key(select_date(u))
    else:
        rec["base"] = rec["ft_p2"] = rec["ft_union"] = "NONE"
    rec["ft_fb"] = rec["ft_p2"] if rec["ft_p2"] != "NONE" else rec["base"]
    rec["sec"] = round(time.time() - t, 1); rows.append(rec)
    if n % 25 == 0:
        print(n, len(T), flush=True); pd.DataFrame(rows).to_csv(out, index=False)
D = pd.DataFrame(rows); D.to_csv(out, index=False)
for col in ["base", "ft_p2", "ft_union", "ft_fb"]:
    rec_ = ((D[col] == D.label) & (D.base != D.label)).sum(); reg = ((D[col] != D.label) & (D.base == D.label)).sum()
    print(f"{col:9s}: 정답 {(D[col] == D.label).sum()}/{len(D)}  base 대비 회복 {rec_} / 퇴보 {reg}")
print("done")
