// [CODE]_서브웨이 본선 발표 자료 — 참고 덱(진한 빨강 섹션 + 흰 본문, 왼쪽 빨간 표식 제목) 디자인
const pptxgen = require("pptxgenjs");
const path = require("path");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.title = "[CODE]_서브웨이 본선 발표";

const RED = "8B0000", INK = "1A1A1A", MUTE = "6B6B6B", CARD = "F2F2F2", LINE = "BFBFBF", WHITE = "FFFFFF", PINK = "F6E3E3";
const KR = "Pretendard SemiBold";
// 글꼴 자체가 SemiBold 라 굵게(b) 속성을 또 주면 가짜 굵기가 덧씌워진다 → 모든 글자에서 bold 를 빼고 글꼴을 통일
const noBold = (o) => { if (!o) return o; const c = Object.assign({}, o); delete c.bold; c.fontFace = KR; return c; };
const fixRuns = (t) => Array.isArray(t) ? t.map((r) => Array.isArray(r) ? fixRuns(r) : (r && typeof r === "object" ? Object.assign({}, r, { options: noBold(r.options || {}) }) : r)) : t;
const _addSlide = pres.addSlide.bind(pres);
pres.addSlide = function () {
  const s = _addSlide.apply(null, arguments);
  const at = s.addText.bind(s), tb = s.addTable.bind(s);
  s.addText = (t, o) => at(fixRuns(t), noBold(o));
  s.addTable = (rows, o) => tb(fixRuns(rows), o);
  return s;
};
const IMG = (n) => path.join(__dirname, "img", n);
let pageNo = 0;

function pageNum(s, dark) {
  pageNo += 1;
  s.addText(String(pageNo), { x: 9.3, y: 0.12, w: 0.5, h: 0.25, fontFace: KR, fontSize: 9, bold: true, color: dark ? WHITE : INK, align: "right", margin: 0, isTextBox: true });
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
  s.addText(String(num), { x: 5.2, y: 0.6, w: 4.8, h: 5.4, fontFace: KR, fontSize: 400, bold: true, color: WHITE, align: "right", valign: "middle", margin: 0, isTextBox: true });
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
  s.addText(n, { x, y, w: 0.34, h: 0.34, fontFace: KR, fontSize: 10, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0, isTextBox: true });
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
  txt(s, "소비기한 추출 파이프라인과 중고거래 게시글 적용", 0.95, 1.88, 8.6, 0.55, { fontSize: 20, bold: true, color: WHITE, valign: "middle" });
  txt(s, "4코어 CPU · GPU 없음 · 오프라인 환경에서의 경량 OCR 설계와 검증", 0.95, 2.7, 8.3, 0.35, { fontSize: 13, color: WHITE });
  txt(s, "제3회 ITDA 연합학술제 본선  |  [CODE]_서브웨이", 0.95, 4.35, 8.3, 0.3, { fontSize: 12, color: WHITE });
  txt(s, "민섭 · 서현 · 병철 · 승아 · 서영", 0.95, 4.68, 8.3, 0.3, { fontSize: 12, color: WHITE });
  pageNum(s, true);
  s.addNotes("안녕하세요, CODE 서브웨이 팀입니다. 저희는 상품 뒷면 사진에서 소비기한을 읽는 OCR을 만들었습니다. 오늘 드릴 말씀의 핵심은 제목 그대로입니다. 저희 시스템은 잘 읽는 것만큼, 못 읽었을 때 못 읽었다고 말하는 것을 중요하게 설계했습니다. 왜 그렇게 했는지, 그리고 그 설계가 중고거래 서비스에서 어떤 의미인지 10분 동안 말씀드리겠습니다.");
}

// ───────────────────────── 2. 섹션 1
section(1, "문제 정의", "무엇을, 어떤 제약 아래에서 풀었는가").addNotes("먼저 문제와 제약입니다.");

