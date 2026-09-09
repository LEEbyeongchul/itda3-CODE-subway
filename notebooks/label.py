# -*- coding: utf-8 -*-
"""소비기한 라벨링 도구 (tkinter, 추가 설치 없음).

    python notebooks/label.py --block 1 --name 홍길동

labels/sample.csv 에서 내 블록의 이미지를 차례로 띄운다. 입력창에 **포장에 찍힌 그대로** 날짜를 치고 Enter.
저장은 labels/labels_block<N>.csv 에 한 줄씩 즉시 기록되므로 중간에 꺼도 이어서 할 수 있다.

입력 예시 (날짜는 보이는 그대로, 뒤에 태그를 공백으로):
    2027.06.26            → 2027-06-26
    25.06.26 2            → 2025-06-26, 태그 2(날짜 두 개 병기, 소비기한만 적은 것)
    20/05/2026            → 2026-05-20 (연도가 뒤면 자동으로 일/월/년)
    050926 d              → 2026-09-05 (d = 일이 먼저: DDMMYY)
    30 12 23 d e          → 2023-12-30, 각인
    06.26  또는 NONE.06.26 → NONE-06-26 (연도 없음)
    2027.7 또는 27.11     → 2027-07-NONE / 2027-11-NONE (일 없음)
    12.2020               → 2020-12-NONE (유럽식 월.연도, 일 없음)
    NOV 29 2021           → 2021-11-29 (영문 월 이름. BBE/EXP 같은 앞말은 빼고)
    NONE                  → 날짜 없음
    s                     → 사람도 못 읽음 (NONE 으로 저장, 태그 s)

태그 (한 글자, 여러 개 가능):
    2  날짜 2개 이상 병기 (제조·소비 등) — 소비기한만 적을 것
    d  일-월-년 순서 (유럽식). 2자리·6자리 입력에서만 의미 있음
    r  라벨/글자가 90도 누움
    t  글자가 너무 작음 · 저해상도
    b  흐림 · 초점 안 맞음
    e  각인 · 양각 (잉크 아님)
    n  키워드(소비기한/유통기한/까지/BBD) 없음
    s  판독 불가
    ?  애매함 — 나중에 같이 검토

단축키:  Enter 저장·다음 | F1 화면 90도 회전 | Ctrl+Z 직전 것 취소 | Esc 종료
"""
import os, re, csv, sys, argparse, datetime
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageOps, ImageTk

ap = argparse.ArgumentParser()
ap.add_argument("--block", type=int, required=True)
ap.add_argument("--name", required=True, help="라벨러 이름 (기록용)")
ap.add_argument("--images", default="images")
ap.add_argument("--sample", default="labels/sample.csv")
args = ap.parse_args()

OUT = f"labels/labels_block{args.block}.csv"
FIELDS = ["block", "labeler", "image_id", "file", "raw", "year", "month", "day", "final_date", "format", "tags", "ts"]
TAGS = set("2drtbens?")
MONTHS = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8, "SEP": 9, "SEPT": 9, "OCT": 10, "NOV": 11, "DEC": 12}
_MON_RE = re.compile(r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEPT|SEP|OCT|NOV|DEC)[A-Z]*")
MAX_W, MAX_H = 1100, 820

# ---------- 데이터 ----------
with open(args.sample, encoding="utf-8") as f:
    todo = [r for r in csv.DictReader(f) if int(r["block"]) == args.block]
done = set()
if os.path.exists(OUT):
    with open(OUT, encoding="utf-8") as f:
        done = {r["file"] for r in csv.DictReader(f)}
queue = [r for r in todo if r["file"] not in done]
if not todo:
    sys.exit(f"블록 {args.block} 에 배정된 이미지가 없습니다. sample.csv 를 확인하세요.")
print(f"블록 {args.block}: 전체 {len(todo)}장, 완료 {len(done)}장, 남은 {len(queue)}장 → {OUT}")


