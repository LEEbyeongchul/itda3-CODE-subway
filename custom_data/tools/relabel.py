# -*- coding: utf-8 -*-
"""오답 재라벨 점검 도구 (tkinter). 파이프라인이 틀린 사진을 전부 띄워 **정답 라벨 자체가 틀렸는지** 사람이 다시 본다.

    python notebooks/relabel.py --name 서현
    python notebooks/relabel.py --summary          # 창 없이 지금까지 집계만
    python notebooks/relabel.py --name 서현 --control 100   # 대조군: 예측이 라벨과 같았던 사진 100장 무작위

사진 위에 현재 라벨과 예측이 표시된다.
    (빈칸) Enter          라벨이 맞음 → 그냥 넘김 (기록만 남음)
    2027.07.02 Enter      라벨이 틀림 → 포장에 찍힌 그대로 다시 입력 (형식·태그 규칙은 label.py 와 동일)
    s / m / NONE          판독 불가 / 제조일자만 있음 / 날짜 없음 → NONE 으로 고침
태그를 안 치면 원래 태그를 물려받는다 (s·m 제외). 고친 줄에는 태그 l(라벨 수정)이 붙는다.

고친 값은 labels/labels_block<N>.csv 의 그 줄에 바로 덮어쓰고, 판정은 labels/relabel_review.csv 에 한 줄씩 쌓인다.
오답만 보면 라벨이 예측 쪽으로만 고쳐지므로, 정답 처리된 사진도 --control 로 같은 눈으로 본다 (기록 labels/relabel_control.csv).
중간에 꺼도 이어서 된다. 대상은 예측 CSV 에 있는 사진만 (봉인 500장·블록 17 은 예측이 없어 빠진다).

단축키: Enter 저장·다음 | 휠 확대·축소 | 드래그 이동 | F1 회전 | F2 확대 초기화 | Ctrl+Z 직전 취소 | Esc 종료
"""
import os, re, ast, csv, sys, glob, random, argparse, datetime, collections
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageOps, ImageTk

ap = argparse.ArgumentParser()
ap.add_argument("--name", default="", help="검수자 이름 (기록용)")
ap.add_argument("--pred", default="results/exp_rules4_2026-09-26_kolp1det_merged.csv", help="image_id·label·예측 열이 있는 CSV")
ap.add_argument("--col", default="kol", help="예측 열 이름 (kol = 현 기본값 p1det)")
ap.add_argument("--labels", default="labels/labels_block*.csv")
ap.add_argument("--control", type=int, default=0, help="대조군: 예측이 라벨과 같은 사진에서 N장 무작위 점검")
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--log", default="", help="기본 labels/relabel_review.csv, 대조군은 labels/relabel_control.csv")
ap.add_argument("--images", default="images")
ap.add_argument("--summary", action="store_true")
args = ap.parse_args()
args.log = args.log or ("labels/relabel_control.csv" if args.control else "labels/relabel_review.csv")
if not args.summary and not args.name:
    sys.exit("--name 이 필요합니다.")

LOG_FIELDS = ["image_id", "block", "원라벨러", "원라벨", "원raw", "원tags", "예측", "판정", "새라벨", "새raw", "새tags", "검수자", "ts", "비고"]
LABEL_KEYS = ["raw", "year", "month", "day", "final_date", "format", "tags"]
MAX_W, MAX_H = 1100, 820


def load_label_rules():
    """label.py 의 입력 해석 규칙(normalize·split_input)만 가져온다. label.py 는 실행형이라 import 하면 창이 뜬다."""
    want = {"TAGS", "MONTHS", "_MON_RE", "normalize", "split_input"}
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "label.py"), encoding="utf-8").read()
    body = [n for n in ast.parse(src).body
            if (isinstance(n, ast.FunctionDef) and n.name in want)
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) in want)]
    ns = {"re": re}
    exec(compile(ast.Module(body=body, type_ignores=[]), "label.py", "exec"), ns)
    ns["TAGS"] |= set("ml")                  # m 제조일자만(9/12 추가) · l 라벨 수정
    return ns["normalize"], ns["split_input"]


