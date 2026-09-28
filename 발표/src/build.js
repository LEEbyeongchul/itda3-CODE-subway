// [CODE]_서브웨이 본선 발표 자료 — 참고 덱(진한 빨강 섹션 + 흰 본문, 왼쪽 빨간 표식 제목) 디자인
const pptxgen = require("pptxgenjs");
const path = require("path");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.title = "[CODE]_서브웨이 본선 발표";

const RED = "8B0000", INK = "1A1A1A", MUTE = "6B6B6B", CARD = "F2F2F2", LINE = "BFBFBF", WHITE = "FFFFFF", PINK = "F6E3E3";
const KR = "맑은 고딕";
const IMG = (n) => path.join(__dirname, "img", n);
let pageNo = 0;

function pageNum(s, dark) {
  pageNo += 1;
  s.addText(String(pageNo), { x: 9.3, y: 0.12, w: 0.5, h: 0.25, fontFace: "Arial", fontSize: 9, bold: true, color: dark ? WHITE : INK, align: "right", margin: 0, isTextBox: true });
}
function content(title, accent) {
  const s = pres.addSlide(); s.background = { color: WHITE };
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.3, w: 0.07, h: 0.4, fill: { color: RED }, line: { color: RED, width: 0 } });
  const runs = [{ text: title, options: { color: INK } }];
  if (accent) runs.push({ text: accent, options: { color: RED } });
  s.addText(runs, { x: 0.45, y: 0.25, w: 8.7, h: 0.5, fontFace: KR, fontSize: 19, bold: true, margin: 0, valign: "middle", isTextBox: true });
  s.addShape(pres.shapes.LINE, { x: 0.3, y: 0.82, w: 9.4, h: 0, line: { color: LINE, width: 0.75 } });
  pageNum(s, false); return s;
}
function section(num, title, sub) {
  const s = pres.addSlide(); s.background = { color: RED };
  s.addText(String(num), { x: 5.2, y: 0.6, w: 4.8, h: 5.4, fontFace: "Arial", fontSize: 400, bold: true, color: WHITE, align: "right", valign: "middle", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.RECTANGLE, { x: 1.05, y: 3.05, w: 0.07, h: 0.5, fill: { color: WHITE }, line: { color: WHITE, width: 0 } });
  s.addText(title, { x: 1.22, y: 2.98, w: 5, h: 0.65, fontFace: KR, fontSize: 28, bold: true, color: WHITE, margin: 0, valign: "middle", isTextBox: true });
  if (sub) s.addText(sub, { x: 1.22, y: 3.68, w: 5.2, h: 0.4, fontFace: KR, fontSize: 12, color: WHITE, margin: 0, isTextBox: true });
  pageNum(s, true); return s;
}
const card = (s, x, y, w, h, fill) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill || CARD }, line: { color: fill || CARD, width: 0 } });
const txt = (s, t, x, y, w, h, o) => s.addText(t, Object.assign({ x, y, w, h, fontFace: KR, fontSize: 12, color: INK, margin: 0, valign: "top", isTextBox: true }, o || {}));
// 빨간 강조가 섞인 한 줄: ["일반", ["강조"], "일반"]
const rich = (parts, base) => parts.map((p) => Array.isArray(p) ? { text: p[0], options: Object.assign({ color: RED, bold: true }, base || {}) } : { text: p, options: Object.assign({}, base || {}) });
function strip(s, parts, y, h) {
  card(s, 0.3, y, 9.4, h || 0.42);
  s.addText(rich(parts), { x: 0.45, y, w: 9.1, h: h || 0.42, fontFace: KR, fontSize: 12.5, bold: true, color: INK, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function badge(s, n, x, y) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.34, h: 0.34, fill: { color: RED }, line: { color: RED, width: 0 } });
  s.addText(n, { x, y, w: 0.34, h: 0.34, fontFace: "Arial", fontSize: 10, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function table(s, rows, x, y, w, colW, o) {
  o = o || {};
  const data = rows.map((r, ri) => r.map((c) => {
    const cell = typeof c === "string" ? { text: c } : c;
    const head = ri === 0;
    return { text: cell.text, options: Object.assign({ fontFace: KR, fontSize: o.fontSize || 10.5, color: head ? WHITE : INK, bold: head || !!cell.bold, fill: { color: head ? "3A3A3A" : (cell.hl ? PINK : WHITE) }, align: cell.align || "left", valign: "middle", margin: [3, 6, 3, 6] }, cell.red ? { color: RED, bold: true } : {}) };
  }));
  s.addTable(data, { x, y, w, colW, rowH: o.rowH || 0.3, border: { type: "solid", color: "9A9A9A", pt: 0.5 } });
}

// ───────────────────────── 1. 표지
{
  const s = pres.addSlide(); s.background = { color: RED };
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.2, w: 0.08, h: 1.25, fill: { color: WHITE }, line: { color: WHITE, width: 0 } });
  txt(s, "읽지 못하면, 읽지 못했다고 말하는 OCR", 0.95, 1.15, 8.6, 0.7, { fontSize: 30, bold: true, color: WHITE, valign: "middle" });
  txt(s, "소비기한 추출 파이프라인과 물류 입고 검수 적용", 0.95, 1.88, 8.6, 0.55, { fontSize: 20, bold: true, color: WHITE, valign: "middle" });
  txt(s, "4코어 CPU · GPU 없음 · 오프라인 환경에서의 경량 OCR 설계와 검증", 0.95, 2.7, 8.3, 0.35, { fontSize: 13, color: WHITE });
  txt(s, "제3회 ITDA 연합학술제 본선  |  [CODE]_서브웨이", 0.95, 4.35, 8.3, 0.3, { fontSize: 12, color: WHITE });
  txt(s, "민섭 · 서현 · 병철 · 승아 · 서영", 0.95, 4.68, 8.3, 0.3, { fontSize: 12, color: WHITE });
  pageNum(s, true);
  s.addNotes("안녕하세요, CODE 서브웨이 팀입니다. 저희는 상품 뒷면 사진에서 소비기한을 읽는 OCR을 만들었습니다. 오늘 드릴 말씀의 핵심은 제목 그대로입니다. 저희 시스템은 잘 읽는 것만큼, 못 읽었을 때 못 읽었다고 말하는 것을 중요하게 설계했습니다. 왜 그렇게 했는지, 그리고 그 설계가 물류 현장에서 어떤 의미인지 10분 동안 말씀드리겠습니다.");
}

// ───────────────────────── 2. 섹션 1
section(1, "문제 정의", "무엇을, 어떤 제약 아래에서 풀었는가").addNotes("먼저 문제와 제약입니다.");

// 3. 제약이 설계를 정했다
{
  const s = content("출발점 : ", "제약이 설계를 결정했다");
  const items = [["3,352장", "정답 라벨 없음", "상품 뒷면 사진만 제공. 정확도를 잴 자(尺)부터 직접 만들어야 했다"],
                 ["4코어 CPU", "GPU 없음 · 오프라인", "채점 서버 Ubuntu 22.04, RAM 8GB. 무거운 모델·외부 API 사용 불가"],
                 ["2,500초", "500장 제한 시간", "초과하면 결과 파일이 나오지 않아 정확도까지 0점. 장당 5초가 상한"]];
  items.forEach((it, i) => {
    const x = 0.3 + i * 3.18;
    card(s, x, 1.05, 3.04, 2.45);
    txt(s, it[0], x + 0.2, 1.22, 2.64, 0.7, { fontFace: "Arial", fontSize: 34, bold: true, color: RED, valign: "middle" });
    txt(s, it[1], x + 0.2, 1.95, 2.64, 0.35, { fontSize: 13.5, bold: true });
    txt(s, it[2], x + 0.2, 2.4, 2.64, 1.0, { fontSize: 12, color: MUTE });
  });
  txt(s, rich(["첫 파이프라인(EasyOCR)은 4코어에서 ", ["장당 5.8초, 500장 2,905초"], " 로 한도를 넘겼다"]), 0.3, 3.85, 9.4, 0.3, { fontSize: 12.5, align: "center" });
  txt(s, rich(["정확도를 올리기 전에 ", ["\"끝까지 돌아가는가\""], " 부터 풀어야 하는 문제였다"]), 0.3, 4.2, 9.4, 0.3, { fontSize: 12.5, align: "center" });
  strip(s, ["그래서 모든 설계 결정에 ", ["정확도와 시간을 함께"], " 기록했다"], 4.75);
  s.addNotes("이 대회는 세 가지 제약이 있었습니다. 첫째, 사진 3,352장에 정답이 없습니다. 둘째, 채점 서버는 GPU 없는 4코어 CPU이고 인터넷이 끊겨 있습니다. 셋째, 500장을 2,500초 안에 끝내야 하고, 넘기면 결과 파일 자체가 안 나와 정확도까지 0점입니다. 처음 만든 파이프라인은 500장에 2,905초가 걸려 이미 탈락이었습니다. 그래서 정확도보다 먼저, 끝까지 돌아가는 구조에서 출발했습니다.");
}

// ───────────────────────── 4. 섹션 2
section(2, "데이터와 검증 설계", "정답이 없는 데이터에서 정확도를 재는 법").addNotes("두 번째는 검증 설계입니다. 심사에서 가장 먼저 확인하실 부분이라고 생각합니다.");

// 5. 라벨링·측정 프로토콜
{
  const s = content("검증 설계 : ", "규칙을 먼저 정하고, 시험지를 봉인했다");
  badge(s, "01", 0.3, 1.05); txt(s, "해석 규칙을 먼저 문서로 확정", 0.72, 1.05, 4.0, 0.34, { fontSize: 13, bold: true, valign: "middle" });
  txt(s, "라벨러는 포장에 찍힌 그대로만 입력. 해석(연·월·일 순서, 2자리 연도)은 도구가 규칙으로 처리 → 라벨과 모델이 같은 규칙을 쓴다", 0.72, 1.4, 4.0, 0.8, { fontSize: 11, color: MUTE });
  badge(s, "02", 0.3, 2.3); txt(s, "3,352장 전수 직접 라벨링", 0.72, 2.3, 4.0, 0.34, { fontSize: 13, bold: true, valign: "middle" });
  txt(s, "5명 분담, 자체 제작 라벨링 도구. 오답 530장을 사람이 다시 보고 라벨 오류 23장 수정", 0.72, 2.65, 4.0, 0.7, { fontSize: 11, color: MUTE });
  badge(s, "03", 0.3, 3.45); txt(s, "약점 유형만 골라 추가 촬영", 0.72, 3.45, 4.0, 0.34, { fontSize: 13, bold: true, valign: "middle" });
  txt(s, "도트 인쇄·각인·두 날짜 병기 위주 494장 촬영, 389장 라벨링. 한 번도 본 적 없는 시험지로 사용", 0.72, 3.8, 4.0, 0.7, { fontSize: 11, color: MUTE });

  card(s, 5.0, 1.05, 4.7, 3.5);
  txt(s, "데이터 분리", 5.2, 1.15, 4.3, 0.3, { fontSize: 12.5, bold: true });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.55, w: 0.64, h: 0.55, fill: { color: RED }, line: { color: RED, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.84, y: 1.55, w: 3.66, h: 0.55, fill: { color: "BDBDBD" }, line: { color: "BDBDBD", width: 0 } });
  txt(s, "500", 5.2, 1.55, 0.64, 0.55, { fontFace: "Arial", fontSize: 12, bold: true, color: WHITE, align: "center", valign: "middle" });
  txt(s, "2,852", 5.84, 1.55, 3.66, 0.55, { fontFace: "Arial", fontSize: 12, bold: true, color: INK, align: "center", valign: "middle" });
  txt(s, rich([["봉인 500장"], "  학습·규칙 도출에 쓰지 않음. 측정 전용"]), 5.2, 2.2, 4.3, 0.3, { fontSize: 11 });
  txt(s, rich([["판정용 2,852장"], "  모든 채택·기각 판정"], { }), 5.2, 2.5, 4.3, 0.3, { fontSize: 11 });
  txt(s, "채택 기준", 5.2, 2.95, 4.3, 0.3, { fontSize: 12.5, bold: true });
  txt(s, [{ text: "새로 맞힌 장(회복)과 새로 틀린 장(퇴보)을 따로 센다", options: { bullet: true, breakLine: true } },
          { text: "퇴보가 회복의 1/3 을 넘으면 점수가 올라도 기각", options: { bullet: true, breakLine: true } },
          { text: "±1%p 는 잡음으로 보고 근거로 쓰지 않는다", options: { bullet: true } }], 5.2, 3.27, 4.3, 1.15, { fontSize: 11, paraSpaceAfter: 3 });
  strip(s, ["정답 라벨도 검증 대상 : 고친 라벨 23장 중 ", ["16장은 모델이 맞은 쪽"], " 이었다"], 4.75);
  s.addNotes("정답이 없으니 자부터 만들었습니다. 먼저 날짜를 어떻게 해석할지 규칙을 문서로 정하고, 그 규칙대로 동작하는 라벨링 도구를 만들어 3,352장 전부에 다섯 명이 직접 라벨을 달았습니다. 그중 500장은 따로 봉인해서 학습과 규칙 도출에 쓰지 않고 측정에만 썼고, 오늘 말씀드리는 공식 수치는 전부 이 500장 기준입니다. 기능을 넣을지는 나머지 2,852장에서 판정했고, 새로 맞힌 장과 새로 틀린 장을 따로 세어 퇴보가 크면 점수가 올라도 버렸습니다. 정답 라벨도 의심했습니다. 오답을 다시 보니 라벨이 틀린 게 23장, 그중 16장은 모델이 맞은 경우였습니다.");
}

