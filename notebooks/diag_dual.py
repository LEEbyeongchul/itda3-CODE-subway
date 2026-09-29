"""현재 기본값(p1det 켬)에서 병기 오답 83장을 다시 돌려, 정답이 어느 단계까지 살아 있었는지 본다. 읽기 전용(결과는 스크래치패드)."""
import csv, json, os, re, sys, time
os.environ.setdefault("ITDA_THREADS", "8")
OUT = sys.argv[1]
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__diag__", "os": os}
for i in (1, 2, 3, 4, 5):
    exec(cells[i], g)
load_image, pass1, pass2, select_date, reread = g["load_image"], g["pass1"], g["pass2"], g["select_date"], g["keyword_line_reread"]
print("KO_LINE", g["KO_LINE"], g["KO_LINE_MODE"], "rec_ko", g.get("rec_ko") is not None, flush=True)

rows = list(csv.DictReader(open("results/exp_rules4_2026-09-26_kolp1det_merged.csv", encoding="utf-8-sig")))
E = [r for r in rows if "2" in (r.get("tags") or "") and r["kol"] != r["label"]]
DATEISH = re.compile(r"\d{2}[./\-:]\d{1,2}")

def key(c):
    y = c["y"] if c["y"] is not None else "NONE"; d = "NONE" if c["d"] is None else f"{c['d']:02d}"
    return f"{y}-{c['m']:02d}-{d}"

import traceback
# 파일명은 join CSV 의 file 열을 쓴다 (003347·003349·003350 은 '3347.jpeg' 꼴이라 image_id + '.jpg' 로는 못 찾는다)
FILES = {jr["image_id"]: jr["file"] for jr in csv.DictReader(open("results/join_all3352_v6.csv", encoding="utf-8-sig"))}
COLS = ["image_id", "label", "prev", "sel", "in_p1", "in_p2", "in_final", "p1", "p2", "final", "src", "kind", "n_dateish", "dateish", "wh", "sec", "err"]

def save():
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(out)

out = []
for n, r in enumerate(E):
    t = time.time()
    try:
        img = load_image(f"images/{FILES.get(r['image_id'], r['image_id'] + '.jpg')}")
        c1, seen = pass1(img)
        k1 = sorted({key(c) for c in c1})
        c2 = pass2(img, c1) if c1 else []
        k2 = sorted({key(c) for c in c2})
        c3 = reread(img, c2, seen) if g["KO_LINE"] else c2
        k3 = sorted({key(c) for c in c3})
        b = select_date(c3)
        sel = key(b) if b else "NONE"
        lines = [ln["text"] for L, ls in seen for ln in ls]
        dl = [t_ for t_ in lines if DATEISH.search(t_)]
        out.append(dict(image_id=r["image_id"], label=r["label"], prev=r["kol"], sel=sel, in_p1=r["label"] in k1, in_p2=r["label"] in k2, in_final=r["label"] in k3,
                        p1=";".join(k1), p2=";".join(k2), final=";".join(k3), src=(b or {}).get("src", ""), kind=(b or {}).get("kind", ""),
                        n_dateish=len(dl), dateish=" || ".join(dl)[:300], wh=f"{img.shape[1]}x{img.shape[0]}", sec=round(time.time() - t, 1), err=""))
    except Exception as e:
        print("ERR", r["image_id"], type(e).__name__, str(e)[:200], flush=True)
        traceback.print_exc()
        out.append(dict(image_id=r["image_id"], label=r["label"], prev=r["kol"], err=f"{type(e).__name__}: {str(e)[:150]}"))
    if n % 10 == 0 or n == len(E) - 1:
        print(n + 1, len(E), flush=True)
        save()
print("done")