normalize, split_input = load_label_rules()

# ---------- 데이터 ----------
where = {}                                   # image_id(6자리) → (라벨 파일, 파일 안의 image_id)
label_fields = {}
for p in glob.glob(args.labels):
    with open(p, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f); label_fields[p] = rd.fieldnames
        for r in rd:
            where[r["image_id"].zfill(6)] = (p, r["image_id"])


def read_label(iid):
    p, raw_id = where[iid]
    with open(p, encoding="utf-8", newline="") as f:
        return next(r for r in csv.DictReader(f) if r["image_id"] == raw_id)


def write_label(iid, vals):
    p, raw_id = where[iid]
    with open(p, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if r["image_id"] == raw_id:
            r.update(vals)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=label_fields[p]); w.writeheader(); w.writerows(rows)


def read_log():
    if not os.path.exists(args.log):
        return []
    with open(args.log, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_log(rows):
    with open(args.log, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS); w.writeheader(); w.writerows(rows)


with open(args.pred, encoding="utf-8-sig") as f:
    preds = [r for r in csv.DictReader(f)]
wrong = sorted((r for r in preds if r[args.col] != r["label"] and r["image_id"].zfill(6) in where), key=lambda r: r["image_id"].zfill(6))
n_wrong = len(wrong)
if args.control:                             # 대조군: 점검 대상을 정답 처리분의 무작위 표본으로 바꾼다
    pool = sorted((r for r in preds if r[args.col] == r["label"] and r["image_id"].zfill(6) in where), key=lambda r: r["image_id"].zfill(6))
    wrong = sorted(random.Random(args.seed).sample(pool, min(args.control, len(pool))), key=lambda r: r["image_id"].zfill(6))
pred_of = {r["image_id"].zfill(6): r[args.col] for r in wrong}
log = read_log()
done = {r["image_id"] for r in log}
queue = [r["image_id"].zfill(6) for r in wrong if r["image_id"].zfill(6) not in done]


def summary():
    seen = [r for r in log if r["image_id"] in pred_of]
    fixed = [r for r in seen if r["판정"] == "수정"]
    hit = [r for r in fixed if r["새라벨"] == r["예측"]]
    n, k = len(preds), len(preds) - n_wrong
    if args.control:
        lines = [f"대조군 (예측 = 라벨 {k}장 중 무작위 {len(wrong)}장, seed {args.seed})",
                 f"검수 {len(seen)}/{len(wrong)}장 · 라벨 맞음 {len(seen) - len(fixed)} · 라벨 수정 {len(fixed)}"]
        if seen:
            lines.append(f"정답 처리분의 라벨 오류 비율 {len(fixed) / len(seen):.1%} → 전체 {k}장이면 약 {k * len(fixed) / len(seen):.0f}장이 정답에서 빠진다")
        return "\n".join(lines)
    lines = [f"예측 {args.pred} [{args.col}]: {n}장 중 오답 {len(wrong)}장 (완전일치 {k / n:.1%})",
             f"검수 {len(seen)}/{len(wrong)}장 · 라벨 맞음 {len(seen) - len(fixed)} · 라벨 수정 {len(fixed)}"]
    if seen:
        lines.append(f"오답 중 라벨 오류 비율 {len(fixed) / len(seen):.1%} · 수정 후 예측과 일치 {len(hit)}장"
                     f" → 검수분 반영 완전일치 {(k + len(hit)) / n:.1%}")
        by = collections.Counter(r["원라벨러"] for r in fixed)
        if by:
            lines.append("수정 라벨러별: " + ", ".join(f"{a} {b}" for a, b in by.most_common()))
    return "\n".join(lines)


print(summary())
if args.summary:
    sys.exit()
if not queue:
    sys.exit("남은 항목이 없습니다.")

# ---------- UI ----------
root = tk.Tk(); root.title(f"재라벨 점검 — {args.name}")
big = tkfont.Font(size=13)
MAX_W = min(MAX_W, root.winfo_screenwidth() - 80); MAX_H = min(MAX_H, root.winfo_screenheight() - 260)
entry = tk.Entry(root, font=tkfont.Font(size=16)); entry.pack(fill="x", padx=8, pady=(8, 2))
status = tk.Label(root, anchor="w", font=big, fg="#444"); status.pack(fill="x", padx=8)
info = tk.Label(root, anchor="w", font=big, fg="#06c"); info.pack(fill="x", padx=8)
hint = tk.Label(root, anchor="w", fg="#888",
                text="맞으면 빈칸 Enter · 틀리면 보이는 그대로 다시 입력 (s 판독불가 · m 제조일자만 · NONE)   |   휠 확대  드래그 이동  F1 회전  F2 원래 크기  Ctrl+Z 취소  Esc 종료")
hint.pack(fill="x", padx=8, pady=(0, 4))
canvas = tk.Canvas(root, width=MAX_W, height=MAX_H, bg="#222"); canvas.pack()
entry.focus_set()
state = {"k": 0, "rot": 0, "photo": None, "img": None, "zoom": 1.0, "cx": 0, "cy": 0, "drag": None, "last": "", "undo": []}


def image_path(file):
    for d in (args.images, "custom_photos"):
        if os.path.exists(os.path.join(d, file)):
            return os.path.join(d, file)
    return os.path.join(args.images, file)


def scale():
    w, h = state["img"].size
    return min(MAX_W / w, MAX_H / h) * state["zoom"]


def render():
    im, s = state["img"], scale()
    vw, vh = MAX_W / s, MAX_H / s                      # 화면에 들어오는 원본 영역
    w, h = im.size
    state["cx"] = w / 2 if vw >= w else min(max(state["cx"], vw / 2), w - vw / 2)
    state["cy"] = h / 2 if vh >= h else min(max(state["cy"], vh / 2), h - vh / 2)
    box = [round(v) for v in (state["cx"] - vw / 2, state["cy"] - vh / 2, state["cx"] + vw / 2, state["cy"] + vh / 2)]
    view = im.crop(box).resize((MAX_W, MAX_H), Image.BILINEAR, reducing_gap=2.0)
    state["photo"] = ImageTk.PhotoImage(view)
    canvas.delete("all"); canvas.create_image(0, 0, anchor="nw", image=state["photo"])


def show():
    if state["k"] >= len(queue):
        canvas.delete("all")
        canvas.create_text(MAX_W // 2, MAX_H // 2, text="점검 완료! 수고하셨습니다.\n\n" + summary(), fill="white", font=big, justify="center")
        status.config(text="끝", fg="#444"); info.config(text=""); entry.config(state="disabled"); return
    iid = queue[state["k"]]
    r = read_label(iid)
    with Image.open(image_path(r["file"])) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
    if state["rot"]:
        im = im.rotate(state["rot"], expand=True)
    state["img"] = im; state["zoom"] = 1.0; state["cx"], state["cy"] = im.size[0] / 2, im.size[1] / 2
    render()
    status.config(text=f"[{len(wrong) - len(queue) + state['k'] + 1}/{len(wrong)}]  {r['file']}  (블록 {r['block']}, {r['labeler']})     {state['last']}", fg="#444")
    info.config(text=f"라벨 {r['final_date']}   |   예측 {pred_of[iid]}   |   라벨 원문 '{r['raw']}'   |   태그 {r['tags'] or '-'}")


def submit(_=None):
    global log
    iid = queue[state["k"]]
    old = read_label(iid)
    text = entry.get().strip()
    row = {"image_id": iid, "block": old["block"], "원라벨러": old["labeler"], "원라벨": old["final_date"], "원raw": old["raw"],
           "원tags": old["tags"], "예측": pred_of[iid], "판정": "맞음", "새라벨": "", "새raw": "", "새tags": "",
           "검수자": args.name, "ts": datetime.datetime.now().isoformat(timespec="seconds")}
    new = None
    if text:
        try:
            date_str, tags = split_input(text)
            if not tags:
                tags = set(old["tags"]) - set("sml")
            y, m, d, fmt = normalize(date_str, tags)
        except ValueError as e:
            status.config(text=f"⚠ {e}", fg="#c00"); return
        ys = f"{y:04d}" if y is not None else "NONE"
        ms = f"{m:02d}" if m is not None else "NONE"
        ds = f"{d:02d}" if d is not None else "NONE"
        fd = "NONE" if fmt == "none" else f"{ys}-{ms}-{ds}"
        if fmt == "none":
            tags &= set("sm")
        if fd != old["final_date"]:
            new = {"raw": text, "year": ys, "month": ms, "day": ds, "final_date": fd, "format": fmt, "tags": "".join(sorted(tags | {"l"}))}
    if new:
        write_label(iid, new)
        row.update({"판정": "수정", "새라벨": new["final_date"], "새raw": new["raw"], "새tags": new["tags"]})
        state["last"] = f"수정: {iid} {old['final_date']} → {new['final_date']} [{new['format']}] {new['tags']}"
    else:
        state["last"] = f"맞음: {iid} {old['final_date']}" + ("  (입력이 라벨과 같음)" if text else "")
    log.append(row); write_log(log)
    state["undo"].append((iid, {k: old[k] for k in LABEL_KEYS} if new else None, text))
    state["k"] += 1; state["rot"] = 0; entry.delete(0, "end"); show()


def undo(_=None):
    if not state["undo"]:
        status.config(text="취소할 것이 없습니다 (이번에 창을 띄운 뒤 저장한 것만 취소됩니다)", fg="#c00"); return
    iid, old_vals, text = state["undo"].pop()
    if old_vals:
        write_label(iid, old_vals)
    log[:] = [r for r in log if r["image_id"] != iid]; write_log(log)
    state["k"] -= 1; state["rot"] = 0; state["last"] = f"취소: {iid}"
    entry.config(state="normal"); entry.delete(0, "end"); entry.insert(0, text); show()


def rotate(_=None):
    if state["k"] < len(queue):
        state["rot"] = (state["rot"] + 90) % 360; show()


def zoom(e):
    if state["k"] >= len(queue):
        return
    s0 = scale()
    px, py = state["cx"] + (e.x - MAX_W / 2) / s0, state["cy"] + (e.y - MAX_H / 2) / s0     # 커서 아래의 원본 좌표
    state["zoom"] = min(max(state["zoom"] * (1.25 if e.delta > 0 else 0.8), 1.0), 16.0)
    s1 = scale()
    state["cx"], state["cy"] = px - (e.x - MAX_W / 2) / s1, py - (e.y - MAX_H / 2) / s1     # 커서 아래 점을 고정
    render()


def drag_start(e):
    state["drag"] = (e.x, e.y)


def drag_move(e):
    if state["drag"] is None or state["k"] >= len(queue):
        return
    s = scale()
    state["cx"] -= (e.x - state["drag"][0]) / s; state["cy"] -= (e.y - state["drag"][1]) / s
    state["drag"] = (e.x, e.y); render()


def zoom_reset(_=None):
    if state["k"] < len(queue):
        state["zoom"] = 1.0; render()


entry.bind("<Return>", submit); root.bind("<F1>", rotate); root.bind("<F2>", zoom_reset); root.bind("<Control-z>", undo)
if sys.platform == "darwin": root.bind("<Command-z>", undo)
canvas.bind("<MouseWheel>", zoom); canvas.bind("<ButtonPress-1>", drag_start); canvas.bind("<B1-Motion>", drag_move)
root.bind("<Escape>", lambda e: root.destroy())
show(); root.mainloop()