// ───────────────────────── 6. 섹션 3
section(3, "아키텍처 설계", "왜 이 구조인가").addNotes("세 번째, 아키텍처입니다.");

// 7. 파이프라인 구조도
{
  const s = content("전체 파이프라인 : ", "쉬운 사진은 한 번에, 어려운 사진에만 비용을");
  const steps = [["입력", "EXIF 보정\n640px 축소"], ["① 탐지", "PP-OCRv5 det\n5MB · 장당 1회"], ["② 인식", "PP-OCRv5 rec\n큰 글자부터"], ["③ 다시 읽기", "후보 줄만 원본으로\n3표 다수결"], ["④ 규칙 해석", "형식 정규화\n잡음 제거 · 선택"], ["출력", "YYYY-MM-DD\n또는 NONE"]];
  steps.forEach((st, i) => {
    const x = 0.3 + i * 1.6, dl = i === 1 || i === 2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.1, w: 1.4, h: 1.15, rectRadius: 0.06, fill: { color: dl ? RED : "3A3A3A" }, line: { color: dl ? RED : "3A3A3A", width: 0 } });
    txt(s, st[0], x, 1.17, 1.4, 0.32, { fontSize: 12, bold: true, color: WHITE, align: "center", valign: "middle" });
    txt(s, st[1], x + 0.05, 1.5, 1.3, 0.7, { fontSize: 9.5, color: WHITE, align: "center", valign: "middle" });
    if (i < steps.length - 1) txt(s, "▶", x + 1.4, 1.5, 0.2, 0.3, { fontFace: "Arial", fontSize: 10, color: MUTE, align: "center", valign: "middle" });
  });
  txt(s, rich([["■ "], "사전학습 딥러닝 모델      "], {}), 0.3, 2.32, 3, 0.25, { fontSize: 9.5, color: MUTE });
  txt(s, "■ 규칙·재인식 단계", 2.2, 2.32, 3, 0.25, { fontSize: 9.5, color: MUTE });

  txt(s, "조건이 맞을 때만 동작하는 단계", 0.3, 2.7, 9.4, 0.3, { fontSize: 12.5, bold: true });
  table(s, [["장치", "발동 조건", "동작", "효과"],
            ["이웃 줄 재탐지", "후보 줄 옆에 크기 비슷한 숫자 줄", "그 주변만 원본 해상도로 다시 탐지", "병기 +5 / −1"],
            ["도트 인쇄 폴백", "후보 없음", "점을 이어 붙이는 전처리 후 재시도", "+17 / −0"],
            ["파인튜닝 인식기", "그래도 후보 없음", "우리 라벨로 학습한 인식기로 재시도", "+7 / −0"],
            ["시간 예산 가드", "예상 소요 2,000초 초과", "폴백 생략 → 2패스 생략 → NONE", "완주 보장"]],
        0.3, 3.0, 9.4, [1.7, 2.9, 3.4, 1.4], { fontSize: 10, rowH: 0.29 });
  strip(s, ["딥러닝은 ", ["\"읽기\""], " 만, 소비기한을 고르는 판단은 ", ["설명 가능한 규칙"], " 이 맡는다"], 4.75);
  s.addNotes("구조는 단순합니다. 사진을 640픽셀로 줄여서 글자 위치를 찾고, 큰 글자부터 읽습니다. 날짜로 보이는 줄만 원본 해상도로 다시 읽어서 첫 결과와 다수결합니다. 그다음 규칙이 형식을 해석하고 소비기한을 고릅니다. 빨간 상자 두 개만 딥러닝 모델이고 나머지는 규칙입니다. 중요한 건 아래 표입니다. 비용이 큰 단계는 전부 조건부입니다. 대부분의 사진은 위 한 줄로 끝나고, 어려운 사진에서만 재탐지, 도트 폴백, 파인튜닝 인식기가 차례로 동작합니다.");
}

