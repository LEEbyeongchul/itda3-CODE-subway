# 본선 발표 자료

| 파일 | 내용 |
| --- | --- |
| `[CODE]_서브웨이_본선발표.pptx` | 발표 슬라이드 (본문 20장 + 부록 2장). 발표자 노트에 대본이 들어 있음 |
| `[CODE]_서브웨이_본선발표.pdf` | 같은 슬라이드의 PDF (제출용) |
| `발표_대본.md` | 슬라이드별 대본·시간 배분·예상 질문과 답 |
| `src/` | 슬라이드를 만드는 스크립트와 시연 캡처 원본 |

## 글꼴

전체 글꼴은 **Pretendard SemiBold**. 글꼴이 없는 PC 에서도 같게 보이도록 pptx 에 글꼴을 포함해 저장했다(사용한 글자만). 다른 PC 에서 글자를 고치려면 Pretendard 를 설치해야 한다. `node build.js` 로 새로 만든 파일에는 글꼴이 포함되지 않으므로, PowerPoint 의 "다른 이름으로 저장 → 도구 → 저장 옵션 → 파일의 글꼴 포함" 으로 한 번 더 저장한다.

## 숫자가 바뀌면

슬라이드는 `src/build.js` 하나로 만든다. 숫자를 고친 뒤 다시 만들면 슬라이드와 대본이 함께 바뀐다.

```bash
cd 발표/src
npm install pptxgenjs
node build.js            # pptx 생성
python make_script.py    # 발표_대본.md 생성 (build.js 의 발표자 노트 + qa.md)
```

PowerPoint 에서 직접 고쳐도 되지만, 그 뒤에 `build.js` 를 다시 돌리면 직접 고친 내용이 사라진다.

## 서비스 시연 화면 (`src/mockup/`)

**9/29 부터 16번 슬라이드는 서현의 시연용 대시보드(`발표/dashboard/`) 캡처에서 폰 부분을 잘라 쓴다** (`src/img/dash_phone1~4.png`, 원본은 `dashboard/captures/02_판매자_A1·A2·B2·A4`). 아래 목업 4장은 그 전에 쓰던 것으로, 지금 슬라이드에는 들어가지 않는다.

| 파일 | 화면 | 캡처 크기 |
| --- | --- | --- |
| `screen1_capture.html` | ① 날짜면 촬영 | 320 x 640 |
| `screen2_confirm.html` | ② 자동 입력 확인 | 320 x 640 |
| `screen3_listing.html` | ③ 게시글 | 320 x 640 |
| `screen4_dashboard.html` | ④ 운영 화면 | 680 x 410 |

- 사진은 팀이 직접 찍은 `xSY0058`(통조림 바닥). 화면의 날짜 `2027-05-08` 은 모델이 이 사진에서 실제로 읽은 값(확신도 0.947, 0.77초). 남은 일수는 발표일 2026-10-03 기준.
- 운영 화면의 수치는 전부 `results/debug_custom389_2026-09-28.csv` 와 라벨에서 계산한 값(자동 입력 기준 확신도 0.7).
- 특정 플랫폼의 화면·로고를 흉내 내지 않은 중립 디자인이다.
- 캡처: Edge 로 `msedge --headless=new --screenshot=out.png --window-size=320,640 --force-device-scale-factor=3 file:///.../screen1_capture.html`, 결과를 `src/img/` 에 넣고 `node build.js`.

## 시연 캡처 (`src/img/`)

네 장 모두 `predict.ipynb` 의 함수를 그대로 실행해 얻은 결과다 (9/28 통합본).

| 파일 | 사진 | 결과 |
| --- | --- | --- |
| `demo_plain.png` | 000005 일반 인쇄 | 2026-07-02 |
| `demo_two.png` | 000007 제조·소비 병기 | 2026-06-25 (늦은 날짜 선택) |
| `demo_dot.png` | 000749 도트 인쇄 | 2026-01-21 (도트 폴백으로 회복) |
| `demo_none.png` | 000486 | NONE (정답 2027-07-15, 못 읽은 예) |
