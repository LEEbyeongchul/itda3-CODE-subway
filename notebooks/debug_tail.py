"""꼬리 숫자 규칙이 답을 바꾼 장에서, 규칙이 어느 글자에 발동했고 후보가 단계별로 어떻게 바뀌었는지 본다."""
import csv, json, os, sys
os.environ.setdefault("ITDA_THREADS", "8")
IDS = sys.argv[1].split(",")
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__dbg__", "os": os}
for i in (1, 2, 3, 4, 5):
    exec(cells[i], g)
J = {r["image_id"]: r for r in csv.DictReader(open("results/join_all3352_v6.csv", encoding="utf-8-sig"))}
orig = g["parse_dates"]; LOG = []


def logged(text, dmy_hint=False):
    out = orig(text, dmy_hint=dmy_hint)
    if any(t[3] == "YY_TAIL" for t in out):
        LOG.append((text[:70], [(f"{t[0]}-{t[1]:02d}-{t[2]}", t[3]) for t in out]))
    return out


g["parse_dates"] = logged


def key(c):
    y = c["y"] if c["y"] is not None else "NONE"; d = "NONE" if c["d"] is None else f"{c['d']:02d}"
    return f"{y}-{c['m']:02d}-{d}:{c['kind']}:{c['src']}"


for iid in IDS:
    img = g["load_image"](f"images/{J[iid]['file']}")
    print(f"\n=== {iid} 정답 {J[iid]['final_date']} 태그 '{J[iid]['tags']}'")
    for on in (False, True):
        g["RULE_TAIL"] = on; LOG.clear()
        c1, seen = g["pass1"](img)
        c2 = g["pass2"](img, list(c1)) if c1 else []
        c3 = g["keyword_line_reread"](img, c2, seen) if g["KO_LINE"] else c2
        b = g["select_date"](c3)
        print(f"  [{'켬' if on else '끔'}] 선택 {key(b) if b else 'NONE'}")
        print("     1패스:", [key(c) for c in c1])
        print("     최종 :", [key(c) for c in c3])
        for t, o in LOG:
            print("     꼬리 발동:", repr(t), "→", o)
print("done")