// 8. 오답 단계 진단
{
  const s = content("설계 사고 : ", "오답을 \"정답이 사라진 단계\" 로 진단했다");
  txt(s, rich(["예선 구성의 오답 ", ["603장"], " (3,352장 전체 기준) 마다, 정답 날짜가 파이프라인 어느 단계까지 살아 있었는지 추적"]), 0.3, 0.98, 9.4, 0.3, { fontSize: 12 });
  const st = [["183", "못 읽음", "탐지 실패 · 전부 미인식", "원본 재탐지\n작은 사진 확대"], ["290", "잘못 읽음", "인식기가 숫자를 오독", "후처리 규칙 보강\n파인튜닝 폴백"], ["111", "읽었다가 지움", "다시 읽기가 정답을 덮어씀", "\"교정만, 삭제 금지\"\n유지 규칙"], ["19", "잘못 고름", "가짜 후보가 늦은 날짜로 승리", "이중 해석 억제"]];
  st.forEach((r, i) => {
    const x = 0.3 + i * 2.38;
    card(s, x, 1.42, 2.26, 2.1);
    txt(s, r[0], x + 0.15, 1.5, 1.96, 0.62, { fontFace: "Arial", fontSize: 32, bold: true, color: RED, valign: "middle" });
    txt(s, r[1], x + 0.15, 2.12, 1.96, 0.3, { fontSize: 13, bold: true });
    txt(s, r[2], x + 0.15, 2.42, 1.96, 0.45, { fontSize: 10.5, color: MUTE });
    txt(s, r[3], x + 0.15, 2.9, 1.96, 0.55, { fontSize: 10.5, bold: true, color: INK });
  });
  txt(s, "단계마다 처방이 다르다", 0.3, 3.68, 9.4, 0.3, { fontSize: 12.5, bold: true });
  txt(s, [{ text: "\"읽었다가 지움\" 111장은 모델이 아니라 코드 로직의 문제 → 규칙 하나로 판정용 2,852장 +45 / −4", options: { bullet: true, breakLine: true } },
          { text: "\"못 읽음\" 은 해상도를 올려도 회복되지 않았다 (5가지 구성 전부 ±1%p, 시간만 +30~50%) → 원인은 탐지가 아니라 인식 품질", options: { bullet: true } }], 0.3, 3.98, 9.4, 0.7, { fontSize: 11, paraSpaceAfter: 3 });
  strip(s, ["오답을 뭉뚱그려 \"모델을 키우자\" 가 아니라, ", ["원인별로 가장 싼 처방"], " 을 골랐다"], 4.75);
  s.addNotes("본선에서 가장 먼저 한 일은 오답 진단입니다. 오답 603장마다 정답 날짜가 어느 단계까지 살아 있었는지를 추적했더니 네 가지로 갈렸습니다. 못 읽은 것 183장, 잘못 읽은 것 290장, 그리고 흥미로운 게 세 번째입니다. 처음엔 맞게 읽었는데 다시 읽기 단계가 그 정답을 지워 버린 게 111장이었습니다. 이건 모델 문제가 아니라 저희 코드의 문제였고, 다시 읽기는 교정만 하고 삭제는 못 하게 규칙 하나를 바꿔서 45장을 되찾았습니다. 이렇게 원인을 나눠 놓으니, 모델을 키우는 대신 원인마다 가장 싼 처방을 고를 수 있었습니다.");
}

