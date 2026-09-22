# 오답 603장: 정답이 어느 단계(1패스 후보 / 2패스 후보 / 선택)까지 살아 있었는지 진단
import json, os, sys, time, pandas as pd
os.environ.setdefault("ITDA_THREADS", "8")
S = "results"
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__diag__", "os": os}
for i in (1, 2, 3, 4, 5): exec(cells[i], g)
load_image, pass1, pass2, select_date = g["load_image"], g["pass1"], g["pass2"], g["select_date"]
J = pd.read_csv(f"{S}/join_all3352_v6.csv", dtype=str, keep_default_na=False)
J["ok"] = J.final_date == J.pred
E = J[~J.ok]
def key(c): 
    y = c[0] if c[0] is not None else "NONE"; d = "NONE" if c[2] is None else f"{c[2]:02d}"
    return f"{y}-{c[1]:02d}-{d}"
rows = []
for n, (_, r) in enumerate(E.iterrows()):
    t = time.time()
    try:
        img = load_image(f"images/{r.file}")
        c1, seen = pass1(img)
        k1 = {key((c["y"], c["m"], c["d"])) for c in c1}
        c2 = pass2(img, c1) if c1 else []
        k2 = {key((c["y"], c["m"], c["d"])) for c in c2}
        b = select_date(c2)
        sel = key((b["y"], b["m"], b["d"])) if b else "NONE"
        kinds = {c["kind"] for c in c2}
        texts = " || ".join(ln["text"] for L, lines in seen for ln in lines)[:300]
        rows.append(dict(image_id=r.image_id, label=r.final_date, tags=r.tags, fmt=r.format, sel=sel, sel_kind=(b or {}).get("kind", ""), sel_src=(b or {}).get("src", ""),
                         in_p1=r.final_date in k1, in_p2=r.final_date in k2, n_p1=len(c1), n_p2=len(c2), p1=";".join(sorted(k1)), p2=";".join(sorted(k2)),
                         kinds=";".join(sorted(kinds)), ocr=texts, sec=round(time.time() - t, 1)))
    except Exception as e:
        rows.append(dict(image_id=r.image_id, label=r.final_date, err=str(e)[:100]))
    if n % 25 == 0:
        print(n, len(E), flush=True); pd.DataFrame(rows).to_csv(f"{S}/diag_errors_2026-09-22.csv", index=False)
pd.DataFrame(rows).to_csv(f"{S}/diag_errors_2026-09-22.csv", index=False); print("done")
