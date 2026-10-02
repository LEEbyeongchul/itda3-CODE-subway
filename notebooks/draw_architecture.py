"""파이프라인 아키텍처 구조도를 PNG(보고서·발표용)와 SVG(편집용)로 그린다. 본선 최종 구성 기준(2026-09-29).
A4 세로 비율(1:1.414)에 맞춰 단계를 세로로 쌓는다 — 보고서(A4 세로)에 그대로 끼워 넣기 위함.

    python notebooks/draw_architecture.py            # → docs/img/architecture.png, architecture.svg
    python notebooks/draw_architecture.py --acc "86.2%" --field "90.8%" --speed "2.7~4.0초"   # 수치 갱신
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _font(regular_idx, size):
    if os.path.exists("C:/Windows/Fonts/malgun.ttf"):
        path = "C:/Windows/Fonts/malgunbd.ttf" if regular_idx == 6 else "C:/Windows/Fonts/malgun.ttf"
        return ImageFont.truetype(path, size)
    if os.path.exists("/System/Library/Fonts/AppleSDGothicNeo.ttc"):
        return ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", size, index=regular_idx)
    return ImageFont.load_default()


ap = argparse.ArgumentParser()
ap.add_argument("--acc", default="86.2%", help="봉인 500장 완전일치")
ap.add_argument("--field", default="90.8%", help="봉인 500장 필드평균")
ap.add_argument("--speed", default="2.7~4.0초", help="개발 PC 4스레드 장당 (한도 2,500초의 55~79%)")
ap.add_argument("--note", default="본선 최종 구성 · 모델 총 21MB · 완전 오프라인")
a = ap.parse_args()

# 본선보고서 3-1 텍스트 다이어그램의 핵심만 줄였다. [본선] = 예선 이후 추가된 처리.
STAGES = [
    ("입력", ["사진 1장, EXIF로 방향 보정 · 긴 변 2,000px 로 축소"], "#EEF2F7"),
    ("① 1차 읽기", ["640px 축소본에서 탐지·인식, 후보 없으면 1,024px → 도트 전처리"], "#DCEBFA"),
    ("② 다시 읽기", ["후보 줄만 원본 해상도로 재인식. [본선] 1차 후보는 지우지 않는다"], "#DCEBFA"),
    ("③ 주변 재탐지 [본선]", ["옆에 비슷한 숫자줄 있을 때만 그 영역을 원본 해상도로 재탐지"], "#E4F1E4"),
    ("④ 못 읽은 사진 전용", ["파인튜닝 인식기로 재시도. [본선] 작은 사진은 2배 확대"], "#FBEEDB"),
    ("⑤ 해석·선택", ["형식 정규화 → 신뢰 등급 → 연도 검증 → 같은 등급에서 가장 늦은 날짜"], "#FBEEDB"),
    ("출력", ["YYYY-MM-DD · YYYY-MM-NONE · NONE-MM-DD · NONE"], "#EEF2F7"),
]

GUARD = "시간 예산 가드 — 예산을 넘으면 재시도를 줄여서라도 500장 전부 결과를 만든다"
A4_RATIO = 297 / 210  # 세로 / 가로

MARGIN, TOP, ROW_GAP = 70, 160, 50
W = 1040
BOX_W = W - MARGIN * 2
CANVAS_H = 2400  # 넉넉히 잡고 끝에서 실제 내용 높이로 자른다
img = Image.new("RGB", (W, CANVAS_H), "white")
d = ImageDraw.Draw(img)
f_title = _font(6, 34)
f_head = _font(6, 25)
f_body = _font(0, 21)
f_small = _font(0, 19)
f_guard = _font(6, 21)


def wrap(text, font, width):
    words, lines, cur = text.split(" "), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = wd
    if cur:
        lines.append(cur)
    return lines


svg = []


def box(y, head, body, color):
    """한 단계 상자를 그리고 다음 y 좌표를 반환한다."""
    head_lines = wrap(head, f_head, BOX_W - 40)
    body_lines = [sub for line in body for sub in wrap(line, f_body, BOX_W - 44)]
    h = 18 + len(head_lines) * 30 + 14 + len(body_lines) * 30 + 16
    d.rounded_rectangle([MARGIN, y, MARGIN + BOX_W, y + h], radius=16, fill=color, outline="#94A3B8", width=3)
    svg.append(f'<rect x="{MARGIN}" y="{y}" width="{BOX_W}" height="{h}" rx="16" fill="{color}" stroke="#94A3B8" stroke-width="3"/>')
    hy = y + 18
    for sub in head_lines:
        d.text((MARGIN + 22, hy), sub, font=f_head, fill="#111827")
        svg.append(f'<text x="{MARGIN+22}" y="{hy+23}" font-size="23" font-weight="bold" fill="#111827">{sub}</text>')
        hy += 30
    div_y = hy + 7
    d.line([MARGIN + 22, div_y, MARGIN + BOX_W - 22, div_y], fill="#94A3B8", width=2)
    svg.append(f'<line x1="{MARGIN+22}" y1="{div_y}" x2="{MARGIN+BOX_W-22}" y2="{div_y}" stroke="#94A3B8" stroke-width="2"/>')
    yy = div_y + 24
    for sub in body_lines:
        d.text((MARGIN + 22, yy), sub, font=f_body, fill="#1F2937")
        svg.append(f'<text x="{MARGIN+22}" y="{yy+19}" font-size="19" fill="#1F2937">{sub}</text>')
        yy += 30
    return y + h


def down_arrow(y_from, y_to):
    cx = MARGIN + BOX_W // 2
    d.line([cx, y_from + 6, cx, y_to - 16], fill="#475569", width=5)
    d.polygon([(cx, y_to - 2), (cx - 10, y_to - 18), (cx + 10, y_to - 18)], fill="#475569")
    svg.append(f'<line x1="{cx}" y1="{y_from+6}" x2="{cx}" y2="{y_to-16}" stroke="#475569" stroke-width="5"/>')
    svg.append(f'<polygon points="{cx},{y_to-2} {cx-10},{y_to-18} {cx+10},{y_to-18}" fill="#475569"/>')


svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="PLACEHOLDER" font-family="Apple SD Gothic Neo, Malgun Gothic, sans-serif">')
svg.append('<rect width="100%" height="100%" fill="white"/>')
title = "소비기한 OCR 파이프라인 — 본선 최종 구성"
subtitle = f"봉인 500장 완전일치 {a.acc} (필드평균 {a.field}) · 4코어 CPU 장당 {a.speed}"
subtitle2 = a.note
d.text((MARGIN, 36), title, font=f_title, fill="#1F2937")
d.text((MARGIN, 86), subtitle, font=f_small, fill="#4B5563")
d.text((MARGIN, 114), subtitle2, font=f_small, fill="#4B5563")
svg.append(f'<text x="{MARGIN}" y="68" font-size="32" font-weight="bold" fill="#1F2937">{title}</text>')
svg.append(f'<text x="{MARGIN}" y="103" font-size="19" fill="#4B5563">{subtitle}</text>')
svg.append(f'<text x="{MARGIN}" y="131" font-size="19" fill="#4B5563">{subtitle2}</text>')

y = TOP
for i, (head, body, color) in enumerate(STAGES):
    y_end = box(y, head, body, color)
    if i < len(STAGES) - 1:
        down_arrow(y_end, y_end + ROW_GAP)
    y = y_end + ROW_GAP

# 시간 예산 가드
gy = y + 10
gh = 0
guard_lines = wrap(GUARD, f_guard, BOX_W - 48)
gh = 20 + len(guard_lines) * 28 + 16
d.rounded_rectangle([MARGIN, gy, MARGIN + BOX_W, gy + gh], radius=14, outline="#B45309", width=3)
svg.append(f'<rect x="{MARGIN}" y="{gy}" width="{BOX_W}" height="{gh}" rx="14" fill="none" stroke="#B45309" stroke-width="3" stroke-dasharray="10,6"/>')
gyy = gy + 20
for sub in guard_lines:
    d.text((MARGIN + 22, gyy), sub, font=f_guard, fill="#92400E")
    svg.append(f'<text x="{MARGIN+22}" y="{gyy+19}" font-size="21" font-weight="bold" fill="#92400E">{sub}</text>')
    gyy += 28

# 하단 설명
notes = [
    "채점 조건: 4코어 CPU · 500장 2,500초 · 인터넷 차단",
    "모델은 탐지기 1개 + 인식기 2개, 합쳐 약 21MB — 나머지는 전부 규칙",
]
yy = gy + gh + 30
for n in notes:
    for sub in wrap("• " + n, f_small, BOX_W):
        d.text((MARGIN, yy), sub, font=f_small, fill="#374151")
        svg.append(f'<text x="{MARGIN}" y="{yy+15}" font-size="19" fill="#374151">{sub}</text>')
        yy += 28
    yy += 6

H = yy + 30
svg[0] = svg[0].replace("PLACEHOLDER", str(H))
svg.append("</svg>")

print(f"→ 캔버스 {W}x{H}, 비율(가로/세로) {W/H:.3f} (A4 세로 목표 {1/A4_RATIO:.3f})")

out = os.path.join(ROOT, "docs", "img"); os.makedirs(out, exist_ok=True)
img.crop((0, 0, W, H)).save(os.path.join(out, "architecture.png"))
open(os.path.join(out, "architecture.svg"), "w", encoding="utf-8").write("\n".join(svg))
print("→ docs/img/architecture.png, architecture.svg")