// 9. 후처리: 소비기한 vs 다른 숫자
{
  const s = content("후처리 규칙 : ", "소비기한을 다른 숫자와 구분하는 법");
  table(s, [["구분 대상", "실제 예", "규칙", "근거"],
            ["품목보고번호 · 바코드", "20130628332176", "9자리 이상 숫자열은 통째로 제거", "앞 8자리가 완전한 날짜 형식"],
            ["영양성분표 · 중량", "78 7 5 31 / 30.4 GRAMS", "신뢰 등급 : 완전 날짜 > 공백·압축 > 연월 > 월일", "잡음이 이긴 오답 15장에서 도출"],
            ["제조일자 · 유통기한", "25.06.26  /  26.06.25", "가장 좋은 등급 안에서 가장 늦은 날짜", "소비기한 ≥ 유통기한 ≥ 제조일"],
            ["시각 · 로트번호", "13:11  /  A03  /  L8", "날짜 패턴에서 제외, 옆 글자는 일(日)로 읽지 않음", "도트 인쇄 제품에 흔함"],
            ["연·월·일 순서", "30.07.26  /  24/12/21", "년월일 우선. 무효·2028년 이후면 일월년", "라벨 : 년월일 344 · 일월년 102"],
            ["범위 밖 연도", "2033, 2009", "2017 ~ 2031 만 인정", "전수 라벨 최소 2017"]],
        0.3, 1.0, 9.4, [1.7, 1.9, 3.55, 2.25], { fontSize: 9.6, rowH: 0.36 });
  card(s, 0.3, 3.7, 4.6, 0.9);
  txt(s, "미인식(NONE) 기준", 0.45, 3.76, 4.3, 0.28, { fontSize: 12, bold: true });
  txt(s, "후보가 하나도 없으면 추측하지 않는다. 연도나 일만 없으면 그 칸만 NONE (NONE-10-14, 2027-07-NONE)", 0.45, 4.04, 4.3, 0.52, { fontSize: 10.5, color: MUTE });
  card(s, 5.1, 3.7, 4.6, 0.9);
  txt(s, "라벨과 모델이 같은 규칙", 5.25, 3.76, 4.3, 0.28, { fontSize: 12, bold: true });
  txt(s, "운영진 확정 : 모호한 표기는 팀이 문서화한 규칙으로 채점. 규칙 문서 하나를 라벨링 도구와 파서가 공유", 5.25, 4.04, 4.3, 0.52, { fontSize: 10.5, color: MUTE });
  strip(s, ["규칙마다 ", ["어떤 오답에서 나왔는지"], " 와 ", ["회복·퇴보 수"], " 가 기록돼 있다"], 4.75);
  s.addNotes("소비기한을 다른 숫자와 어떻게 구분하는가입니다. 품목보고번호는 앞 여덟 자리가 완전한 날짜 형식이라, 아홉 자리 이상 숫자열은 통째로 지웁니다. 영양성분표 숫자는 신뢰 등급으로 거릅니다. 구분자가 있는 완전한 날짜가 항상 이깁니다. 제조일자와 소비기한이 같이 있으면 가장 늦은 날짜를 고르고, 연월일 순서가 모호하면 직접 단 라벨의 통계로 정한 기본값을 씁니다. 후보가 없으면 추측하지 않고 NONE을 냅니다. 규칙마다 어떤 오답에서 나왔고 몇 장을 얻고 잃었는지가 기록돼 있습니다.");
}

// ───────────────────────── 10. 섹션 4
section(4, "성능과 속도 검증", "무엇을 채택하고 무엇을 버렸는가").addNotes("네 번째, 결과입니다.");

