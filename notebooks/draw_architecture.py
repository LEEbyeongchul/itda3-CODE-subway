"""파이프라인 아키텍처 구조도를 PNG(보고서·발표용)와 SVG(편집용)로 그린다. 본선 최종 구성 기준(2026-09-29).

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

# 본선보고서 3-1 텍스트 다이어그램과 1:1 대응. [본선] 표시는 예선 이후 추가된 처리.
STAGES = [
    ("입력", ["사진 1장 (낱개 뒷면)", "EXIF 회전 보정 (8.7%가 90도 회전)", "긴 변 2,000px 이하로 디코딩 축소"], "#EEF2F7"),
    ("① 1차 읽기", ["640px 축소본에서 글자 위치 탐지", "큰 글자부터 인식, 완전한 날짜 찾으면 잔글씨 생략", "후보 없음 → 1,024px 재시도", "그래도 없음 → 도트 인쇄 전처리 후 재시도"], "#DCEBFA"),
    ("② 다시 읽기", ["후보 줄만 원본 해상도로 재인식, 1차와 다수결", "[본선] 다시 읽은 값이 1차 후보를 지우지 못함", "[본선] 일(日)이 한 자리면 글자상자 넓혀 재인식", "[본선] 깨진 줄은 둘 이상 일치할 때만 후보 추가"], "#DCEBFA"),
    ("③ 주변 재탐지 [본선]", ["후보 줄 옆에 비슷한 크기 숫자줄 있을 때만", "그 영역만 원본 해상도로 다시 탐지", "조건부라 평균 비용 거의 안 늚", "병기(제조일+소비기한) 오답의 주 처방"], "#E4F1E4"),
    ("④ 못 읽은 사진 전용", ["파인튜닝 인식기로 재시도 (크롭 정확도 89.8%)", "[본선] 작은 사진은 2배 확대 후 재시도", "1순위로 쓰면 날짜 아닌 줄을 지어내 기각", "못 읽은 사진에만 적용해 부작용 차단"], "#FBEEDB"),
    ("⑤ 해석·선택", ["형식 정규화 (연월일 순서, 2자리 연도 등)", "신뢰 등급 → 연도 범위(2017~2031) 검증", "같은 등급 안에서 가장 늦은 날짜 선택", "9자리 이상 숫자열은 사전에 제거(바코드 등)"], "#FBEEDB"),
    ("출력", ["YYYY-MM-DD", "YYYY-MM-NONE (일 없음)", "NONE-MM-DD (연도 없음)", "NONE (판독 불가)"], "#EEF2F7"),
]

GUARD = "시간 예산 가드 (모든 단계를 가로지름) — 최근 20장 속도로 총 소요를 예측해 예산을 넘으면 ①의 재시도 생략 → ②를 생략 → 남은 사진은 NONE 으로 채워 결과 파일을 반드시 만든다"

BOX_W, BOX_H, GAP, TOP, MARGIN = 360, 330, 48, 150, 60
W = MARGIN * 2 + len(STAGES) * BOX_W + (len(STAGES) - 1) * GAP
H = 900
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
f_title = _font(6, 34)
f_head = _font(6, 24)
f_body = _font(0, 19)
f_small = _font(0, 18)
f_guard = _font(6, 20)

d.text((60, 40), "소비기한 OCR 파이프라인 아키텍처 — 본선 최종 구성", font=f_title, fill="#1F2937")
d.text((60, 92), f"봉인 500장 완전일치 {a.acc} (필드평균 {a.field}) · 4코어 CPU 장당 {a.speed} · {a.note}", font=f_small, fill="#4B5563")

x0 = MARGIN
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Apple SD Gothic Neo, Malgun Gothic, sans-serif">',
       f'<rect width="{W}" height="{H}" fill="white"/>',
       f'<text x="60" y="72" font-size="34" font-weight="bold" fill="#1F2937">소비기한 OCR 파이프라인 아키텍처 — 본선 최종 구성</text>',
       f'<text x="60" y="110" font-size="18" fill="#4B5563">봉인 500장 완전일치 {a.acc} (필드평균 {a.field}) · 4코어 CPU 장당 {a.speed} · {a.note}</text>']


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
    for sub in wrap(head, f_head, BOX_W - 36):
        d.text((x + 20, y + 16), sub, font=f_head, fill="#111827")
    d.line([x + 20, y + 62, x + BOX_W - 20, y + 62], fill="#94A3B8", width=2)
    yy = y + 78
    for line in body:
        for sub in wrap(line, f_body, BOX_W - 40):
            d.text((x + 20, yy), sub, font=f_body, fill="#1F2937")
            yy += 28
    svg.append(f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{BOX_H}" rx="18" fill="{color}" stroke="#94A3B8" stroke-width="3"/>')
    svg.append(f'<text x="{x+20}" y="{y+42}" font-size="22" font-weight="bold" fill="#111827">{head}</text>')
    svg.append(f'<line x1="{x+20}" y1="{y+62}" x2="{x+BOX_W-20}" y2="{y+62}" stroke="#94A3B8" stroke-width="2"/>')
    yy = y + 100
    for line in body:
        svg.append(f'<text x="{x+20}" y="{yy}" font-size="18" fill="#1F2937">{line}</text>'); yy += 28
    if i < len(STAGES) - 1:
        ax0, ax1, ay = x + BOX_W + 4, x + BOX_W + GAP - 4, y + BOX_H // 2
        d.line([ax0, ay, ax1 - 12, ay], fill="#475569", width=5)
        d.polygon([(ax1, ay), (ax1 - 16, ay - 10), (ax1 - 16, ay + 10)], fill="#475569")
        svg.append(f'<line x1="{ax0}" y1="{ay}" x2="{ax1-12}" y2="{ay}" stroke="#475569" stroke-width="5"/>')
        svg.append(f'<polygon points="{ax1},{ay} {ax1-16},{ay-10} {ax1-16},{ay+10}" fill="#475569"/>')

# 시간 예산 가드 — 모든 단계를 가로지르는 점선 박스
gy = TOP + BOX_H + 36
gx0, gx1 = x0, x0 + len(STAGES) * BOX_W + (len(STAGES) - 1) * GAP
d.rounded_rectangle([gx0, gy, gx1, gy + 64], radius=14, outline="#B45309", width=3)
for i in range(gx0, gx1, 22):
    pass  # PIL rounded_rectangle 는 점선을 직접 지원하지 않아 실선으로 대체
for sub in wrap(GUARD, f_guard, gx1 - gx0 - 48):
    d.text((gx0 + 24, gy + 14), sub, font=f_guard, fill="#92400E")
    gy_line_h = 26
svg.append(f'<rect x="{gx0}" y="{gy}" width="{gx1-gx0}" height="64" rx="14" fill="none" stroke="#B45309" stroke-width="3" stroke-dasharray="10,6"/>')
svg.append(f'<text x="{gx0+24}" y="{gy+38}" font-size="20" font-weight="bold" fill="#92400E">{GUARD}</text>')

# 하단 설명
notes = [
    "채점 제약: GPU 없는 4코어 CPU · 500장 2,500초 · Python 3.10 · 인터넷 차단 · 가중치는 download_weights.sh 로 사전 다운로드 (git 미포함)",
    "딥러닝 모델은 탐지기 1개(사전학습) + 인식기 2개(사전학습 + 우리 라벨 파인튜닝)뿐이고 합쳐 약 21MB. 나머지는 전부 규칙. 비용이 큰 단계는 모두 조건부라 대부분의 사진은 ①·②·⑤만 거친다",
    "정확도 이력: 예선 제출본 84.2% → 다시읽기 규칙 3개 86.0%대(2,852장 기준) → 본선 추가 규칙·재탐지·확대 재시도 반영 → 본선 최종 86.2% (필드평균 90.8%, 봉인 500장)",
]
yy = gy + 64 + 38
for n in notes:
    for sub in wrap("• " + n, f_small, W - 120):
        d.text((60, yy), sub, font=f_small, fill="#374151")
        svg.append(f'<text x="60" y="{yy+16}" font-size="18" fill="#374151">{sub}</text>')
        yy += 28
    yy += 4
svg.append("</svg>")

out = os.path.join(ROOT, "docs", "img"); os.makedirs(out, exist_ok=True)
img = img.crop((0, 0, W, min(H, yy + 20)))
img.save(os.path.join(out, "architecture.png"))
open(os.path.join(out, "architecture.svg"), "w", encoding="utf-8").write("\n".join(svg))
print("→ docs/img/architecture.png, architecture.svg")
