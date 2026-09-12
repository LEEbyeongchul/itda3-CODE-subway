import json, os, sys, cv2, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = [c["source"] for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__dot__", "os": os}
for i in (1, 2, 3, 4, 5): exec(cells[i], g)
load_image, pass1, pass2, select_date = g["load_image"], g["pass1"], g["pass2"], g["select_date"]
ids = sys.argv[1].split(","); raws = dict(zip(ids, sys.argv[2].split("|")))
def blur(img, s):  return cv2.GaussianBlur(img, (0, 0), s)
def close_dark(img, k):   # 어두운 점(잉크)을 이어 붙임: 그레이 반전 후 팽창 = 원본 침식
    return cv2.erode(img, np.ones((k, k), np.uint8))
def close_light(img, k):  return cv2.dilate(img, np.ones((k, k), np.uint8))
variants = {"none": lambda im: im, "blur1": lambda im: blur(im, 1.0), "blur2": lambda im: blur(im, 2.0),
            "erode2": lambda im: close_dark(im, 2), "erode3": lambda im: close_dark(im, 3), "dilate2": lambda im: close_light(im, 2)}
rows = []
for iid in ids:
    img = load_image(f"images/{iid}.jpg")
    h, w = img.shape[:2]; s = 1024 / max(h, w)
    base = cv2.resize(img, (int(w*s), int(h*s)), interpolation=cv2.INTER_AREA) if s < 1 else img   # 전처리는 1024 기준에서
    row = {"id": iid, "정답": raws[iid]}
    for name, f in variants.items():
        im = f(base)
        try:
            cands, _ = pass1(im)
            if cands: cands = pass2(im, cands)
            b = select_date(cands)
            row[name] = f"{b['y']}-{b['m']:02d}-{b['d'] if b['d'] is None else f'{b['d']:02d}'}" if b else "NONE"
        except Exception as e:
            row[name] = f"ERR {type(e).__name__}"
    rows.append(row); print(row, flush=True)
df = pd.DataFrame(rows); print(df.to_string(index=False))