// 11. 성능 이력 (차트)
{
  const s = content("정확도 : ", "봉인 500장 86.2%, 필드 평균 90.8%");
  const labels = ["EasyOCR", "규칙 5개", "인식기 교체", "탐지기 교체", "신뢰 등급", "도트 폴백", "2패스 다수결", "규칙 v5·v6", "파인튜닝 폴백", "예선 제출", "본선 통합"];
  const vals = [39.1, 44.4, 60.9, 71.2, 73.6, 77.0, 78.4, 81.8, 83.2, 84.2, 86.2];
  s.addChart(pres.charts.BAR, [{ name: "완전일치(%)", labels, values: vals }], {
    x: 0.3, y: 0.95, w: 6.1, h: 3.45, barDir: "col", chartColors: ["B9B9B9", "B9B9B9", "B9B9B9", "B9B9B9", "B9B9B9", "B9B9B9", "B9B9B9", "B9B9B9", "B9B9B9", "5A5A5A", RED],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 9, dataLabelColor: INK, dataLabelFontFace: "Arial", dataLabelFormatCode: "0.0",
    catAxisLabelFontSize: 8, catAxisLabelFontFace: KR, catAxisLabelColor: MUTE, catAxisLabelRotate: 315, valAxisLabelFontSize: 8, valAxisLabelColor: MUTE, valAxisMinVal: 30, valAxisMaxVal: 95,
    valGridLine: { color: "E3E3E3", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, showTitle: false });
  txt(s, "※ 앞 세 단계는 개발용 133장, 이후는 500장 기준", 0.4, 4.45, 6, 0.22, { fontSize: 8.5, color: MUTE });
  card(s, 6.6, 0.95, 3.1, 1.45);
  txt(s, "봉인 500장 · 완전일치", 6.78, 1.02, 2.8, 0.26, { fontSize: 10.5, color: MUTE });
  txt(s, "86.2%", 6.78, 1.26, 2.8, 0.62, { fontFace: "Arial", fontSize: 34, bold: true, color: RED, valign: "middle" });
  txt(s, "예선 제출본 84.2% → +2.0%p", 6.78, 1.9, 2.8, 0.4, { fontSize: 10.5 });
  table(s, [["구분", "정확도"], ["필드 평균 (채점 방식)", { text: "90.8%", bold: true, red: true }], ["작은 사진 (≤700px)", "83.7%"], ["중간", "89.5%"], ["큰 사진", "86.7%"], ["두 날짜 병기", "78.4%"], ["미인식률", "3.0%"]],
        6.6, 2.52, 3.1, [2.0, 1.1], { fontSize: 10, rowH: 0.29 });
  strip(s, ["판정용 2,852장에서도 ", ["82.3 → 86.0%"], " : 튜닝에 쓴 셋과 봉인 셋이 함께 올랐다"], 4.75);
  s.addNotes("결과입니다. 처음 39%에서 출발해서 예선 제출 때 84.2%, 본선 통합본은 봉인 500장에서 86.2%입니다. 연월일을 따로 채점하는 필드 평균으로는 90.8%입니다. 가장 큰 도약은 탐지기와 인식기를 교체한 구간인데, 속도 때문에 한 결정이 정확도까지 올린 경우입니다. 튜닝에 쓴 2,852장에서는 82.3에서 86.0으로 올랐고, 한 번도 보지 않은 봉인 셋에서도 같이 올랐기 때문에 튜닝 셋에 과적합된 상승이 아니라고 판단합니다.");
}

// 12. 채택/기각
{
  const s = content("모델·대안 비교 : ", "점수가 올라도 기각한 것들");
  table(s, [["시도", "결과 (회복 / 퇴보)", "판단", "이유"],
            ["탐지·인식기 PP-OCRv5 mobile 로 교체", "39.1 → 67.7%, 5.8 → 1.8초", { text: "채택", bold: true, red: true }, "속도 한도와 정확도를 동시에 해결"],
            ["2패스 \"교정만, 삭제 금지\"", "+45 / −4", { text: "채택", bold: true, red: true }, "코드 로직 결함 수정"],
            ["본선 규칙 합계 (위 포함 7개)", "+102 / −7", { text: "채택", bold: true, red: true }, "병기 64 → 78%"],
            ["이웃 줄 원본 재탐지", "병기 +5 / −1, 그 외 0 / 0", { text: "채택", bold: true, red: true }, "게이트로 비용을 병기에만"],
            ["파인튜닝 인식기를 1순위로", "+86 / −64 (+0.8%p)", "기각", "맞던 답을 흔든다 → 폴백으로만 사용"],
            ["합성 도트 데이터 3,000장 학습", "76.8% (정밀도 84 → 81%)", "기각", "진짜 글씨를 대충 읽게 됨"],
            ["탐지 해상도 상향 (5구성)", "±1%p, 시간 +30~50%", "기각", "원인이 해상도가 아님"],
            ["한국어 인식기 2차 의견", "+14 / −1 → 최신 규칙 위 0 / 0", "보류", "시간 +18%, 기여가 사라짐"],
            ["회전 · 탐지 임계 완화 재시도", "회복 0, 엉뚱한 값 6", "기각", "미인식을 오답으로 바꿀 뿐"]],
        0.3, 1.0, 9.4, [3.0, 2.4, 0.8, 3.2], { fontSize: 9.8, rowH: 0.345 });
  strip(s, ["파인튜닝은 +0.8%p 였지만 ", ["퇴보 64장"], " 때문에 버렸다. 채택 기준이 점수보다 먼저다"], 4.75);
  s.addNotes("저희가 시도한 것 중 절반은 버렸습니다. 대표적인 게 파인튜닝입니다. 저희 라벨로 인식기를 학습시켜서 1순위로 썼더니 정확도가 0.8퍼센트포인트 올랐습니다. 그런데 새로 맞힌 게 86장, 새로 틀린 게 64장이었습니다. 전체 점수는 올랐지만 잘 맞히던 사진 64장을 망가뜨린 겁니다. 그래서 기각했고, 기존 인식기가 못 읽은 사진에만 쓰는 방식으로 넣어 퇴보 없이 7장을 얻었습니다. 합성 데이터도, 해상도 상향도 같은 기준으로 버렸습니다.");
}

// 13. 속도
{
  const s = content("속도·효율 : ", "한도의 60%, 그리고 완주 보장");
  const k = [["약 3초", "장당 처리 시간", "4코어 고정 측정"], ["1,500초", "500장 환산", "한도 2,500초의 60%"], ["1.25GB", "최대 메모리", "한도 8GB (40장 실측)"], ["0원", "학습 비용", "무료 Colab T4 만 사용"]];
  k.forEach((r, i) => {
    const x = 0.3 + i * 2.38;
    card(s, x, 1.02, 2.26, 1.3);
    txt(s, r[0], x + 0.15, 1.08, 1.96, 0.55, { fontFace: KR, fontSize: 24, bold: true, color: RED, valign: "middle" });
    txt(s, r[1], x + 0.15, 1.63, 1.96, 0.28, { fontSize: 11.5, bold: true });
    txt(s, r[2], x + 0.15, 1.9, 1.96, 0.3, { fontSize: 10, color: MUTE });
  });
  txt(s, "속도를 만든 결정", 0.3, 2.5, 4.6, 0.3, { fontSize: 12.5, bold: true });
  txt(s, [{ text: "탐지는 640px 축소본에서 장당 1회 (탐지 비용 = 픽셀 수)", options: { bullet: true, breakLine: true } },
          { text: "인식은 큰 글자부터, 날짜를 찾으면 잔글씨 생략", options: { bullet: true, breakLine: true } },
          { text: "8개씩 배치 인식 (16개 498 → 321ms)", options: { bullet: true, breakLine: true } },
          { text: "다시 읽기는 후보 줄 크롭만, 폴백은 후보 없는 장에만", options: { bullet: true } }], 0.3, 2.8, 4.6, 1.6, { fontSize: 10.8, paraSpaceAfter: 4 });
  card(s, 5.1, 2.5, 4.6, 2.05);
  txt(s, "시간 예산 가드 : 3단계 자동 경량화", 5.25, 2.57, 4.3, 0.3, { fontSize: 12, bold: true });
  txt(s, "최근 20장 속도로 총 소요를 예측, 2,000초를 넘길 것 같으면", 5.25, 2.87, 4.3, 0.3, { fontSize: 10.5, color: MUTE });
  [["1", "재시도 단계 생략"], ["2", "다시 읽기 생략"], ["3", "남은 장 NONE, 결과 파일은 반드시 생성"]].forEach((r, i) => {
    badge(s, r[0], 5.25, 3.25 + i * 0.4); txt(s, r[1], 5.68, 3.25 + i * 0.4, 3.9, 0.34, { fontSize: 11, valign: "middle" });
  });
  strip(s, ["채점 서버 속도를 모르는 상황에서 ", ["\"느리면 0점\""], " 을 구조로 막았다"], 4.75);
  s.addNotes("속도입니다. 채점 환경과 같은 4코어로 고정해서 쟀을 때 장당 약 3초, 500장에 1,500초로 한도의 60퍼센트입니다. 메모리는 1.25기가, 학습은 무료 코랩만 써서 비용이 0원입니다. 탐지는 줄인 사진에서 한 번만 하고, 인식은 큰 글자부터 읽다가 날짜를 찾으면 멈춥니다. 오른쪽이 시간 가드입니다. 채점 서버가 얼마나 빠른지 저희는 모릅니다. 그래서 속도를 지켜보다가 늦을 것 같으면 단계적으로 가벼워지고, 최악의 경우에도 결과 파일은 반드시 나오게 했습니다.");
}

// 14. 시연 캡처
{
  const s = content("실행 화면 : ", "실제 파이프라인 출력");
  const demos = [["demo_plain.png", "일반 인쇄"], ["demo_two.png", "제조·소비 병기"], ["demo_dot.png", "도트 인쇄 (폴백)"], ["demo_none.png", "미인식 → 사람 확인"]];
  demos.forEach((d, i) => {
    const x = 0.3 + i * 2.38;
    s.addImage({ path: IMG(d[0]), x, y: 1.0, w: 2.26, h: 2.142 });
    txt(s, d[1], x, 3.2, 2.26, 0.3, { fontSize: 11.5, bold: true, align: "center" });
  });
  card(s, 0.3, 3.62, 9.4, 1.0);
  txt(s, [{ text: "빨간 상자 = 선택된 날짜 줄, 회색 상자 = 다른 후보. 아래 패널은 파이프라인이 실제로 낸 값·후보·처리 시간", options: { bullet: true, breakLine: true } },
          { text: "병기 사진 : 25.06.26(제조)과 26.06.25(소비)를 모두 읽고 늦은 날짜를 선택", options: { bullet: true, breakLine: true } },
          { text: "네 번째 : 후보가 없으면 날짜를 지어내지 않고 NONE. 현장에서는 이 건만 사람에게 간다", options: { bullet: true } }], 0.45, 3.68, 9.1, 0.9, { fontSize: 10.5, paraSpaceAfter: 3 });
  strip(s, ["재현 : 새 환경에서 ", ["설치 → 가중치 다운로드 → Run All"], " 검증, Ubuntu·Python 3.10·오프라인 자동 테스트 통과"], 4.75);
  s.addNotes("실제 실행 화면입니다. 두 번째가 제조일자와 소비기한이 같이 찍힌 경우입니다. 25년 6월 26일과 26년 6월 25일을 둘 다 읽고 늦은 쪽을 골랐습니다. 세 번째는 도트 인쇄인데, 처음엔 못 읽었다가 점을 이어 붙이는 전처리 후에 읽어 낸 경우입니다. 그리고 네 번째를 일부러 넣었습니다. 못 읽은 사진입니다. 저희 시스템은 여기서 날짜를 지어내지 않고 NONE을 냅니다. 이 선택이 다음에 말씀드릴 현장 적용의 핵심입니다.");
}

// ───────────────────────── 15. 섹션 5
section(5, "도메인 적용과 운영", "물류센터 입고 검수").addNotes("마지막으로 현장 적용입니다.");

// 16. 도메인: 입고 검수
{
  const s = content("적용 도메인 : ", "신선식품 물류센터 입고 검수");
  txt(s, rich(["센터는 기한이 빠른 상품부터 출고한다. 그런데 ", ["공급사가 신고한 기한과 실물이 맞는지"], " 는 지금 사람이 눈으로 확인한다"]), 0.3, 0.98, 9.4, 0.3, { fontSize: 12 });
  const fl = [["촬영", "검수자가 로트별\n대표 상품 표시면 촬영"], ["OCR", "온디바이스 또는\n센터 내 CPU 서버"], ["대조", "읽은 값 vs 공급사 신고값\n잔여기한 기준 계산"]];
  fl.forEach((r, i) => {
    const x = 0.3 + i * 2.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.5, w: 1.85, h: 1.2, rectRadius: 0.06, fill: { color: "3A3A3A" }, line: { color: "3A3A3A", width: 0 } });
    txt(s, r[0], x, 1.58, 1.85, 0.32, { fontSize: 13, bold: true, color: WHITE, align: "center", valign: "middle" });
    txt(s, r[1], x + 0.05, 1.92, 1.75, 0.7, { fontSize: 9.8, color: WHITE, align: "center", valign: "middle" });
    txt(s, "▶", x + 1.85, 1.95, 0.2, 0.3, { fontFace: "Arial", fontSize: 10, color: MUTE, align: "center", valign: "middle" });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.45, y: 1.3, w: 3.25, h: 0.72, rectRadius: 0.06, fill: { color: CARD }, line: { color: CARD, width: 0 } });
  txt(s, rich([["일치"], "  →  자동 통과 (약 80%)"]), 6.6, 1.3, 3.0, 0.72, { fontSize: 11.5, valign: "middle" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.45, y: 2.12, w: 3.25, h: 0.72, rectRadius: 0.06, fill: { color: PINK }, line: { color: PINK, width: 0 } });
  txt(s, rich([["불일치 · 미인식 · 기준 미달"], "\n→  사람 확인 대기열"]), 6.6, 2.12, 3.0, 0.72, { fontSize: 11, valign: "middle" });

  card(s, 0.3, 3.05, 4.6, 1.55);
  txt(s, "이 구조의 핵심", 0.45, 3.12, 4.3, 0.28, { fontSize: 12, bold: true });
  txt(s, rich(["OCR이 잘못 읽어도 신고값과 어긋나 사람에게 간다. 그래서 정확도는 ", ["안전성이 아니라 자동화율"], " 을 결정한다. 위험한 것은 \"못 읽음\" 이 아니라 \"틀린 값을 자신 있게 냄\" 이고, 우리는 그래서 NONE 을 설계했다"]), 0.45, 3.42, 4.3, 1.15, { fontSize: 10.8 });
  card(s, 5.1, 3.05, 4.6, 1.55);
  txt(s, "운영에서 더 세지는 신호", 5.25, 3.12, 4.3, 0.28, { fontSize: 12, bold: true });
  txt(s, [{ text: "읽은 날짜가 오늘보다 이르면 경고 (대회 데이터에서 이 신호의 오답률 72%)", options: { bullet: true, breakLine: true } },
          { text: "제조·포장 키워드만 읽히면 경고 (오답률 57%)", options: { bullet: true, breakLine: true } },
          { text: "사람이 고친 값은 이력과 함께 재학습 데이터로", options: { bullet: true } }], 5.25, 3.42, 4.3, 1.15, { fontSize: 10.5, paraSpaceAfter: 3 });
  strip(s, ["기한 정보가 담긴 QR 이 없는 상품을 맡는 ", ["보완 수단"], " : 제조사 수천 곳이 아니라 읽는 쪽 한 곳만 바뀌면 된다"], 4.75);
  s.addNotes("적용 대상은 신선식품 물류센터의 입고 검수입니다. 공급사가 신고한 기한과 실제 상품의 기한이 맞는지는 지금 사람이 눈으로 확인합니다. 검수자가 로트별로 대표 상품을 찍으면 OCR이 읽고, 읽은 값을 공급사 신고값과 대조합니다. 일치하면 자동 통과, 어긋나거나 못 읽은 건만 사람에게 갑니다. 여기서 중요한 점은, OCR이 틀리게 읽어도 신고값과 어긋나기 때문에 사람에게 간다는 겁니다. 즉 정확도는 안전성이 아니라 자동화율을 결정합니다. 정말 위험한 건 못 읽는 게 아니라 틀린 값을 자신 있게 내는 것이고, 그래서 저희는 확신이 없으면 NONE을 내도록 설계했습니다.");
}

