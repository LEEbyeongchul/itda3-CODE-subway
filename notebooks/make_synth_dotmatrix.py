"""도트매트릭스(잉크젯) 날짜 합성 데이터 생성기 — 인식기 파인튜닝용 (계획서 2.4).

    python notebooks/make_synth_dotmatrix.py --n 3000 --out data/rec_synth
    → data/rec_synth/imgs/*.jpg, data/rec_synth/synth_list.txt (imgs/xxx.jpg<TAB>라벨), sheet_01.jpg (미리보기)

왜: 미검출 이미지를 직접 본 결과 대부분이 도트매트릭스 인쇄·각인. 사전학습 인식기는 점으로 찍힌 글자를 본 적이 없다.
어떻게: 5×7 점 격자 비트맵 폰트로 날짜를 그린다. 배경은 실제 포장 사진의 무작위 조각을 강하게 블러해(글자 제거) 쓴다.
         점 크기·간격·기울기·색(어두운 잉크/밝은 잉크)·블러·노이즈를 무작위로 섞고, 20% 는 일반 TTF 폰트로 그려 분포를 넓힌다.
라벨 형식 분포는 실측 라벨(YYYY.MM.DD 67%, YY.MM.DD 11%, DD.MM.YYYY 10%, 연월만 3%, 영문 월 3% …)을 따른다.
학습에 넣을 때: train_list 에 synth_list.txt 를 이어 붙인다 (Colab 노트북 2절에서 zip 에 같이 넣으면 됨).
"""
import argparse, glob, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 5x7 비트맵 폰트 (각 글자 7행, 각 행 5비트 문자열)
FONT57 = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    " ": ["00000"] * 7,
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11100", "10010", "10001", "10001", "10001", "10010", "11100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "10001", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
}
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def rand_date():
    y = random.randint(2019, 2029); m = random.randint(1, 12); d = random.randint(1, 28)
    r = random.random()
    sep = random.choice([".", ".", ".", "/", "-", " "])
    if r < 0.60:   fmt = f"{y}{sep}{m:02d}{sep}{d:02d}"                 # YYYY.MM.DD
    elif r < 0.72: fmt = f"{y%100:02d}{sep}{m:02d}{sep}{d:02d}"          # YY.MM.DD
    elif r < 0.82: fmt = f"{d:02d}{sep}{m:02d}{sep}{y}"                  # DD.MM.YYYY
    elif r < 0.86: fmt = f"{y}{sep}{m:02d}"                              # YYYY.MM
    elif r < 0.89: fmt = f"{m:02d}{sep}{y}"                              # MM.YYYY
    elif r < 0.92: fmt = f"{y}{m:02d}{d:02d}"                            # YYYYMMDD
    elif r < 0.97:                                                       # 영문 월
        mon = MONTHS[m - 1]
        fmt = random.choice([f"{d:02d} {mon} {y}", f"{mon} {d:02d} {y}", f"{d:02d}-{mon}-{y%100:02d}", f"{mon}/{d:02d}/{y%100:02d}", f"{d:02d}{mon}{y}"])
    else:          fmt = f"{d:02d} {m:02d} {y%100:02d}"                 # 공백 구분 DD MM YY
    prefix = random.choice(["", "", "", "", "EXP ", "EXP:", "BEST BEFORE ", "BBD ", "USE BY "])
    suffix = random.choice(["", "", "", "", " " + str(random.randint(10, 23)) + ":" + f"{random.randint(0, 59):02d}", " L" + str(random.randint(1, 9)), " A", " B"])
    return prefix + fmt + suffix


def draw_dot_text(text, cell, radius, ink, jitter, col_gap, row_gap):
    """점 격자로 글자를 그린 RGBA 이미지. cell = 점 간격(px)."""
    cols = sum(5 + col_gap for _ in text)
    W, H = int(cols * cell + cell * 2), int((7 + row_gap) * cell + cell * 2)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = cell
    for ch in text:
        pat = FONT57.get(ch.upper(), FONT57[" "])
        for r, row in enumerate(pat):
            for c, bit in enumerate(row):
                if bit == "1":
                    cx, cy = x + c * cell + random.uniform(-jitter, jitter), cell + r * cell + random.uniform(-jitter, jitter)
                    rr = radius * random.uniform(0.85, 1.15)
                    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=ink)
        x += (5 + col_gap) * cell
    return im


