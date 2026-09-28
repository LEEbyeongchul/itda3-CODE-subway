# 어두운 사진 밝기 보정 실험 — EDA(results/eda_imgq_2026-09-26.csv)에서 평균 밝기 <110 인 사진의 오답률이 24.9% 로
# 나머지(15.7~19%)보다 높고, 파이프라인에 밝기 보정이 없어서 시험한다. 규칙은 구조 규칙 하나(평균 밝기 <110 이면 보정), 임계값 튜닝 없음.
#   .venv/Scripts/python notebooks/exp_dark.py <K> <N>   → results/exp_dark_<EXP_TAG>_<K>.csv
# 대상: 판정용 2,852장 중 평균 밝기 <110 인 549장만 (나머지는 규칙이 발동하지 않으므로 결과가 base 와 같다).
# base 열은 results/exp_rules4_2026-09-23_kol960_merged.csv 의 base(현 기본값 83.9%) 를 그대로 쓴다 — 재실행 안 함.
# 변형:  gamma = 자동 감마(평균을 128 로 보내는 γ = log(0.5)/log(mean/255), 상한 γ 0.4)
#        clahe = LAB 의 L 채널에 CLAHE(clip 2.0, 8×8)
#        both  = gamma 뒤 clahe
import json, os, sys, time, numpy as np, cv2, pandas as pd
os.environ.setdefault("ITDA_THREADS", "4")
K, N = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__exp__", "os": os}
for i in (1, 2, 3, 4, 5): exec(cells[i], g)
load_image, pass1, pass2, select_date = g["load_image"], g["pass1"], g["pass2"], g["select_date"]
DARK = 110

def gamma_fix(img):
    m = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean()
    gam = max(0.4, np.log(0.5) / np.log(max(m, 1) / 255.0))
    lut = (np.linspace(0, 1, 256) ** gam * 255).astype(np.uint8)
    return cv2.LUT(img, lut)

def clahe_fix(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

VARIANTS = {"gamma": gamma_fix, "clahe": clahe_fix, "both": lambda im: clahe_fix(gamma_fix(im))}
if os.environ.get("EXP_VARIANTS"): VARIANTS = {k: v for k, v in VARIANTS.items() if k in os.environ["EXP_VARIANTS"].split(",")}

def key(b):
    if not b: return "NONE"
    y = b["y"] if b["y"] is not None else "NONE"; d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"

def run(img):
    c1, seen = pass1(img); c2 = pass2(img, list(c1)) if c1 else []
    if g.get("KO_LINE"): c2 = g["keyword_line_reread"](img, c2, seen)
    return key(select_date(c2)) if c2 else "NONE"

Q = pd.read_csv("results/eda_imgq_2026-09-26.csv", dtype={"image_id": str}); Q["image_id"] = Q["image_id"].str.zfill(6)
B = pd.read_csv("results/exp_rules4_2026-09-23_kol960_merged.csv", dtype=str, keep_default_na=False)[["image_id", "label", "tags", "base", "block", "two"]]
J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)[["image_id", "file"]]
T = B.merge(Q[["image_id", "mean"]], on="image_id").merge(J, on="image_id")
T = T[T["mean"] < DARK].iloc[K::N]
out = f"results/exp_dark_{os.environ.get('EXP_TAG', '2026-09-26')}_{K}.csv"
rows = []
for n, (_, r) in enumerate(T.iterrows()):
    t = time.time(); img = load_image(f"images/{r.file}")
    rec = dict(image_id=r.image_id, label=r.label, tags=r.tags, base=r.base, block=r.block, two=r.two, mean=round(r["mean"], 1))
    for name, fn in VARIANTS.items(): rec[name] = run(fn(img))
    rec["sec"] = round(time.time() - t, 1); rows.append(rec)
    if n % 25 == 0: print(n, len(T), flush=True); pd.DataFrame(rows).to_csv(out, index=False)
D = pd.DataFrame(rows); D.to_csv(out, index=False)
for name in VARIANTS:
    for lab, sub in (("전체", D), ("병기", D[D.two == "True"]), ("비병기", D[D.two != "True"])):
        rec_ = ((sub[name] == sub.label) & (sub.base != sub.label)).sum(); reg = ((sub[name] != sub.label) & (sub.base == sub.label)).sum()
        print(f"{name} {lab}: 정답 {(sub[name] == sub.label).sum()}/{len(sub)}  base 대비 회복 {rec_} / 퇴보 {reg}")
print("done")