// 17. 운영 구조·비용·ROI
{
  const s = content("운영 구조와 비용 : ", "CPU 한 대로 시작한다");
  table(s, [["구성", "온디바이스 (검수 단말)", "센터 내 서버"],
            ["환경", "핸디 단말·태블릿 CPU", "4코어 CPU 서버 1대, GPU 없음"],
            ["모델", "탐지 5MB + 인식 8MB × 2", "동일 (총 21MB)"],
            ["네트워크", "불필요 (오프라인 동작 검증)", "센터 내부망"],
            ["처리량", "장당 약 3초", "시간당 약 1,200장"],
            ["적합한 곳", "냉장·냉동 구역, 통신 음영", "검수대 고정 촬영, 이력 집계"]],
        0.3, 1.0, 5.6, [1.2, 2.2, 2.2], { fontSize: 10, rowH: 0.34 });
  card(s, 6.1, 1.0, 3.6, 2.05);
  txt(s, "비용 구조", 6.25, 1.07, 3.3, 0.28, { fontSize: 12, bold: true });
  txt(s, [{ text: "라이선스 0원 (오픈소스 모델, 외부 API 없음)", options: { bullet: true, breakLine: true } },
          { text: "GPU 0대, 학습 비용 0원", options: { bullet: true, breakLine: true } },
          { text: "서버 1대 또는 기존 단말 활용", options: { bullet: true, breakLine: true } },
          { text: "남는 비용은 사람 확인 인건비", options: { bullet: true } }], 6.25, 1.37, 3.3, 1.6, { fontSize: 10.5, paraSpaceAfter: 3 });
  txt(s, "절감 효과 계산 (가정을 명시한 추정)", 0.3, 3.2, 9.4, 0.3, { fontSize: 12.5, bold: true });
  table(s, [["항목", "가정", "계산", "결과"],
            ["현재 : 전수 육안 확인", "하루 2,000 로트, 건당 20초", "2,000 × 20초", "하루 11.1시간"],
            ["도입 후 : 예외만 확인", "자동 통과 80%, 확인 건당 8초 (실측)", "400 × 8초 + 촬영", { text: "하루 0.9시간 + 촬영", bold: true, red: true }],
            ["실측 근거", "오답 446장 점검에 61분", "장당 평균 8초", "불일치율 15.6%"]],
        0.3, 3.5, 9.4, [2.2, 3.2, 1.9, 2.1], { fontSize: 10, rowH: 0.29 });
  strip(s, ["로트 수·건당 시간은 가정값. ", ["확인 건당 8초와 불일치율은 우리가 직접 잰 값"], " 이다"], 4.75);
  s.addNotes("모델 전체가 21메가바이트이고 GPU가 필요 없어서, 검수 단말에 넣으면 통신이 안 되는 냉동 구역에서도 동작하고, 서버 한 대에 두면 시간당 1,200장을 처리합니다. 라이선스 0원, GPU 0대이고, 남는 비용은 사람이 확인하는 인건비입니다. 하루 2,000로트를 건당 20초씩 본다고 가정하면 지금은 하루 11시간입니다. 도입 후에는 예외 400건만 보면 됩니다. 건당 8초는 저희가 오답 446장을 다시 볼 때 잰 실측값이고, 로트 수와 현재 확인 시간은 가정입니다.");
}