def normalize(raw, tags):
    """사람이 친 문자열 → (y, m, d, format). y 는 None 허용. 잘못되면 ValueError."""
    s = raw.strip().upper()
    if s in ("", "NONE", "N", "X") or "s" in tags:
        return None, None, None, "none"
    nums = re.findall(r"\d+", s)
    day_first = "d" in tags
    mm = _MON_RE.search(s)
    if mm:                                   # 'NOV 29 2021' / '29 NOV 21' / 'NOV 2021' — 영문 월 이름
        m = MONTHS[mm.group(1)]
        num_matches = list(re.finditer(r"\d+", s))
        n4 = [nm for nm in num_matches if len(nm.group()) == 4]
        n2 = [nm for nm in num_matches if len(nm.group()) <= 2]
        day_tok = year_tok = None
        if n4:
            year_tok = n4[0]
            y = int(year_tok.group())
            if n2:
                day_tok = n2[0]
                d = int(day_tok.group())
            else:
                d = None
        elif len(n2) >= 2:
            year_tok = n2[-1]
            y = 2000 + int(year_tok.group())
            day_tok = n2[0]
            d = int(day_tok.group())
        elif len(n2) == 1:
            day_tok = n2[0]
            y, d = None, int(day_tok.group())  # 'NOV 21' 은 일로 해석. 연도였다면 '?' 태그로
        else:
            y, d = None, None
        # 실제 토큰 순서대로 포맷 라벨을 구성 (예: '26 MAR 2021' → DD MON YYYY, 'NOV 29 2021' → MON DD YYYY)
        parts = [(mm.start(), "MON")]
        if day_tok is not None:
            parts.append((day_tok.start(), "DD"))
        if year_tok is not None:
            parts.append((year_tok.start(), "YYYY" if len(year_tok.group()) == 4 else "YY"))
        fmt = " ".join(label for _, label in sorted(parts))
        if y is not None and not (2015 <= y <= 2035):
            raise ValueError(f"연도 {y} 가 범위 밖")
        if d is not None and not (1 <= d <= 31):
            raise ValueError(f"일 {d} 이 범위 밖")
        return y, m, d, fmt
    if len(nums) == 1:
        t = nums[0]
        if len(t) == 8:
            y, m, d, fmt = int(t[:4]), int(t[4:6]), int(t[6:]), "YYYYMMDD"
        elif len(t) == 6:
            if day_first:
                y, m, d, fmt = 2000 + int(t[4:]), int(t[2:4]), int(t[:2]), "DDMMYY"
            else:
                y, m, d, fmt = 2000 + int(t[:2]), int(t[2:4]), int(t[4:]), "YYMMDD"
        elif len(t) == 4:
            y, m, d, fmt = None, int(t[:2]), int(t[2:]), "MMDD"
        else:
            raise ValueError(f"숫자 덩어리 길이 {len(t)} 는 해석 불가")
    elif len(nums) == 2:
        a, b = nums
        if len(a) == 4:                      # '2027.7' → 연·월만, 일 없음 → 2027-07-NONE (일본 賞味期限 등)
            y, m, d, fmt = int(a), int(b), None, "YYYY.MM"
        elif len(b) == 4:                    # '12.2020' → 유럽식 월.연도, 일 없음 → 2020-12-NONE
            y, m, d, fmt = int(b), int(a), None, "MM.YYYY"
        elif 15 <= int(a) <= 35 and int(b) <= 12:   # '25.11' → 2025-11-NONE (연도 15~35 와 월 1~12 는 안 겹침)
            y, m, d, fmt = 2000 + int(a), int(b), None, "YY.MM"
        else:                                # '10.14' → 연도 없음 → NONE-10-14. 유럽식 MM/YY(11/25)는 '2025.11' 로 풀어 칠 것
            y, m, d, fmt = None, int(a), int(b), "MM.DD"
    else:
        a, b, c = nums[:3]
        if len(a) == 4:
            y, m, d, fmt = int(a), int(b), int(c), "YYYY.MM.DD"
        elif len(c) == 4:
            if not (1 <= int(b) <= 12) and 1 <= int(a) <= 12:  # '4.13.2026' → b(13)는 월일 수 없음 → 미국식 MM.DD.YYYY
                y, m, d, fmt = int(c), int(a), int(b), "MM.DD.YYYY"
            else:
                y, m, d, fmt = int(c), int(b), int(a), "DD.MM.YYYY"
        elif day_first:
            y, m, d, fmt = 2000 + int(c), int(b), int(a), "DD.MM.YY"
        else:
            y, m, d, fmt = 2000 + int(a), int(b), int(c), "YY.MM.DD"
    if y is not None and not (2015 <= y <= 2035):
        raise ValueError(f"연도 {y} 가 범위 밖 — d 태그(일이 먼저)가 필요한가요?")
    if not (1 <= m <= 12):
        raise ValueError(f"월 {m} 이 범위 밖")
    if d is not None and not (1 <= d <= 31):
        raise ValueError(f"일 {d} 이 범위 밖")
    return y, m, d, fmt


def split_input(text):
    toks = text.strip().split()
    date_toks, tags = [], set()
    for t in toks:
        # 태그 판정을 먼저. '2' 는 태그지만 '22'·'12' 같은 두 자리 이상 순수 숫자는 날짜 조각('30 12 22')
        if set(t) <= TAGS and not re.fullmatch(r"\d{2,}", t):
            tags |= set(t)
        elif re.search(r"\d", t) or t.upper() in ("NONE", "N", "X") or _MON_RE.fullmatch(t.upper()):
            date_toks.append(t)
        else:
            raise ValueError(f"알 수 없는 토큰 '{t}'")
    return " ".join(date_toks), tags