// 3. 제약이 설계를 정했다
{
  const s = content("출발점 : ", "제약이 설계를 결정했다");
  const items = [["3,352장", "정답 라벨 없음", "상품 뒷면 사진만 제공. 정확도를 잴 기준부터 직접 만들어야 했다"],
                 ["4코어 CPU", "GPU 없음 · 오프라인", "채점 서버 Ubuntu 22.04, RAM 8GB. 무거운 모델·외부 API 사용 불가"],
                 ["2,500초", "500장 제한 시간", "초과하면 결과 파일이 나오지 않아 정확도까지 0점. 장당 5초가 상한"]];
  items.forEach((it, i) => {
    const x = 0.3 + i * 3.18;
    card(s, x, 1.05, 3.04, 2.45);
    txt(s, it[0], x + 0.2, 1.22, 2.64, 0.7, { fontFace: KR, fontSize: 34, bold: true, color: RED, valign: "middle" });
    txt(s, it[1], x + 0.2, 1.95, 2.64, 0.35, { fontSize: 13.5, bold: true });
    txt(s, it[2], x + 0.2, 2.4, 2.64, 1.0, { fontSize: 12, color: MUTE });
  });
  txt(s, rich(["EasyOCR 탐지기를 쓴 초기 구성은 4코어에서 ", ["장당 5.8초, 500장 2,905초"], " 로 한도를 넘겼다"]), 0.3, 3.85, 9.4, 0.3, { fontSize: 12.5, align: "center" });
  txt(s, rich(["정확도를 올리기 전에 ", ["\"끝까지 돌아가는가\""], " 부터 풀어야 하는 문제였다"]), 0.3, 4.2, 9.4, 0.3, { fontSize: 12.5, align: "center" });
  strip(s, ["그래서 모든 설계 결정에 ", ["정확도와 시간을 함께"], " 기록했다"], 4.75);
  s.addNotes("이 대회는 세 가지 제약이 있었습니다. 첫째, 사진 3,352장에 정답이 없습니다. 둘째, 채점 서버는 GPU 없는 4코어 CPU이고 인터넷이 끊겨 있습니다. 셋째, 500장을 2,500초 안에 끝내야 하고, 넘기면 결과 파일 자체가 안 나와 정확도까지 0점입니다. 초기 구성은 500장에 2,905초가 걸려 이미 탈락이었습니다. 그래서 정확도보다 먼저, 끝까지 돌아가는 구조에서 출발했습니다.");
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
  txt(s, "도트 인쇄·각인·두 날짜 병기 위주 489장 촬영, 389장 라벨링. 한 번도 본 적 없는 시험지로 사용", 0.72, 3.8, 4.0, 0.7, { fontSize: 11, color: MUTE });

  card(s, 5.0, 1.05, 4.7, 3.5);
  txt(s, "데이터 분리", 5.2, 1.15, 4.3, 0.3, { fontSize: 12.5, bold: true });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.55, w: 0.64, h: 0.55, fill: { color: RED }, line: { color: RED, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.84, y: 1.55, w: 3.66, h: 0.55, fill: { color: "BDBDBD" }, line: { color: "BDBDBD", width: 0 } });
  txt(s, "500", 5.2, 1.55, 0.64, 0.55, { fontFace: KR, fontSize: 12, bold: true, color: WHITE, align: "center", valign: "middle" });
  txt(s, "2,852", 5.84, 1.55, 3.66, 0.55, { fontFace: KR, fontSize: 12, bold: true, color: INK, align: "center", valign: "middle" });
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
    if (i < steps.length - 1) txt(s, "▶", x + 1.4, 1.5, 0.2, 0.3, { fontFace: KR, fontSize: 10, color: MUTE, align: "center", valign: "middle" });
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
    txt(s, r[0], x + 0.15, 1.5, 1.96, 0.62, { fontFace: KR, fontSize: 32, bold: true, color: RED, valign: "middle" });
    txt(s, r[1], x + 0.15, 2.12, 1.96, 0.3, { fontSize: 13, bold: true });
    txt(s, r[2], x + 0.15, 2.42, 1.96, 0.45, { fontSize: 10.5, color: MUTE });
    txt(s, r[3], x + 0.15, 2.9, 1.96, 0.55, { fontSize: 10.5, bold: true, color: INK });
  });
  txt(s, "단계마다 처방이 다르다", 0.3, 3.68, 9.4, 0.3, { fontSize: 12.5, bold: true });
  txt(s, [{ text: "\"읽었다가 지움\" 111장은 모델이 아니라 코드 로직의 문제 → 1차 후보를 지우지 못하게 해 +53 / −5", options: { bullet: true, breakLine: true } },
          { text: "\"못 읽음\" 은 해상도를 올려도 회복되지 않았다 (5가지 구성 전부 ±1%p, 시간만 +30~50%) → 원인은 탐지가 아니라 인식 품질", options: { bullet: true } }], 0.3, 3.98, 9.4, 0.7, { fontSize: 11, paraSpaceAfter: 3 });
  strip(s, ["오답을 뭉뚱그려 \"모델을 키우자\" 가 아니라, ", ["원인별로 가장 싼 처방"], " 을 골랐다"], 4.75);
  s.addNotes("본선에서 가장 먼저 한 일은 오답 진단입니다. 오답 603장마다 정답 날짜가 어느 단계까지 살아 있었는지를 추적했더니 네 가지로 갈렸습니다. 못 읽은 것 183장, 잘못 읽은 것 290장, 그리고 흥미로운 게 세 번째입니다. 처음엔 맞게 읽었는데 다시 읽기 단계가 그 정답을 지워 버린 게 111장이었습니다. 이건 모델 문제가 아니라 저희 코드의 문제였고, 다시 읽기는 교정만 하고 삭제는 못 하게 규칙을 바꿔서 53장을 되찾았습니다. 이렇게 원인을 나눠 놓으니, 모델을 키우는 대신 원인마다 가장 싼 처방을 고를 수 있었습니다.");
}