// 18. 한계
{
  const s = content("한계 : ", "약점만 모은 새 시험지에서는 45%");
  card(s, 0.3, 1.0, 4.6, 2.2);
  txt(s, "직접 촬영 166장 (도트·각인·병기만)", 0.45, 1.07, 4.3, 0.28, { fontSize: 12, bold: true });
  s.addChart(pres.charts.BAR, [{ name: "완전일치(%)", labels: ["배포 데이터 (봉인 500장)", "직접 촬영 (약점 유형)"], values: [86.2, 45.2] }], {
    x: 0.4, y: 1.35, w: 4.4, h: 1.8, barDir: "bar", chartColors: ["5A5A5A", RED], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelFontFace: "Arial", dataLabelColor: INK, dataLabelFormatCode: "0.0",
    catAxisLabelFontSize: 9.5, catAxisLabelFontFace: KR, catAxisLabelColor: INK, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 100, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, showTitle: false });
  card(s, 5.1, 1.0, 4.6, 2.2);
  txt(s, "남은 한계 세 가지", 5.25, 1.07, 4.3, 0.28, { fontSize: 12, bold: true });
  txt(s, [{ text: "도트 인쇄·각인 : 규칙으로는 끝. 인식기 학습 데이터가 답", options: { bullet: true, breakLine: true } },
          { text: "작은 사진 (전체의 33%) : 글자 8~12픽셀, 확대·해상도 상향 모두 효과 없음", options: { bullet: true, breakLine: true } },
          { text: "제조일자만 있는 사진 (정답 NONE) : 한글 단서가 필요해 미지원, 0.5% 미만", options: { bullet: true } }], 5.25, 1.37, 4.3, 1.75, { fontSize: 10.5, paraSpaceAfter: 4 });
  txt(s, "보완 계획", 0.3, 3.38, 9.4, 0.3, { fontSize: 12.5, bold: true });
  [["01", "촬영 단계에서 막는다", "\"날짜를 가운데, 가까이\" 가이드와 반사 감지 재촬영"], ["02", "어려운 크롭을 사람이 고른다", "미인식 사진의 날짜 줄을 검수해 재학습"], ["03", "경고를 붙인다", "답은 바꾸지 않고 의심 신호에 사람 확인 표시"]].forEach((r, i) => {
    const x = 0.3 + i * 3.18;
    badge(s, r[0], x, 3.75); txt(s, r[1], x + 0.42, 3.72, 2.6, 0.3, { fontSize: 11.5, bold: true, valign: "middle" });
    txt(s, r[2], x + 0.42, 4.02, 2.6, 0.6, { fontSize: 10, color: MUTE });
  });
  strip(s, ["86% 는 쉬운 사진이 섞인 평균이다. ", ["약점의 실제 크기를 따로 재서 공개"], " 한다"], 4.75);
  s.addNotes("한계를 말씀드리겠습니다. 저희는 86퍼센트라는 숫자를 그대로 믿지 않았습니다. 오답이 몰린 유형, 즉 도트 인쇄와 각인, 두 날짜 병기만 골라서 팀원들이 편의점에서 직접 사진을 찍었고, 모델이 한 번도 본 적 없는 그 사진에 돌렸더니 45퍼센트가 나왔습니다. 약점의 실제 크기는 이만큼입니다. 남은 오답은 규칙이 아니라 인식 품질의 문제라서, 촬영 단계에서 날짜를 가까이 찍게 안내하고, 못 읽은 날짜 줄을 사람이 골라 재학습하는 방향으로 보완합니다.");
}

// 19. 확장
{
  const s = content("확장성 : ", "\"제품에 찍힌 기한\" 을 읽는 모든 곳");
  table(s, [["적용 분야", "읽는 값", "바꿀 것", "그대로 쓰는 것"],
            ["의약품·화학 제품 출하 표시물 검증", "제조번호 · 사용기한", "표기 형식 규칙", "읽기 · 신고값 대조 · 예외 처리"],
            ["온라인 식품 발송 시점 기한 검증", "소비기한", "대조 대상 (판매 페이지 약속)", "파이프라인 전체"],
            ["단체급식 식재료 검수일지", "소비기한", "출력 양식 (검수일지)", "파이프라인 전체"],
            ["고압가스 용기 · 소화기 점검", "재검사 기한 · 제조연월", "형식 규칙, 각인 전처리", "탐지 · 폴백 구조"]],
        0.3, 1.0, 9.4, [3.1, 2.0, 2.2, 2.1], { fontSize: 10.3, rowH: 0.38 });
  card(s, 0.3, 3.15, 9.4, 1.45);
  txt(s, "왜 옮겨 쓸 수 있는가", 0.45, 3.22, 9.1, 0.28, { fontSize: 12, bold: true });
  txt(s, [{ text: "딥러닝 모델은 \"글자를 읽는 일\" 만 하고, 도메인 지식은 전부 규칙 문서 한 장에 있다", options: { bullet: true, breakLine: true } },
          { text: "읽기 → 기준값과 대조 → 예외만 사람에게 : 이 세 단계는 분야가 바뀌어도 같다", options: { bullet: true, breakLine: true } },
          { text: "사람이 확정한 값이 다시 학습 데이터가 되는 순환 구조", options: { bullet: true } }], 0.45, 3.52, 9.1, 1.05, { fontSize: 10.8, paraSpaceAfter: 3 });
  strip(s, ["규칙 계층만 바꾸면 되는 구조 : ", ["모델을 다시 만들 필요가 없다"]], 4.75);
  s.addNotes("이 구조는 식품에만 쓰이지 않습니다. 의약품이나 화학 제품의 출하 표시물에서 제조번호와 사용기한을 검증하는 일도 같은 구조입니다. 모델은 글자를 읽는 일만 하고 도메인 지식은 규칙 문서에 있기 때문에, 형식 규칙만 바꾸면 됩니다.");
}