def background(imgs, w, h):
    """실제 사진의 무작위 조각을 강하게 블러해 배경으로. 글자는 사라지고 색·질감만 남는다."""
    path = random.choice(imgs)
    try:
        im = ImageOps.exif_transpose(Image.open(path).convert("RGB"))
    except Exception:
        return Image.new("RGB", (w, h), (random.randint(180, 255),) * 3)
    im.thumbnail((1200, 1200))
    if im.width < w or im.height < h:
        im = im.resize((max(w, im.width), max(h, im.height)))
    x0, y0 = random.randint(0, im.width - w), random.randint(0, im.height - h)
    patch = im.crop((x0, y0, x0 + w, y0 + h)).filter(ImageFilter.GaussianBlur(random.uniform(4, 9)))
    return patch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--out", default="data/rec_synth")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    random.seed(a.seed); np.random.seed(a.seed)
    out = os.path.join(ROOT, a.out); os.makedirs(os.path.join(out, "imgs"), exist_ok=True)
    imgs = glob.glob(os.path.join(ROOT, "images", "*.jpg"))
    ttf = [f for f in ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/cour.ttf", "C:/Windows/Fonts/consola.ttf"] if os.path.exists(f)]
    lines = []
    for i in range(a.n):
        text = rand_date()
        dot = random.random() < 0.8 or not ttf
        dark = random.random() < 0.75          # 어두운 잉크 on 밝은 배경 (75%), 밝은 잉크 on 어두운 배경 (25%)
        ink = (random.randint(0, 60),) * 3 if dark else (random.randint(200, 255),) * 3
        if random.random() < 0.15:              # 가끔 색 잉크 (빨강/파랑)
            ink = random.choice([(random.randint(150, 220), 0, 0), (0, 0, random.randint(120, 200))])
        if dot:
            cell = random.uniform(4, 9); radius = cell * random.uniform(0.32, 0.52)
            txt = draw_dot_text(text, cell, radius, ink + (255,), jitter=cell * random.uniform(0, 0.12),
                                col_gap=random.choice([1, 1, 2]), row_gap=random.choice([1, 2]))
        else:
            f = ImageFont.truetype(random.choice(ttf), random.randint(28, 56))
            bw, bh = ImageDraw.Draw(Image.new("RGB", (10, 10))).textbbox((0, 0), text, font=f)[2:]
            txt = Image.new("RGBA", (bw + 30, bh + 24), (0, 0, 0, 0)); ImageDraw.Draw(txt).text((15, 8), text, font=f, fill=ink + (255,))
        txt = txt.rotate(random.uniform(-4, 4), expand=True, resample=Image.BICUBIC)
        pad = random.randint(6, 24)
        W, H = txt.width + pad * 2, txt.height + pad * 2
        bg = background(imgs, W, H)
        if dark and np.array(bg).mean() < 110:   # 어두운 잉크인데 배경이 어두우면 배경을 밝힌다
            bg = Image.blend(bg, Image.new("RGB", bg.size, (235, 235, 225)), 0.7)
        if not dark and np.array(bg).mean() > 140:
            bg = Image.blend(bg, Image.new("RGB", bg.size, (30, 30, 40)), 0.7)
        bg.paste(txt, (pad, pad), txt)
        im = bg
        if random.random() < 0.5:
            im = im.filter(ImageFilter.GaussianBlur(random.uniform(0.3, 1.2)))
        arr = np.array(im).astype(np.float32) + np.random.normal(0, random.uniform(0, 8), np.array(im).shape)
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        if random.random() < 0.3:
            s = random.uniform(0.5, 0.85); im = im.resize((max(32, int(im.width * s)), max(12, int(im.height * s))), Image.BILINEAR)
        fn = f"synth_{i:05d}.jpg"
        im.save(os.path.join(out, "imgs", fn), quality=random.randint(60, 92))
        lines.append(f"imgs/{fn}\t{text}")
    with open(os.path.join(out, "synth_list.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    # 미리보기 시트
    sample = random.sample(lines, min(40, len(lines)))
    sheet = Image.new("RGB", (4 * 420, 10 * 110), "white"); d = ImageDraw.Draw(sheet)
    for k, ln in enumerate(sample):
        fn, lab = ln.split("\t"); im = Image.open(os.path.join(out, fn)); im.thumbnail((410, 80))
        x, y = (k % 4) * 420, (k // 4) * 110; sheet.paste(im, (x + 5, y + 5)); d.text((x + 5, y + 92), lab, fill="black")
    sheet.save(os.path.join(out, "sheet_01.jpg"), quality=85)
    print(f"{len(lines)}장 → {a.out}/synth_list.txt, sheet_01.jpg")


if __name__ == "__main__":
    main()
