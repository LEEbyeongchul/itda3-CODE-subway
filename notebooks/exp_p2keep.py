# 실험: 2패스가 1패스 후보를 지우지 못하게(같은 연·월 후보가 2패스에 없으면 1패스 후보 유지) + 공백 구분 YY MM DD 보조 패턴.
# 병기(태그 2) 349장 전부에서 기존(pred_all3352 v6)과 비교.
import json, os, re, time, pandas as pd
os.environ.setdefault("ITDA_THREADS", "4")
S = "results"
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__exp__", "os": os}
for i in (1, 2, 3, 4, 5): exec(cells[i], g)
load_image, pass1, pass2, select_date = g["load_image"], g["pass1"], g["pass2"], g["select_date"]
_SP3 = re.compile(r"(?<!\d)(\d{2})\s+(\d{2})\s+(\d{2})(?!\d)")
def sp_ymd(text):
    out = []
    for a, b, c in _SP3.findall(text):
        y, m, d = 2000 + int(a), int(b), int(c)
        if 2017 <= y <= 2031 and 1 <= m <= 12 and 1 <= d <= 31:
            out.append((y, m, d))
    return out
def p2_keep(img, cands, sp=False):
    out = pass2(img, cands)
    keys = {(c["y"], c["m"]) for c in out}
    for c in cands:
        if (c["y"], c["m"]) not in keys:
            out.append({**c, "src": "p1keep/" + c["src"]}); keys.add((c["y"], c["m"]))
    if sp:
        for c in list(out):
            for (y, m, d) in sp_ymd(c.get("text", "")):
                if (y, m) not in keys:
                    out.append({**c, "y": y, "m": m, "d": d, "kind": "YY", "src": "spymd/" + c["src"]}); keys.add((y, m))
    return out
def key(b):
    if not b: return "NONE"
    y = b["y"] if b["y"] is not None else "NONE"; d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"
J = pd.read_csv(f"{S}/join_all3352_v6.csv", dtype=str, keep_default_na=False)
T = J[J.tags.str.contains("2")]
rows = []
for n, (_, r) in enumerate(T.iterrows()):
    t = time.time()
    img = load_image(f"images/{r.file}")
    c1, _ = pass1(img)
    base = key(select_date(pass2(img, list(c1)))) if c1 else "NONE"
    ka = key(select_date(p2_keep(img, list(c1)))) if c1 else "NONE"
    kb = key(select_date(p2_keep(img, list(c1), sp=True))) if c1 else "NONE"
    rows.append(dict(image_id=r.image_id, label=r.final_date, old=r.pred, base=base, keep=ka, keep_sp=kb, sec=round(time.time() - t, 1)))
    if n % 25 == 0:
        print(n, len(T), flush=True); pd.DataFrame(rows).to_csv(f"{S}/exp_p2keep_tag2_2026-09-22.csv", index=False)
D = pd.DataFrame(rows); D.to_csv(f"{S}/exp_p2keep_tag2_2026-09-22.csv", index=False)
for col in ["old", "base", "keep", "keep_sp"]:
    print(col, "정확", (D[col] == D.label).sum(), "/", len(D))
for col in ["keep", "keep_sp"]:
    rec = ((D[col] == D.label) & (D.base != D.label)).sum(); reg = ((D[col] != D.label) & (D.base == D.label)).sum()
    print(f"{col}: 회복 {rec} / 퇴보 {reg}")
print("done")