def append_row(row):
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            wr.writeheader()
        wr.writerow(row)


def pop_last_row():
    with open(OUT, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    last = rows.pop()
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS)
        wr.writeheader()
        wr.writerows(rows)
    return last


# ---------- UI ----------
root = tk.Tk()
root.title(f"라벨링 — 블록 {args.block} · {args.name}")
big = tkfont.Font(size=13)
# 화면 크기에 맞춰 사진 영역을 정한다 (입력칸이 화면 밖으로 잘리지 않도록). 입력부는 사진 **위**에 둔다.
MAX_W = min(MAX_W, root.winfo_screenwidth() - 80)
MAX_H = min(MAX_H, root.winfo_screenheight() - 240)
entry = tk.Entry(root, font=tkfont.Font(size=16))
entry.pack(fill="x", padx=8, pady=(8, 2))
status = tk.Label(root, anchor="w", font=big, fg="#444")
status.pack(fill="x", padx=8)
hint = tk.Label(root, anchor="w", fg="#888",
                text="보이는 그대로 입력 + 태그   2 병기 · d 일먼저 · r 회전 · t 작음 · b 흐림 · e 각인 · n 키워드없음 · s 판독불가 · ? 애매   |   F1 회전  Ctrl+Z 취소  Esc 종료")
hint.pack(fill="x", padx=8, pady=(0, 4))
canvas = tk.Canvas(root, width=MAX_W, height=MAX_H, bg="#222")
canvas.pack()
entry.focus_set()

state = {"i": 0, "rot": 0, "photo": None, "last": ""}


def show():
    if state["i"] >= len(queue):
        canvas.delete("all")
        canvas.create_text(MAX_W // 2, MAX_H // 2, text=f"블록 {args.block} 완료! 수고하셨습니다.\n{OUT} 를 커밋해 주세요.", fill="white", font=big, justify="center")
        status.config(text="끝")
        entry.config(state="disabled")
        return
    r = queue[state["i"]]
    p = os.path.join(args.images, r["file"])
    with Image.open(p) as im:
        if im.format in ("JPEG", "MPO"):
            im.draft("RGB", (MAX_W, MAX_H))
        im = ImageOps.exif_transpose(im).convert("RGB")
        if state["rot"]:
            im = im.rotate(state["rot"], expand=True)
        im.thumbnail((MAX_W, MAX_H))
        state["photo"] = ImageTk.PhotoImage(im)
    canvas.delete("all")
    canvas.create_image(MAX_W // 2, MAX_H // 2, image=state["photo"])
    n_done = len(done) + state["i"]
    status.config(text=f"[{n_done + 1}/{len(todo)}]  {r['file']}  ({r['stratum']}, {r['w']}x{r['h']})     {state['last']}")


def submit(_=None):
    text = entry.get()
    r = queue[state["i"]]
    try:
        date_str, tags = split_input(text)
        y, m, d, fmt = normalize(date_str, tags)
    except ValueError as e:
        status.config(text=f"⚠ {e}", fg="#c00")
        return
    ys = f"{y:04d}" if y is not None else "NONE"
    ms = f"{m:02d}" if m is not None else "NONE"
    ds = f"{d:02d}" if d is not None else "NONE"
    fd = "NONE" if (y is None and m is None and d is None) else f"{ys}-{ms}-{ds}"
    append_row({"block": args.block, "labeler": args.name, "image_id": r["image_id"], "file": r["file"],
                "raw": text.strip(), "year": ys, "month": ms, "day": ds, "final_date": fd, "format": fmt,
                "tags": "".join(sorted(tags)), "ts": datetime.datetime.now().isoformat(timespec="seconds")})
    state["last"] = f"저장: {r['image_id']} → {fd} [{fmt}] {''.join(sorted(tags))}"
    state["i"] += 1
    state["rot"] = 0
    entry.delete(0, "end")
    status.config(fg="#444")
    show()


def undo(_=None):
    if state["i"] == 0:
        status.config(text="취소할 것이 없습니다", fg="#c00")
        return
    last = pop_last_row()
    state["i"] -= 1
    state["rot"] = 0
    entry.delete(0, "end")
    if last:
        entry.insert(0, last["raw"])
    state["last"] = f"취소: {last['image_id'] if last else ''}"
    show()


def rotate(_=None):
    state["rot"] = (state["rot"] + 90) % 360
    show()


entry.bind("<Return>", submit)
root.bind("<F1>", rotate)
root.bind("<Control-z>", undo)
if sys.platform == "darwin":
    root.bind("<Command-z>", undo)  # 맥은 Cmd+Z 로 undo 하는 습관이 있어 Ctrl+Z 와 같이 지원
root.bind("<Escape>", lambda e: root.destroy())
show()
root.mainloop()
