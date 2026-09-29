"""1차 판정 검증: 기준선(9/26 실행)과 답이 달라진 장을 같은 프로세스에서 규칙 끔/켬으로 다시 돌려, 변화가 규칙 때문인지(끔 = 기준선 재현) 확인한다.
추가로 답이 안 바뀐 장 가운데 무작위 표본을 끔으로 돌려 기준선 재현율(실행 간 흔들림)을 잰다."""
import csv, glob, json, os, random, sys
os.environ.setdefault("ITDA_THREADS", "8")
OUT = sys.argv[1]; NSAMPLE = int(sys.argv[2]) if len(sys.argv) > 2 else 40
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__verify__", "os": os}
for i in (1, 2, 3, 4, 5):
    exec(cells[i], g)
base = {r["image_id"]: r for r in csv.DictReader(open("results/exp_rules4_2026-09-26_kolp1det_merged.csv", encoding="utf-8-sig"))}
J = {r["image_id"]: r["file"] for r in csv.DictReader(open("results/join_all3352_v6.csv", encoding="utf-8-sig"))}
rows = []
for f in sorted(glob.glob("results/exp_rules4_2026-09-27_sepmix_[0-9].csv")):
    rows += list(csv.DictReader(open(f, encoding="utf-8-sig")))
changed = [r["image_id"] for r in rows if r["sep"] != base[r["image_id"]]["kol"]]
same = [r["image_id"] for r in rows if r["sep"] == base[r["image_id"]]["kol"]]
random.seed(927)
sample = random.sample(same, min(NSAMPLE, len(same)))


def key(b):
    if not b:
        return "NONE"
    y = b["y"] if b["y"] is not None else "NONE"; d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"


def run(img, on):
    g["RULE_SEPMIX"] = on
    c1, seen = g["pass1"](img)
    c2 = g["pass2"](img, list(c1)) if c1 else []
    if g["KO_LINE"]:
        c2 = g["keyword_line_reread"](img, c2, seen)
    return key(g["select_date"](c2)) if c2 else "NONE", sorted({key(c) for c in c2})


out = []
for kind, ids in (("changed", changed), ("sample", sample)):
    for n, iid in enumerate(ids):
        img = g["load_image"](f"images/{J[iid]}")
        off, c_off = run(img, False)
        on, c_on = run(img, True) if kind == "changed" else (off, c_off)
        b = base[iid]
        out.append(dict(kind=kind, image_id=iid, tags=b["tags"], label=b["label"], base=b["kol"], off=off, on=on, base_repro=(off == b["kol"]),
                        cands_off=";".join(c_off), cands_on=";".join(c_on)))
        print(kind, n + 1, len(ids), iid, flush=True)
with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
ch = [r for r in out if r["kind"] == "changed"]; sm = [r for r in out if r["kind"] == "sample"]
print(f"달라진 장 {len(ch)}: 끔이 기준선을 재현 {sum(r['base_repro'] for r in ch)} / 재현 안 됨 {sum(not r['base_repro'] for r in ch)}")
for r in ch:
    if not r["base_repro"]:
        print("   재현 안 됨:", r["image_id"], "기준", r["base"], "끔", r["off"], "켬", r["on"], "정답", r["label"])
print(f"안 바뀐 장 표본 {len(sm)}: 기준선 재현 {sum(r['base_repro'] for r in sm)}")
for r in sm:
    if not r["base_repro"]:
        print("   흔들림:", r["image_id"], "기준", r["base"], "끔", r["off"], "정답", r["label"])
print("done")
