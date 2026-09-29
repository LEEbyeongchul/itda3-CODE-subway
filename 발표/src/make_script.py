# -*- coding: utf-8 -*-
"""build.js 의 발표자 노트를 뽑아 발표 대본(md)을 만든다. 슬라이드와 대본이 항상 같은 문장을 쓰게 하려는 것."""
import io, re, sys

src = io.open("build.js", encoding="utf-8").read()
notes = [m.group(1) for m in re.finditer(r'addNotes\("(.*?)"\)', src, re.S)]
TITLES = ["표지", "[1] 문제 정의", "출발점: 제약이 설계를 결정했다", "[2] 데이터와 검증 설계", "검증 설계: 규칙을 먼저 정하고, 시험지를 봉인했다",
          "[3] 아키텍처 설계", "전체 파이프라인", "설계 사고: 오답을 단계로 진단", "후처리 규칙: 소비기한 vs 다른 숫자", "[4] 성능과 속도 검증",
          "정확도: 봉인 500장 86.2%", "모델·대안 비교: 채택과 기각", "속도·효율", "실행 화면 (시연 캡처)", "[5] 도메인 적용과 운영",
          "적용 도메인: 중고거래 게시글의 소비기한", "운영 구조와 비용", "한계와 보완 계획", "확장성", "정리", "부록 1: 날짜 해석 규칙표", "부록 2: 측정 수치"]
CRIT = {3: "설계 논리", 5: "설계 논리 · 식별력", 7: "설계 논리", 8: "설계 논리", 9: "식별력·정확성 · 후처리 근거", 11: "식별력·정확성", 12: "후처리·모델 근거",
        13: "속도·효율", 14: "식별력 · 발표(시연)", 16: "도메인·운영", 17: "도메인·운영·비용", 18: "설계 논리 · 도메인", 19: "도메인(확장성)", 20: "발표"}
assert len(notes) == len(TITLES) == 22, len(notes)
CPM = 330  # 분당 글자 수(공백 제외), 또박또박 말하는 속도
body = notes[:20]
chars = [len(n.replace(" ", "")) for n in body]
total = sum(chars)
if "--stat" in sys.argv:
    print("본문 글자수", total, "→", round(total / CPM, 1), "분"); sys.exit()

out = []
out.append("# 본선 발표 대본 — [CODE]_서브웨이\n")
out.append("> 발표 10분 + 질의응답 5분. 2026-10-03(토) 14:00, 인하대학교 6호관(경영대학) 220호.")
out.append("> 슬라이드: `발표/[CODE]_서브웨이_본선발표.pptx` (발표자 노트에 같은 대본이 들어 있음). 본문 20장 + 부록 2장.")
out.append(f"> 분량: 공백 제외 {total:,}자, 분당 {CPM}자 기준 약 {total / CPM:.1f}분. 섹션 표지(숫자 슬라이드)는 한 문장만 말하고 넘긴다.\n")
out.append("## 1. 시간 배분\n")
out.append("| 구간 | 슬라이드 | 시간 | 배점 항목 |\n| --- | --- | --- | --- |")
groups = [("문제 정의", 1, 3, "설계 논리 (25)"), ("데이터·검증 설계", 4, 5, "설계 논리 (25) · 식별력 (20)"), ("아키텍처", 6, 9, "설계 논리 (25) · 후처리 근거 (15)"),
          ("성능·속도·시연", 10, 14, "식별력 (20) · 속도 (15) · 모델 근거 (15)"), ("도메인·운영·한계", 15, 19, "도메인·운영·비용 (15)"), ("정리", 20, 20, "발표 (10)")]
acc = 0
for name, a, b, crit in groups:
    sec = sum(chars[a - 1:b]) / CPM * 60
    out.append(f"| {name} | {a}~{b} | {int(sec // 60)}분 {int(sec % 60):02d}초 (누적 {int((acc + sec) // 60)}:{int((acc + sec) % 60):02d}) | {crit} |")
    acc += sec
out.append("\n## 2. 슬라이드별 대본\n")
t = 0
for i, (ti, n) in enumerate(zip(TITLES, notes), 1):
    if i == 21: out.append("## 3. 부록 슬라이드 (질의응답 때만 띄움)\n")
    sec = len(n.replace(" ", "")) / CPM * 60
    head = f"### {i}. {ti}"
    if i <= 20:
        head += f"  ·  {int(t // 60)}:{int(t % 60):02d} 시작, 약 {int(round(sec))}초"
        t += sec
    out.append(head + "\n")
    if i in CRIT: out.append(f"- 겨냥하는 배점: **{CRIT[i]}**")
    out.append(f"\n{n}\n")
out.append(io.open("qa.md", encoding="utf-8").read())
io.open("발표_대본.md", "w", encoding="utf-8").write("\n".join(out))
print("ok", total, round(total / CPM, 1))
