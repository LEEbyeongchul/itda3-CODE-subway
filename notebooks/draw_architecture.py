"""파이프라인 아키텍처 구조도를 PNG(요약서·발표용)와 SVG(편집용)로 그린다.

    python notebooks/draw_architecture.py            # → docs/img/architecture.png, architecture.svg
    python notebooks/draw_architecture.py --acc "73.6%" --speed "1.8초"   # 수치 갱신
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "C:/Windows/Fonts/malgun.ttf" if os.path.exists("C:/Windows/Fonts/malgun.ttf") else None
FONT_B = "C:/Windows/Fonts/malgunbd.ttf" if os.path.exists("C:/Windows/Fonts/malgunbd.ttf") else FONT

ap = argparse.ArgumentParser()
ap.add_argument("--acc", default="73.6%")
ap.add_argument("--speed", default="1.8초")
ap.add_argument("--note", default="사전학습 모델 그대로 (파인튜닝 전)")
a = ap.parse_args()

STAGES = [
    ("입력", ["원본 사진 (3,352장 배포)", "EXIF 회전 보정", "긴 변 640px 축소", "후보 없으면 1024px 재시도"], "#EEF2F7"),
    ("① 텍스트 탐지", ["PaddleOCR PP-OCRv5 mobile det", "약 5 MB · CPU 전용", "4코어 640px 기준 약 0.3초", "모든 글자 박스 검출"], "#DCEBFA"),
    ("② 텍스트 인식", ["PaddleOCR PP-OCRv5 mobile rec (en)", "약 8 MB · 숫자·영문·구분자", "글자 크기순 8개 배치 인식", "연도 포함 날짜 찾으면 잔글씨 생략"], "#DCEBFA"),
    ("③ 2패스 재인식", ["후보 줄의 단어 박스만", "원본 해상도(≤2000px) 크롭", "검출기 재실행 없음", "자릿수 오독 보정"], "#E4F1E4"),
    ("④ 후처리 규칙", ["오독 복원 2O27→2027, 0ct→Oct", "정규식 4단계 (완전 날짜 → 공백·6자리 → 연월 → 월일)", "연도 2017~2031 검증, 긴 숫자열 제거", "신뢰 등급 우선 → 가장 늦은 날짜"], "#FBEEDB"),
    ("출력", ["YYYY-MM-DD", "NONE-MM-DD (연도 없음)", "YYYY-MM-NONE (일 없음)", "NONE (판독 불가)"], "#EEF2F7"),
]

W, H = 2600, 760
BOX_W, BOX_H, GAP, TOP = 380, 330, 52, 150
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
f_title = ImageFont.truetype(FONT_B, 34) if FONT_B else ImageFont.load_default()
f_head = ImageFont.truetype(FONT_B, 26) if FONT_B else ImageFont.load_default()
f_body = ImageFont.truetype(FONT, 20) if FONT else ImageFont.load_default()
f_small = ImageFont.truetype(FONT, 19) if FONT else ImageFont.load_default()

d.text((60, 40), "소비기한 OCR 파이프라인 아키텍처", font=f_title, fill="#1F2937")
d.text((60, 92), f"측정용 500장 정확도 {a.acc} · 4코어 CPU 장당 {a.speed} · 인터넷 차단 환경 · {a.note}", font=f_small, fill="#4B5563")

x0 = (W - (len(STAGES) * BOX_W + (len(STAGES) - 1) * GAP)) // 2
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Malgun Gothic, Apple SD Gothic Neo, sans-serif">',
       f'<rect width="{W}" height="{H}" fill="white"/>',
       f'<text x="60" y="72" font-size="34" font-weight="bold" fill="#1F2937">소비기한 OCR 파이프라인 아키텍처</text>',
       f'<text x="60" y="110" font-size="19" fill="#4B5563">측정용 500장 정확도 {a.acc} · 4코어 CPU 장당 {a.speed} · 인터넷 차단 환경 · {a.note}</text>']

def wrap(text, font, width):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines

for i, (head, body, color) in enumerate(STAGES):
    x = x0 + i * (BOX_W + GAP)
    y = TOP
    d.rounded_rectangle([x, y, x + BOX_W, y + BOX_H], radius=18, fill=color, outline="#94A3B8", width=3)
    d.text((x + 22, y + 18), head, font=f_head, fill="#111827")
    d.line([x + 22, y + 60, x + BOX_W - 22, y + 60], fill="#94A3B8", width=2)
    yy = y + 76
    for line in body:
        for sub in wrap(line, f_body, BOX_W - 44):
            d.text((x + 22, yy), sub, font=f_body, fill="#1F2937")
            yy += 30
    svg.append(f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{BOX_H}" rx="18" fill="{color}" stroke="#94A3B8" stroke-width="3"/>')
    svg.append(f'<text x="{x+22}" y="{y+46}" font-size="26" font-weight="bold" fill="#111827">{head}</text>')
    svg.append(f'<line x1="{x+22}" y1="{y+60}" x2="{x+BOX_W-22}" y2="{y+60}" stroke="#94A3B8" stroke-width="2"/>')
    yy = y + 100
    for line in body:
        svg.append(f'<text x="{x+22}" y="{yy}" font-size="20" fill="#1F2937">{line}</text>'); yy += 30
    if i < len(STAGES) - 1:
        ax0, ax1, ay = x + BOX_W + 6, x + BOX_W + GAP - 6, y + BOX_H // 2
        d.line([ax0, ay, ax1 - 12, ay], fill="#475569", width=5)
        d.polygon([(ax1, ay), (ax1 - 16, ay - 10), (ax1 - 16, ay + 10)], fill="#475569")
        svg.append(f'<line x1="{ax0}" y1="{ay}" x2="{ax1-12}" y2="{ay}" stroke="#475569" stroke-width="5"/>')
        svg.append(f'<polygon points="{ax1},{ay} {ax1-16},{ay-10} {ax1-16},{ay+10}" fill="#475569"/>')

# 하단 설명
notes = [
    "채점 제약: GPU 없는 4코어 CPU · 500장 · 셀 타임아웃 2,400초 · Python 3.10 · 가중치는 download_weights.sh 로 사전 다운로드 (git 미포함)",
    "날짜 해석 규칙(연도 위치, 2자리 연도, 공백 구분, 영문 월, 키워드)은 요약서 규칙표와 동일하게 predict.ipynb 파서에 구현 · 라벨링 도구와 같은 규칙",
    "성능 이력(133장): EasyOCR 원본 39.1% → 규칙 수정 44.4% → 인식기 교체 60.9% → 탐지기 교체 67.7% → 신뢰 등급 선택 73.6%(500장)",
]
yy = TOP + BOX_H + 60
for n in notes:
    d.text((60, yy), "• " + n, font=f_small, fill="#374151"); svg.append(f'<text x="60" y="{yy+17}" font-size="19" fill="#374151">• {n}</text>'); yy += 34
svg.append("</svg>")

out = os.path.join(ROOT, "docs", "img"); os.makedirs(out, exist_ok=True)
img.save(os.path.join(out, "architecture.png"))
open(os.path.join(out, "architecture.svg"), "w", encoding="utf-8").write("\n".join(svg))
print("→ docs/img/architecture.png, architecture.svg")
