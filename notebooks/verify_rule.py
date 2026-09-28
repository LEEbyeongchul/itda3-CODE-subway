"""규칙 실험 검증: 기준선(9/26 실행)과 답이 달라진 장을 같은 프로세스에서 규칙 끔/켬으로 다시 돌려, 변화가 규칙 때문인지(끔 = 기준선 재현) 확인한다.
플래그를 쉼표로 여럿 주면 전부 끔 · 하나씩만 켬 · 전부 켬을 돌려 어느 규칙 책임인지 가른다 (구성 qr 처럼 규칙을 묶어 잰 실험용).
답이 안 바뀐 장 가운데 무작위 표본을 끔으로 돌려 기준선 재현율(실행 간 흔들림)도 잰다.
  .venv/Scripts/python notebooks/verify_rule.py <EXP_TAG> <구성 열> <플래그[,플래그]> <출력 CSV> [표본 수]
  예: verify_rule.py 2026-09-27_qr qr RULE_SEPMIX,RULE_TAIL results/verify_qr_2026-09-27.csv 40"""
import csv, glob, json, os, random, sys
os.environ.setdefault("ITDA_THREADS", "8")
TAG, COL, FLAG, OUT = sys.argv[1:5]; NSAMPLE = int(sys.argv[5]) if len(sys.argv) > 5 else 40
FLAGS = FLAG.split(",")
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__verify__", "os": os}
for i in (1, 2, 3, 4, 5):
    exec(cells[i], g)
for f in FLAGS:   # '변수=값' 꼴(예: KO_LINE_MODE=auto)은 켤 때 그 값으로, 끌 때 노트북 기본값(env 반영)으로 둔다
    assert f.split("=")[0] in g, f
BASE0 = {f.split("=")[0]: g[f.split("=")[0]] for f in FLAGS if "=" in f}
base = {r["image_id"]: r for r in csv.DictReader(open("results/exp_rules4_2026-09-26_kolp1det_merged.csv", encoding="utf-8-sig"))}
J = {r["image_id"]: r["file"] for r in csv.DictReader(open("results/join_all3352_v6.csv", encoding="utf-8-sig"))}
rows = []
for f in sorted(glob.glob(f"results/exp_rules4_{TAG}_[0-9].csv")):
    rows += list(csv.DictReader(open(f, encoding="utf-8-sig")))
changed = [r["image_id"] for r in rows if r[COL] != base[r["image_id"]]["kol"]]
same = [r["image_id"] for r in rows if r[COL] == base[r["image_id"]]["kol"]]
random.seed(927)
sample = random.sample(same, min(NSAMPLE, len(same)))


def key(b):
    if not b:
        return "NONE"
    y = b["y"] if b["y"] is not None else "NONE"; d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"


def run(img, on):
    for f in FLAGS:
        if "=" in f:
            k, v = f.split("="); g[k] = v if f in on else BASE0[k]
        else:
            g[f] = f in on
    c1, seen = g["pass1"](img)
    c2 = g["pass2"](img, list(c1)) if c1 else []
    if g["KO_LINE"]:
        c2 = g["keyword_line_reread"](img, c2, seen)
    if g.get("RULE_REREAD"):
        c2 = g["broken_line_reread"](img, c2, seen)
    return key(g["select_date"](c2)) if c2 else "NONE"


out = []
for kind, ids in (("changed", changed), ("sample", sample)):
    for n, iid in enumerate(ids):
        img = g["load_image"](f"images/{J[iid]}")
        b = base[iid]
        rec = dict(kind=kind, image_id=iid, tags=b["tags"], label=b["label"], base=b["kol"], off=run(img, []))
        rec["base_repro"] = rec["off"] == b["kol"]
        if kind == "changed":
            for f in FLAGS:
                rec["on_" + f] = run(img, [f]) if len(FLAGS) > 1 else ""
            rec["on"] = run(img, FLAGS)
            rec["by"] = "+".join(f for f in FLAGS if len(FLAGS) > 1 and rec["on_" + f] != rec["off"]) or (FLAGS[0] if len(FLAGS) == 1 else "둘이 함께일 때만")
        else:
            for f in FLAGS:
                rec["on_" + f] = ""
            rec["on"] = rec["off"]; rec["by"] = ""
        out.append(rec)
        print(kind, n + 1, len(ids), iid, flush=True)
with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
ch = [r for r in out if r["kind"] == "changed"]; sm = [r for r in out if r["kind"] == "sample"]
print(f"달라진 장 {len(ch)}: 끔이 기준선을 재현 {sum(r['base_repro'] for r in ch)} / 재현 안 됨 {sum(not r['base_repro'] for r in ch)}")
for r in ch:
    tag = "회복" if r["on"] == r["label"] else ("퇴보" if r["off"] == r["label"] else "오답→오답")
    grp = "병기" if "2" in (r["tags"] or "") else "비병기"
    print("   ", tag, grp, r["image_id"], "정답", r["label"], "끔", r["off"], "켬", r["on"], "책임", r["by"], "" if r["base_repro"] else "← 기준선 재현 안 됨")
print(f"안 바뀐 장 표본 {len(sm)}: 기준선 재현 {sum(r['base_repro'] for r in sm)}")
for r in sm:
    if not r["base_repro"]:
        print("   흔들림:", r["image_id"], "기준", r["base"], "끔", r["off"], "정답", r["label"])
print("done")