// 20. 마무리
{
  const s = pres.addSlide(); s.background = { color: RED };
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 0.75, w: 0.08, h: 0.55, fill: { color: WHITE }, line: { color: WHITE, width: 0 } });
  txt(s, "정리", 0.95, 0.72, 8, 0.6, { fontSize: 26, bold: true, color: WHITE, valign: "middle" });
  const pts = [["제약에서 출발", "4코어 CPU · 2,500초 안에서 끝까지 돌아가는 구조. 봉인 500장 86.2%, 한도의 60%"],
               ["검증을 먼저", "전수 라벨링, 봉인 시험지, 회복·퇴보 기준. 점수가 올라도 퇴보가 크면 버렸다"],
               ["틀리는 방식을 설계", "확신이 없으면 NONE. 현장에서는 정확도가 안전성이 아니라 자동화율이 된다"]];
  pts.forEach((p, i) => {
    const y = 1.7 + i * 1.05;
    s.addShape(pres.shapes.OVAL, { x: 0.95, y: y + 0.03, w: 0.5, h: 0.5, fill: { color: WHITE }, line: { color: WHITE, width: 0 } });
    txt(s, String(i + 1), 0.95, y + 0.03, 0.5, 0.5, { fontFace: "Arial", fontSize: 16, bold: true, color: RED, align: "center", valign: "middle" });
    txt(s, p[0], 1.65, y - 0.02, 7.6, 0.34, { fontSize: 16, bold: true, color: WHITE, valign: "middle" });
    txt(s, p[1], 1.65, y + 0.32, 7.6, 0.4, { fontSize: 11.5, color: WHITE });
  });
  txt(s, "감사합니다  |  github.com/LEEbyeongchul/itda3-CODE-subway", 0.95, 4.95, 8.3, 0.3, { fontSize: 11, color: WHITE });
  pageNum(s, true);
  s.addNotes("정리하겠습니다. 첫째, 제약에서 출발해 봉인 500장 86.2퍼센트를 한도의 60퍼센트 시간에 냈습니다. 둘째, 검증을 먼저 세웠습니다. 점수가 올라도 잘 맞히던 걸 망가뜨리면 버렸습니다. 셋째, 틀리는 방식을 설계했습니다. 확신이 없으면 못 읽었다고 말하는 시스템이기 때문에, 현장에서 사람과 함께 일할 수 있습니다. 감사합니다.");
}

// 21~. 부록 (Q&A 대비)
{
  const s = content("부록 : ", "날짜 해석 규칙표 (모호한 표기)");
  table(s, [["상황", "해석", "근거 (전수 라벨 3,352장)"],
            ["4자리 연도가 앞 / 뒤", "앞이면 년/월/일, 뒤면 일/월/년. 구분자 종류는 무관", "연도 앞 2,217 · 연도 뒤 362"],
            ["2자리 세 개 (26.03.20)", "년/월/일 우선. 무효이거나 연도 2028 이상이면 일/월/년", "년월일 344 : 일월년 102"],
            ["영문 유통 문구 (BBD, BEST BEFORE, EXP)", "같은 사진에 있으면 일/월/년 우선", "수입품 표기 관행"],
            ["공백 구분 (30 12 23)", "일/월/년", "전부 수입품"],
            ["영문 월 (04-Jul-21, 22OCT2021)", "월 위치 확정, 4자리는 연도", "148장"],
            ["월/일/년 (06/18/23)", "일/월/년이 불가능할 때만 (가운데 13 이상)", "확정 미국식 2장"],
            ["연월만 / 월일만", "YYYY-MM-NONE / NONE-MM-DD", "운영진 확정"],
            ["날짜가 여럿", "가장 좋은 등급 안에서 가장 늦은 날짜", "병기 345장 (10.3%)"]],
        0.3, 1.0, 9.4, [3.0, 4.2, 2.2], { fontSize: 10, rowH: 0.385 });
  strip(s, ["해석 기본값은 감이 아니라 ", ["직접 단 라벨의 통계"], " 로 정했다"], 4.75);
  s.addNotes("질의응답용 부록입니다. 모호한 날짜 표기를 어떻게 해석하는지와 그 근거입니다.");
}
{
  const s = content("부록 : ", "측정 수치 한눈에");
  table(s, [["측정셋", "구성", "완전일치", "필드평균", "비고"],
            ["봉인 500장", "예선 제출본 (9/13)", "84.2%", "88.8%", "미인식 17"],
            ["봉인 500장", "본선 통합본 (9/28)", { text: "86.2%", bold: true, red: true }, { text: "90.8%", bold: true, red: true }, "미인식 15, 정밀도 88.9%"],
            ["판정용 2,852장", "예선 구성", "81.9%", "", "라벨 점검 후 82.3%, 병기 64.1%"],
            ["판정용 2,852장", "본선 규칙 + 한국어 2차 의견", "86.0%", "", "라벨 점검 후, 병기 77.9%"],
            ["판정용 2,852장", "통합본 (9/24, 규칙 4개 전)", "85.1%", "89.8%", "예선 대비 +97 / −6"],
            ["직접 촬영 166장", "본선 통합본", "45.2%", "59.0%", "약점 유형만, 미인식 23%"]],
        0.3, 1.0, 9.4, [1.7, 3.0, 1.2, 1.2, 2.3], { fontSize: 10, rowH: 0.36 });
  txt(s, [{ text: "완전일치 : 연·월·일이 모두 맞은 사진 비율", options: { bullet: true, breakLine: true } },
          { text: "필드평균 : 연·월·일을 따로 채점한 평균 (운영진 채점 방식)", options: { bullet: true, breakLine: true } },
          { text: "회복 / 퇴보 : 이전 버전 대비 새로 맞힌 장 / 새로 틀린 장", options: { bullet: true } }], 0.3, 3.7, 9.4, 0.95, { fontSize: 10.8, paraSpaceAfter: 3 });
  strip(s, ["모든 수치의 예측 파일과 실험 기록은 ", ["저장소 results/ · docs/실험_기록.md"], " 에 있다"], 4.75);
  s.addNotes("질의응답용 부록입니다. 측정셋별 수치 전체입니다.");
}

pres.writeFile({ fileName: path.join(__dirname, "[CODE]_서브웨이_본선발표.pptx") }).then((f) => console.log("saved", f, "slides", pageNo));
