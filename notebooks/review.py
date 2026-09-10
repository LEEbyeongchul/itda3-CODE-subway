# -*- coding: utf-8 -*-
"""오답 원인 태깅 도구 (tkinter). 파이프라인이 틀린 이미지를 눈으로 보고 왜 틀렸는지 코드 한 글자로 기록한다.

    python notebooks/review.py --who A --name 서현        # labels/review_v3.csv 의 담당=A 행

사진 위에 정답·예측이 표시된다. 입력칸에 원인 코드 한 글자 (+ 공백 + 메모) 치고 Enter.
    u  사람 눈에도 안 보임 (저화질·흐림·가림)
    r  보이는데 OCR 이 잘못 읽음
    s  날짜는 읽혔는데 엉뚱한 숫자를 골랐음 (품목보고번호·로트)
    p  제조·소비 병기에서 잘못 고름
    f  형식을 파서가 모름 (처음 보는 표기)
    l  라벨이 틀림 — 메모에 진짜 정답을 적을 것 (예: l 2026.03.12)
    o  기타 — 메모 한 줄
단축키: Enter 저장·다음 | F1 회전 | Ctrl+Z 직전 취소 | Esc 종료 (중간에 꺼도 이어서 됨)
"""
import os, csv, sys, argparse
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageOps, ImageTk, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument("--who", required=True, help="담당 열 값 (A/B)")
ap.add_argument("--name", required=True)
ap.add_argument("--csv", default="labels/review_v3.csv")
ap.add_argument("--images", default="images")
args = ap.parse_args()

CODES = {"u": "안 보임", "r": "오독", "s": "엉뚱한 숫자", "p": "병기 오선택", "f": "형식 미지원", "l": "라벨 오류", "o": "기타"}
MAX_W, MAX_H = 1100, 820

rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
FIELDS = list(rows[0].keys())
mine = [i for i, r in enumerate(rows) if r["담당"] == args.who]
queue = [i for i in mine if not rows[i]["원인"]]
print(f"담당 {args.who}: 전체 {len(mine)}장, 완료 {len(mine) - len(queue)}장, 남은 {len(queue)}장")
if not queue:
    sys.exit("남은 항목이 없습니다.")


def save():
    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)


root = tk.Tk(); root.title(f"오답 검토 — {args.who} · {args.name}")
big = tkfont.Font(size=13)
MAX_W = min(MAX_W, root.winfo_screenwidth() - 80); MAX_H = min(MAX_H, root.winfo_screenheight() - 260)
entry = tk.Entry(root, font=tkfont.Font(size=16)); entry.pack(fill="x", padx=8, pady=(8, 2))
status = tk.Label(root, anchor="w", font=big, fg="#444"); status.pack(fill="x", padx=8)
info = tk.Label(root, anchor="w", font=big, fg="#06c"); info.pack(fill="x", padx=8)
hint = tk.Label(root, anchor="w", fg="#888", text="  ".join(f"{k} {v}" for k, v in CODES.items()) + "   |   Enter 저장  F1 회전  Ctrl+Z 취소  Esc 종료")
hint.pack(fill="x", padx=8, pady=(0, 4))
canvas = tk.Canvas(root, width=MAX_W, height=MAX_H, bg="#222"); canvas.pack()
entry.focus_set()
state = {"k": 0, "rot": 0, "photo": None, "done": []}


def show():
    if state["k"] >= len(queue):
        canvas.delete("all"); canvas.create_text(MAX_W // 2, MAX_H // 2, text=f"담당 {args.who} 완료! {args.csv} 를 커밋해 주세요.", fill="white", font=big)
        entry.config(state="disabled"); return
    r = rows[queue[state["k"]]]
    with Image.open(os.path.join(args.images, r["file"])) as im:
        if im.format in ("JPEG", "MPO"): im.draft("RGB", (MAX_W, MAX_H))
        im = ImageOps.exif_transpose(im).convert("RGB")
        if state["rot"]: im = im.rotate(state["rot"], expand=True)
        im.thumbnail((MAX_W, MAX_H))
        state["photo"] = ImageTk.PhotoImage(im)
    canvas.delete("all"); canvas.create_image(MAX_W // 2, MAX_H // 2, image=state["photo"])
    status.config(text=f"[{len(mine) - len(queue) + state['k'] + 1}/{len(mine)}]  {r['file']}  ({r['stratum']})", fg="#444")
    info.config(text=f"정답 {r['정답']}   |   예측 {r['예측']}   |   라벨 원문 '{r['raw']}'   |   후보 {r['후보'][:60]}")


def submit(_=None):
    t = entry.get().strip()
    if not t or t[0].lower() not in CODES:
        status.config(text="⚠ 원인 코드 한 글자 (u r s p f l o) 로 시작해야 합니다", fg="#c00"); return
    r = rows[queue[state["k"]]]
    r["원인"] = t[0].lower(); r["메모"] = t[1:].strip()
    save(); state["done"].append(queue[state["k"]]); state["k"] += 1; state["rot"] = 0; entry.delete(0, "end"); show()


def undo(_=None):
    if not state["done"]: return
    idx = state["done"].pop(); state["k"] -= 1
    entry.delete(0, "end"); entry.insert(0, (rows[idx]["원인"] + " " + rows[idx]["메모"]).strip())
    rows[idx]["원인"] = ""; rows[idx]["메모"] = ""; save(); state["rot"] = 0; show()


def rotate(_=None):
    state["rot"] = (state["rot"] + 90) % 360; show()


entry.bind("<Return>", submit); root.bind("<F1>", rotate); root.bind("<Control-z>", undo)
if sys.platform == "darwin": root.bind("<Command-z>", undo)
root.bind("<Escape>", lambda e: root.destroy())
show(); root.mainloop()