// 9. 후처리: 소비기한 vs 다른 숫자
{
  const s = content("후처리 규칙 : ", "소비기한을 다른 숫자와 구분하는 법");
  table(s, [["구분 대상", "실제 예", "규칙", "근거"],
            ["품목보고번호 · 바코드", "20130628332176", "9자리 이상 숫자열은 통째로 제거", "앞 8자리가 완전한 날짜 형식"],
            ["영양성분표 · 중량", "78 7 5 31 / 30.4 GRAMS", "신뢰 등급 : 완전 날짜 > 공백·압축 > 연월 > 월일", "잡음이 이긴 오답 15장에서 도출"],
            ["제조일자 · 유통기한", "25.06.26  /  26.06.25", "가장 좋은 등급 안에서 가장 늦은 날짜", "소비기한 ≥ 유통기한 ≥ 제조일"],
            ["시각 · 로트번호", "13:11  /  A03  /  L8", "날짜 패턴에서 제외, 옆 글자를 '일' 자리로 읽지 않음", "도트 인쇄 제품에 흔함"],
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
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 9, dataLabelColor: INK, dataLabelFontFace: KR, dataLabelFormatCode: "0.0",
    catAxisLabelFontSize: 8, catAxisLabelFontFace: KR, catAxisLabelColor: MUTE, catAxisLabelRotate: 315, valAxisLabelFontSize: 8, valAxisLabelColor: MUTE, valAxisMinVal: 30, valAxisMaxVal: 95,
    valGridLine: { color: "E3E3E3", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, showTitle: false });
  txt(s, "※ 앞 세 단계는 개발용 133장, 이후는 500장 기준", 0.4, 4.45, 6, 0.22, { fontSize: 8.5, color: MUTE });
  card(s, 6.6, 0.95, 3.1, 1.45);
  txt(s, "봉인 500장 · 완전일치", 6.78, 1.02, 2.8, 0.26, { fontSize: 10.5, color: MUTE });
  txt(s, "86.2%", 6.78, 1.26, 2.8, 0.62, { fontFace: KR, fontSize: 34, bold: true, color: RED, valign: "middle" });
  txt(s, "예선 제출본 84.2% → +2.0%p", 6.78, 1.9, 2.8, 0.4, { fontSize: 10.5 });
  table(s, [["구분", "정확도"], ["필드 평균 (채점 방식)", { text: "90.8%", bold: true, red: true }], ["작은 사진 (≤700px)", "83.7%"], ["중간", "89.5%"], ["큰 사진", "86.7%"], ["두 날짜 병기", "78.4%"], ["미인식률", "3.0%"]],
        6.6, 2.52, 3.1, [2.0, 1.1], { fontSize: 10, rowH: 0.29 });
  strip(s, ["판정용 2,852장에서도 ", ["82.3 → 86.7%"], " : 튜닝에 쓴 셋과 봉인 셋이 함께 올랐다"], 4.75);
  s.addNotes("결과입니다. 처음 39%에서 출발해서 예선 제출 때 84.2%, 본선 통합본은 봉인 500장에서 86.2%입니다. 연월일을 따로 채점하는 필드 평균으로는 90.8%입니다. 가장 큰 도약은 탐지기와 인식기를 교체한 구간인데, 속도 때문에 한 결정이 정확도까지 올린 경우입니다. 튜닝에 쓴 2,852장에서는 82.3에서 86.7로 올랐고, 한 번도 보지 않은 봉인 셋에서도 같이 올랐기 때문에 튜닝 셋에 과적합된 상승이 아니라고 판단합니다.");
}

// 12. 채택/기각
{
  const s = content("모델·대안 비교 : ", "점수가 올라도 기각한 것들");
  table(s, [["시도", "결과 (회복 / 퇴보)", "판단", "이유"],
            ["탐지·인식기 PP-OCRv5 mobile 로 교체", "39.1 → 67.7%, 5.8 → 1.8초", { text: "채택", bold: true, red: true }, "속도 한도와 정확도를 동시에 해결"],
            ["다시 읽기 규칙 (1차 후보를 지우지 못하게 등)", "+63 / −5", { text: "채택", bold: true, red: true }, "82.3 → 84.3%. 코드 로직 결함 수정"],
            ["해석 규칙 4개", "+39 / −2", { text: "채택", bold: true, red: true }, "병기 64.9 → 78.3%"],
            ["주변 재탐지 · 확대 재시도 · 파인튜닝 재시도", "+25 / −1", { text: "채택", bold: true, red: true }, "못 읽은 사진에만 비용을 쓴다"],
            ["파인튜닝 인식기를 다시 읽기에", "+86 / −64", "기각", "점수가 올라도 맞던 답을 흔들면 버린다"],
            ["합성 도트 글자 3,000장 추가 학습", "정밀도 84 → 81%", "기각", "진짜 글씨를 대충 읽게 됨"],
            ["인식기 셋 다수결", "+8 / −4, 장당 +0.43초", "기각", "퇴보가 회복의 1/3 초과"],
            ["탐지 해상도 상향", "±1%p, 시간 +30~50%", "기각", "원인이 해상도가 아님"],
            ["한국어 인식기로 한 번 더 읽기", "판정용 +7 / −2, 장당 +0.3~0.7초", "기본 끔", "시간이 한도의 94% 까지 차서 여유를 택함"]],
        0.3, 1.0, 9.4, [3.0, 2.4, 0.8, 3.2], { fontSize: 9.8, rowH: 0.345 });
  strip(s, ["파인튜닝은 점수를 올렸지만 ", ["퇴보 64장"], " 때문에 버렸다. 채택 기준이 점수보다 먼저다"], 4.75);
  s.addNotes("저희가 시도한 것 중 절반은 버렸습니다. 대표적인 게 파인튜닝입니다. 저희 라벨로 학습시킨 인식기를 다시 읽기 단계에 썼더니 점수는 올랐습니다. 그런데 새로 맞힌 게 86장, 새로 틀린 게 64장이었습니다. 전체 점수는 올랐지만 잘 맞히던 사진 64장을 망가뜨린 겁니다. 그래서 기각했고, 기존 인식기가 못 읽은 사진에만 쓰는 방식으로 넣어 퇴보 없이 7장을 얻었습니다. 합성 데이터도, 해상도 상향도 같은 기준으로 버렸습니다.");
}

// 13. 속도
{
  const s = content("속도·효율 : ", "한도의 55 ~ 79%, 그리고 완주 보장");
  const k = [["2.7 ~ 4.0초", "장당 처리 시간", "개발 PC 두 대, 4스레드"], ["1,370 ~ 1,985초", "500장", "한도 2,500초의 55 ~ 79%"], ["1.25GB", "최대 메모리", "한도 8GB (40장 실측)"], ["0원", "학습 비용", "무료 Colab T4 만 사용"]];
  k.forEach((r, i) => {
    const x = 0.3 + i * 2.38;
    card(s, x, 1.02, 2.26, 1.3);
    txt(s, r[0], x + 0.15, 1.08, 2.06, 0.55, { fontFace: KR, fontSize: r[0].length > 8 ? 18 : 24, bold: true, color: RED, valign: "middle" });
    txt(s, r[1], x + 0.15, 1.63, 1.96, 0.28, { fontSize: 11.5, bold: true });
    txt(s, r[2], x + 0.15, 1.9, 1.96, 0.3, { fontSize: 10, color: MUTE });
  });
  txt(s, "속도를 만든 결정", 0.3, 2.5, 4.6, 0.3, { fontSize: 12.5, bold: true });
  txt(s, [{ text: "탐지는 640px 축소본에서 장당 1회 (탐지 비용 = 픽셀 수)", options: { bullet: true, breakLine: true } },
          { text: "인식은 큰 글자부터, 날짜를 찾으면 잔글씨 생략", options: { bullet: true, breakLine: true } },
          { text: "사진의 88% 는 1.8초에 끝나고, 재시도까지 간 12% 가 시간의 절반을 쓴다", options: { bullet: true, breakLine: true } },
          { text: "다시 읽기는 후보 줄 크롭만, 폴백은 후보 없는 장에만", options: { bullet: true } }], 0.3, 2.8, 4.6, 1.6, { fontSize: 10.8, paraSpaceAfter: 4 });
  card(s, 5.1, 2.5, 4.6, 2.05);
  txt(s, "시간 예산 가드 : 3단계 자동 경량화", 5.25, 2.57, 4.3, 0.3, { fontSize: 12, bold: true });
  txt(s, "최근 20장 속도로 총 소요를 예측, 2,000초를 넘길 것 같으면", 5.25, 2.87, 4.3, 0.3, { fontSize: 10.5, color: MUTE });
  [["1", "재시도 단계 생략"], ["2", "다시 읽기 생략"], ["3", "남은 장 NONE, 결과 파일은 반드시 생성"]].forEach((r, i) => {
    badge(s, r[0], 5.25, 3.25 + i * 0.4); txt(s, r[1], 5.68, 3.25 + i * 0.4, 3.9, 0.34, { fontSize: 11, valign: "middle" });
  });
  strip(s, ["채점 서버 속도를 모르는 상황에서 ", ["\"느리면 0점\""], " 을 구조로 막았다"], 4.75);
  s.addNotes("속도입니다. 개발 PC 두 대에서 스레드를 4개로 제한해 쟀을 때 장당 2.7초에서 4초, 500장에 한도의 55에서 79퍼센트입니다. 메모리는 1.25기가, 학습은 무료 코랩만 써서 비용이 0원입니다. 탐지는 줄인 사진에서 한 번만 하고, 인식은 큰 글자부터 읽다가 날짜를 찾으면 멈춥니다. 오른쪽이 시간 가드입니다. 채점 서버가 얼마나 빠른지 저희는 모릅니다. 그래서 속도를 지켜보다가 늦을 것 같으면 단계적으로 가벼워지고, 최악의 경우에도 결과 파일은 반드시 나오게 했습니다.");
}

// 14. 시연 캡처
{
  const s = content("실행 화면 : ", "실제 파이프라인 출력");
  const demos = [["demo_plain.png", "일반 인쇄"], ["demo_two.png", "제조·소비 병기"], ["demo_dot.png", "도트 인쇄 (폴백)"], ["demo_none.png", "미인식 → 판매자 입력"]];
  demos.forEach((d, i) => {
    const x = 0.3 + i * 2.38;
    s.addImage({ path: IMG(d[0]), x, y: 1.0, w: 2.26, h: 2.142 });
    txt(s, d[1], x, 3.2, 2.26, 0.3, { fontSize: 11.5, bold: true, align: "center" });
  });
  card(s, 0.3, 3.62, 9.4, 1.0);
  txt(s, [{ text: "빨간 상자 = 선택된 날짜 줄, 회색 상자 = 다른 후보. 아래 패널은 파이프라인이 실제로 낸 값·후보·처리 시간", options: { bullet: true, breakLine: true } },
          { text: "병기 사진 : 25.06.26(제조)과 26.06.25(소비)를 모두 읽고 늦은 날짜를 선택", options: { bullet: true, breakLine: true } },
          { text: "네 번째 : 후보가 없으면 날짜를 지어내지 않고 NONE. 게시 화면에서는 빈칸으로 두고 판매자가 입력한다", options: { bullet: true } }], 0.45, 3.68, 9.1, 0.9, { fontSize: 10.5, paraSpaceAfter: 3 });
  strip(s, ["재현 : 새 환경에서 ", ["설치 → 가중치 다운로드 → Run All"], " 검증, Ubuntu·Python 3.10·오프라인 자동 테스트 통과"], 4.75);
  s.addNotes("실제 실행 화면입니다. 두 번째가 제조일자와 소비기한이 같이 찍힌 경우입니다. 25년 6월 26일과 26년 6월 25일을 둘 다 읽고 늦은 쪽을 골랐습니다. 세 번째는 도트 인쇄인데, 처음엔 못 읽었다가 점을 이어 붙이는 전처리 후에 읽어 낸 경우입니다. 그리고 네 번째를 일부러 넣었습니다. 못 읽은 사진입니다. 저희 시스템은 여기서 날짜를 지어내지 않고 NONE을 냅니다. 이 선택이 다음에 말씀드릴 중고거래 적용의 핵심입니다.");
}

// ───────────────────────── 15. 섹션 5
section(5, "도메인 적용과 운영", "중고거래 식품 게시글의 잔여기한").addNotes("마지막으로 서비스 적용입니다.");

// 16. 도메인: 중고거래 소비기한 (시연 화면은 발표/dashboard 캡처에서 폰 부분을 자른 것)
{
  const s = content("적용 도메인 : ", "중고거래 식품·건강기능식품 게시글의 소비기한");
  txt(s, rich(["소비기한은 판매자가 손으로 적는다. 적발된 위반 375건 중 ", ["211건이 사용기한 확인 불가·불일치"], ", 전담 모니터링 인력은 ", ["5명"]]), 0.3, 0.93, 9.4, 0.27, { fontSize: 10.8 });
  txt(s, "아래는 시연용으로 만든 서비스 화면(설계안)이며 실제 앱을 구현한 것은 아니다. 사진·판독값·확신도는 우리 파이프라인의 실제 출력이다", 0.3, 1.19, 9.4, 0.2, { fontSize: 9, color: MUTE });
  const ph = [["dash_phone1.png", "① 날짜면 촬영"], ["dash_phone2.png", "② 확신하면 자동 입력"], ["dash_phone3.png", "③ 확신이 낮으면 빈칸"], ["dash_phone4.png", "④ 날짜·남은 일수·원본"]];
  ph.forEach((p, i) => {
    const x = 0.3 + i * 1.66;
    s.addImage({ path: IMG(p[0]), x, y: 1.42, w: 1.432, h: 3.0 });
    txt(s, p[1], x - 0.1, 4.44, 1.632, 0.26, { fontSize: 9.5, bold: true, align: "center", valign: "middle" });
    if (i < 3) txt(s, "▶", x + 1.432, 2.77, 0.228, 0.3, { fontFace: KR, fontSize: 9, color: MUTE, align: "center", valign: "middle" });
  });
  txt(s, "모델 결과별로 판매자에게 일어나는 일", 6.95, 1.42, 2.75, 0.28, { fontSize: 11, bold: true });
  table(s, [["모델 결과", "판매자에게 일어나는 일"],
            ["맞게 읽음", "채워진 날짜를 확인"],
            ["못 읽음 · 확신 낮음", "빈칸. 손으로 입력 (지금과 같음)"],
            ["이르게 읽음", "확대본을 보고 고침"],
            [{ text: "늦게 읽음", hl: true, red: true }, { text: "확대본을 보고 고침. 안 고치면 남은 날이 많게 표시", hl: true }]],
        6.95, 1.74, 2.75, [0.95, 1.8], { fontSize: 8.8, rowH: 0.36 });
  card(s, 6.95, 3.78, 2.75, 0.92);
  txt(s, rich(["판매자가 마지막에 확인하므로 정확도는 안전성이 아니라 ", ["자동 입력 비율"], " 을 정한다. 속이려는 소수는 기존 사후 모니터링이 맡는다"]), 7.07, 3.82, 2.51, 0.84, { fontSize: 9.3, valign: "middle" });
  strip(s, ["포장 판독과 사진 기반 자동 입력은 각각 이미 있다. 우리는 둘을 ", ["게시 흐름에서 잇는 빈자리"], " 를 채운다"], 4.75);
  s.addNotes("적용 대상은 중고거래 플랫폼의 식품과 건강기능식품 게시글입니다. 소비기한은 판매자가 손으로 적고 구매자는 확인할 방법이 없습니다. 약사 단체 모니터링에서 적발된 위반 중 가장 많은 유형이 사용기한 확인 불가였고, 게시글은 한 달에 2만 4천 건인데 전담 모니터링 인력은 다섯 명으로 보도됐습니다. 화면은 시연용 설계안이고, 실제 앱을 만든 것은 아닙니다. 판매자가 날짜면을 찍으면 서버가 읽고, 확신할 때만 날짜 칸을 채웁니다. 확신이 낮으면 읽은 값을 보여 주지 않고 빈칸으로 둡니다. 게시글에는 읽은 날짜와 남은 일수, 날짜면 원본이 붙습니다. 판매자가 마지막에 확인하므로 모델이 틀려도 한 번 고치면 끝나고, 못 읽으면 빈칸이니 지금보다 나빠지지 않습니다. 그래서 정확도는 안전성이 아니라 자동 입력 비율을 정합니다. 플랫폼에는 사진을 읽어 글을 자동으로 써 주는 기능이 이미 있습니다. 저희는 소비기한 판독을 그 게시 흐름에 잇습니다.");
}

// 17. 운영 구조·비용
{
  const s = content("운영 구조와 비용 : ", "건당 0.2 ~ 5.8원, 도입 이유는 규제 대응");
  table(s, [["항목", "내용"],
            ["1차 대상", "건강기능식품 카테고리 (미개봉 · 소비기한 이내 · 연 10회 이하)"],
            ["규모", "게시글 월 약 2.4만 건, 하루 약 800건 (식약처 자료)"],
            ["구조", "플랫폼 서버에서 추론. 모델 21MB, CPU 전용, 10초 제한"],
            ["서버", "하루 53분 ~ 2.4시간 = 서버 1대의 4 ~ 10%"],
            [{ text: "비용", bold: true }, { text: "게시글 한 건당 0.2 ~ 5.8원. 라이선스·GPU·학습비 0원", bold: true, red: true }]],
        0.3, 1.0, 5.6, [1.0, 4.6], { fontSize: 9.8, rowH: 0.34 });
  card(s, 6.1, 1.0, 3.6, 2.05);
  txt(s, "도입 이유 : 비용 절감이 아니다", 6.25, 1.07, 3.3, 0.28, { fontSize: 12, bold: true });
  txt(s, [{ text: "위반 처리비 절감으로는 본전이 안 된다 : 손익분기 780 ~ 1,900원, 사람 검토는 약 86원 (가정)", options: { bullet: true, breakLine: true } },
          { text: "건강기능식품 개인 간 거래는 시범사업. 게시글마다 남는 사진과 판독 기록이 관리 체계의 증거", options: { bullet: true, breakLine: true } },
          { text: "남은 일수 표시·자동 숨김은 날짜 칸만으로 되므로 OCR 효과로 세지 않았다", options: { bullet: true } }], 6.25, 1.37, 3.3, 1.62, { fontSize: 9.8, paraSpaceAfter: 3 });
  txt(s, "자동 입력 기준 (직접 찍은 폰 사진 389장 실측)", 0.3, 3.15, 9.4, 0.28, { fontSize: 12, bold: true });
  table(s, [["자동 입력 기준", "채워지는 비율", "채운 값의 정확도", "틀린 값을 받는 판매자"],
            ["기준 없음 (읽히면 채움)", "70.2%", "70.3%", "20.8%"],
            ["확신도 0.7 이상", "44.7%", "77.0%", "10.3%"],
            [{ text: "확신도 0.7 이상 + 10초 제한 (운영 기준)", hl: true }, { text: "40.6%", hl: true }, { text: "79.7%", hl: true }, { text: "8.2%", hl: true, red: true }],
            ["확신도 0.9 이상", "16.5%", "87.5%", "2.1%"]],
        0.3, 3.43, 9.4, [3.4, 2.0, 2.0, 2.0], { fontSize: 9.6, rowH: 0.245 });
  strip(s, ["OCR 이 있어야 되는 것 : ", ["입력값과 사진의 대조"], ", 날짜면이 찍혔는지 확인, 자동 입력과 수정값 축적"], 4.75);
  s.addNotes("1차 대상은 위반 통계가 공개된 건강기능식품 카테고리이고, 게시글은 하루 800건 정도입니다. 서버 한 대의 4에서 10퍼센트면 되고, 게시글 한 건당 0.2원에서 5.8원입니다. 아래 표는 직접 찍은 폰 사진 389장으로 잰 값입니다. 읽히는 대로 채우면 판매자 다섯 명 중 한 명이 틀린 값을 받습니다. 확신도 0.7 이상이고 10초 안에 읽힌 것만 채우면 41퍼센트가 자동으로 채워지고 틀린 값은 8퍼센트로 줄어듭니다. 이익은 부풀리지 않았습니다. 위반 처리비 절감만으로는 본전이 되지 않는다는 계산을 먼저 공개합니다. 플랫폼이 도입할 이유는 규제 대응입니다. 건강기능식품 개인 간 거래는 아직 시범사업이고, 게시글마다 남는 날짜 사진과 판독 기록이 관리 체계의 증거가 됩니다.");
}

// 17-1. 운영 아키텍처 (서버 / 온디바이스)
{
  const s = content("운영 아키텍처 : ", "서버는 지금, 온디바이스는 다음 단계");
  card(s, 0.3, 1.0, 4.6, 3.35);
  txt(s, "지금 — 서버 추론", 0.45, 1.1, 4.3, 0.3, { fontSize: 13, bold: true, color: RED });
  txt(s, [{ text: "판매자가 제목·가격을 쓰는 동안 서버가 사진을 읽는다", options: { bullet: true, breakLine: true } },
          { text: "확신도 0.7 이상이고 10초 안에 읽혀야 칸을 채운다. 아니면 빈칸", options: { bullet: true, breakLine: true } },
          { text: "모델이 21MB라 가볍다. GPU도 외부 API도 필요 없고, 사진은 서버 밖으로 안 나간다", options: { bullet: true, breakLine: true } },
          { text: "서버 한 대로 충분하다. 지금 쓰는 양은 그중 4 ~ 10%뿐이다", options: { bullet: true } }],
      0.45, 1.46, 4.3, 2.75, { fontSize: 10.3, paraSpaceAfter: 5 });
  card(s, 5.1, 1.0, 4.6, 3.35, PINK);
  txt(s, "다음 — 온디바이스 (폰 자체 추론)", 5.25, 1.1, 4.3, 0.3, { fontSize: 13, bold: true, color: RED });
  txt(s, [{ text: "폰 안에서 직접 돌리는 건 아직 안 해 봤다", options: { bullet: true, breakLine: true } },
          { text: "모델이 작아서 될 것 같긴 하지만, 그건 추측이지 잰 값이 아니다", options: { bullet: true, breakLine: true } },
          { text: "폰에서 장당 몇 초가 걸리는지, 배터리는 얼마나 쓰는지부터 재야 한다", options: { bullet: true, breakLine: true } },
          { text: "되면 서버 비용이 거의 사라지고, 사진도 폰 밖으로 안 나간다", options: { bullet: true } }],
      5.25, 1.46, 4.3, 2.75, { fontSize: 10.3, paraSpaceAfter: 5 });
  strip(s, ["지금 돌아가는 건 서버 추론 하나뿐이다. ", ["온디바이스는 가능성일 뿐, 된다고 말한 적 없다"]], 4.55);
  s.addNotes("운영 아키텍처입니다. 지금은 서버 추론 하나만 돌아갑니다. 모델이 21메가바이트로 작아 폰 안에서 직접 돌리는 온디바이스도 가능할 걸로 보지만, 아직 재 보지 않아 다음 단계로 남겨 뒀습니다.");
}

// 17-2. 손실 절감과 ROI
{
  const s = content("손실 절감과 ROI : ", "비용 절감으로는 본전이 안 된다");
  txt(s, "OCR이 있어야 되는 것 / 날짜 칸만 있으면 되는 것", 0.3, 1.0, 9.4, 0.28, { fontSize: 12, bold: true });
  table(s, [["편익", "누구에게", "OCR 필요?", "근거"],
            ["입력값과 사진의 대조", "구매자 · 플랫폼", { text: "예", red: true }, "틀린 입력이 판독값과 우연히 같아 지나갈 확률 0.2 ~ 0.4%"],
            ["날짜면이 찍혔는지 확인", "구매자", { text: "예", red: true }, "메루카리는 이 확인을 사람이 한다"],
            ["입력 편의 · 판매자 수정값 축적", "판매자 · 플랫폼", { text: "예", red: true }, "폰 사진 기준 자동 입력 41 ~ 45%"],
            ["남은 일수 표시 · 기한 지난 글 자동 숨김", "구매자 · 플랫폼", "아니오", "날짜 칸만 있으면 됨 — OCR 편익으로 세지 않음"]],
        0.3, 1.3, 9.4, [2.7, 1.7, 1.1, 3.9], { fontSize: 9.6, rowH: 0.34 });
  txt(s, "손익분기 : 위반 처리비 절감만으로는 본전이 안 된다", 0.3, 3.1, 9.4, 0.28, { fontSize: 12, bold: true });
  table(s, [["조건", "연간 위반(가정 50% 포착)", "연간 서버비", "손익분기 1건당 처리비"],
            ["20개월 평균, 기존 서버 여유분", "435건", "17만원", "약 780원"],
            ["거래조건 강화 뒤 추정, 기존 서버 여유분", "180건", "17만원", "약 1,900원"],
            [{ text: "거래조건 강화 뒤 추정, 전용 서버", hl: true }, { text: "180건", hl: true }, { text: "169만원", hl: true }, { text: "약 1만 9천원", hl: true, red: true }]],
        0.3, 3.38, 9.4, [3.0, 2.2, 2.0, 2.2], { fontSize: 9.6, rowH: 0.3 });
  strip(s, ["사람이 30초 검토하면 약 86원. 손익분기 처리비는 이보다 ", ["9 ~ 220배 크다"], " — 도입 이유는 비용 절감이 아니라 규제 대응이다"], 4.75);
  s.addNotes("손실 절감과 ROI입니다. 손익분기 처리비가 사람 검토 비용 86원의 9배에서 220배라, 저희는 비용 절감이 아니라 규제 대응을 도입 이유로 듭니다.");
}

// 18. 한계
{
  const s = content("한계 : ", "폰 사진에서는 다섯 장 중 한 장을 못 읽는다");
  card(s, 0.3, 1.0, 4.6, 2.2);
  txt(s, "틀리는 방향 (직접 찍은 폰 사진 389장)", 0.45, 1.07, 4.3, 0.28, { fontSize: 12, bold: true });
  s.addChart(pres.charts.BAR, [{ name: "비율(%)", labels: ["늦게 읽음 (남은 날이 많게 표시)", "이르게 읽음", "못 읽음 → 빈칸"], values: [4.9, 15.8, 21.9] }], {
    x: 0.4, y: 1.35, w: 4.4, h: 1.8, barDir: "bar", chartColors: [RED, "9A9A9A", "5A5A5A"], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelFontFace: KR, dataLabelColor: INK, dataLabelFormatCode: "0.0",
    catAxisLabelFontSize: 9, catAxisLabelFontFace: KR, catAxisLabelColor: INK, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 30, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, showTitle: false });
  card(s, 5.1, 1.0, 4.6, 2.2);
  txt(s, "남은 한계", 5.25, 1.07, 4.3, 0.28, { fontSize: 12, bold: true });
  txt(s, [{ text: "못 읽음 21.9% 는 봉인 500장(3.0%)의 약 일곱 배. 찍은 사람과 촬영 조건에 따라 크게 갈린다", options: { bullet: true, breakLine: true } },
          { text: "389장은 어려운 유형 위주로 찍은 것. 실제 게시 사진으로 다시 재야 한다", options: { bullet: true, breakLine: true } },
          { text: "조작·개봉 여부·카테고리를 바꿔 촬영을 피하는 것은 막지 못한다", options: { bullet: true, breakLine: true } },
          { text: "판매자가 보지 않고 확인을 누르는 비율은 재지 못했다", options: { bullet: true } }], 5.25, 1.37, 4.3, 1.78, { fontSize: 10, paraSpaceAfter: 3 });
  txt(s, "보완 계획", 0.3, 3.38, 9.4, 0.3, { fontSize: 12.5, bold: true });
  [["01", "촬영 단계에서 막는다", "촬영 안내와 해상도·흐림 검사, 미달이면 다시 촬영"], ["02", "판매자 수정값으로 재학습", "고친 값을 검수해 인식기 학습 데이터로"], ["03", "확인을 동작으로", "버튼 대신 날짜의 '일' 칸을 다시 입력. 실제 수정 비율을 지표로"]].forEach((r, i) => {
    const x = 0.3 + i * 3.18;
    badge(s, r[0], x, 3.75); txt(s, r[1], x + 0.42, 3.72, 2.6, 0.3, { fontSize: 11.5, bold: true, valign: "middle" });
    txt(s, r[2], x + 0.42, 4.02, 2.6, 0.6, { fontSize: 10, color: MUTE });
  });
  strip(s, ["규칙으로 닿는 오답은 거의 다 썼다. 남은 것은 ", ["인식 품질(각인·도트)과 저해상도"], " 다"], 4.75);
  s.addNotes("한계입니다. 판매자가 폰으로 찍는 사진이 저희 약점입니다. 팀원 네 명이 어려운 유형 위주로 389장을 직접 찍어 돌렸더니 다섯 장 중 한 장은 읽지 못했습니다. 봉인 500장의 일곱 배입니다. 가장 위험한 것은 늦게 읽어서 남은 날이 많게 표시되는 경우로 4.9퍼센트입니다. 그래서 채운 값 옆에 늘 날짜 확대본을 보여 주고, 읽은 값만으로 게시를 막지 않습니다. 조작과 개봉 여부는 막지 못하고, 판매자가 보지 않고 확인을 누르는 비율은 재지 못했습니다.");
}

// 19. 확장
{
  const s = content("확장성 : ", "\"제품에 찍힌 기한\" 을 읽는 모든 곳");
  table(s, [["적용 분야", "읽는 값", "바꿀 것", "그대로 쓰는 것"],
            ["1단계 건강기능식품 → 2단계 가공식품 · 선물세트", "소비기한", "대상 카테고리, 상품별 촬영", "파이프라인 전체"],
            ["품목보고번호 인식 → 제품 조회·회수 확인", "품목보고번호", "9자리 숫자 마스킹 규칙 재설계", "탐지 · 인식 (정확도 미측정)"],
            ["식품공장 출하 전 날짜 인쇄 확인", "소비기한", "대조 대상 (제조일 + 품목별 일수)", "놓칠 확률 한 장당 0.2%"],
            ["의약품 · 화학 제품 출하 표시물", "제조번호 · 사용기한", "표기 형식 규칙", "읽기 · 대조 · 예외 처리"]],
        0.3, 1.0, 9.4, [3.1, 1.8, 2.4, 2.1], { fontSize: 10.1, rowH: 0.38 });
  card(s, 0.3, 3.15, 9.4, 1.45);
  txt(s, "왜 옮겨 쓸 수 있는가", 0.45, 3.22, 9.1, 0.28, { fontSize: 12, bold: true });
  txt(s, [{ text: "딥러닝 모델은 \"글자를 읽는 일\" 만 하고, 도메인 지식은 전부 규칙 문서 한 장에 있다", options: { bullet: true, breakLine: true } },
          { text: "읽기 → 기준값과 대조 → 예외만 사람에게 : 이 세 단계는 분야가 바뀌어도 같다", options: { bullet: true, breakLine: true } },
          { text: "사람(판매자·검수자)이 확정한 값이 다시 학습 데이터가 되는 순환 구조", options: { bullet: true } }], 0.45, 3.52, 9.1, 1.05, { fontSize: 10.8, paraSpaceAfter: 3 });
  strip(s, ["규칙 계층만 바꾸면 되는 구조 : ", ["모델을 다시 만들 필요가 없다"]], 4.75);
  s.addNotes("확장입니다. 뼈대는 읽은 값을 기준값과 대조하고 예외만 사람에게 넘기는 것입니다. 건강기능식품에서 시작해 가공식품과 명절 선물세트로 넓히고, 지금은 잡음으로 지우는 품목보고번호를 읽으면 제품 조회와 회수 대상 확인까지 할 수 있습니다. 같은 파이프라인은 공장의 출하 전 날짜 인쇄 확인이나 의약품 표시물 검증에도 형식 규칙만 바꿔 쓸 수 있습니다.");
}

// 20. 마무리
{
  const s = pres.addSlide(); s.background = { color: RED };
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 0.75, w: 0.08, h: 0.55, fill: { color: WHITE }, line: { color: WHITE, width: 0 } });
  txt(s, "정리", 0.95, 0.72, 8, 0.6, { fontSize: 26, bold: true, color: WHITE, valign: "middle" });
  const pts = [["제약에서 출발", "4코어 CPU · 2,500초 안에서 끝까지 돌아가는 구조. 봉인 500장 86.2%, 한도의 55 ~ 79%"],
               ["검증을 먼저", "전수 라벨링, 봉인 시험지, 회복·퇴보 기준. 점수가 올라도 퇴보가 크면 버렸다"],
               ["틀리는 방식을 설계", "확신이 없으면 NONE, 판매자가 직접 입력. 정확도는 안전성이 아니라 자동 입력 비율이 된다"]];
  pts.forEach((p, i) => {
    const y = 1.7 + i * 1.05;
    s.addShape(pres.shapes.OVAL, { x: 0.95, y: y + 0.03, w: 0.5, h: 0.5, fill: { color: WHITE }, line: { color: WHITE, width: 0 } });
    txt(s, String(i + 1), 0.95, y + 0.03, 0.5, 0.5, { fontFace: KR, fontSize: 16, bold: true, color: RED, align: "center", valign: "middle" });
    txt(s, p[0], 1.65, y - 0.02, 7.6, 0.34, { fontSize: 16, bold: true, color: WHITE, valign: "middle" });
    txt(s, p[1], 1.65, y + 0.32, 7.6, 0.4, { fontSize: 11.5, color: WHITE });
  });
  txt(s, "감사합니다  |  github.com/LEEbyeongchul/itda3-CODE-subway", 0.95, 4.95, 8.3, 0.3, { fontSize: 11, color: WHITE });
  pageNum(s, true);
  s.addNotes("정리하겠습니다. 첫째, 제약에서 출발해 봉인 500장 86.2퍼센트를 제한 시간 안에 냈습니다. 둘째, 검증을 먼저 세웠습니다. 점수가 올라도 잘 맞히던 걸 망가뜨리면 버렸습니다. 셋째, 틀리는 방식을 설계했습니다. 확신이 없으면 못 읽었다고 말하기 때문에, 판매자가 믿고 쓸 수 있습니다. 감사합니다.");
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
            ["판정용 2,852장", "예선 구성 (지금 라벨로 채점)", "82.3%", "", "병기 64.9%"],
            ["판정용 2,852장", "본선 최종 (한국어 인식기 끔)", "86.7%", "", "병기 78.3% · 비병기 87.7%"],
            ["직접 찍은 폰 사진 389장", "본선 최종 (운영 수치 계산용)", "", "", "미인식 21.9%, 자동 입력 41 ~ 45%"]],
        0.3, 1.0, 9.4, [1.7, 3.0, 1.2, 1.2, 2.3], { fontSize: 10, rowH: 0.36 });
  txt(s, [{ text: "완전일치 : 연·월·일이 모두 맞은 사진 비율", options: { bullet: true, breakLine: true } },
          { text: "필드평균 : 연·월·일을 따로 채점한 평균 (운영진 채점 방식)", options: { bullet: true, breakLine: true } },
          { text: "회복 / 퇴보 : 이전 버전 대비 새로 맞힌 장 / 새로 틀린 장", options: { bullet: true } }], 0.3, 3.7, 9.4, 0.95, { fontSize: 10.8, paraSpaceAfter: 3 });
  strip(s, ["모든 수치의 예측 파일과 실험 기록은 ", ["저장소 results/ · docs/실험_기록.md"], " 에 있다"], 4.75);
  s.addNotes("질의응답용 부록입니다. 측정셋별 수치 전체입니다.");
}

pres.writeFile({ fileName: path.join(__dirname, "[CODE]_서브웨이_본선발표.pptx") }).then((f) => console.log("saved", f, "slides", pageNo));
