# ITDA 3rd 학술제 — 소비기한 추출 · [CODE]_서브웨이

상품 뒷면 이미지에서 **소비기한 날짜**를 추출해 `submission.csv` 를 생성하는 추론 파이프라인입니다.
제3회 ITDA 연합학술제 제출용입니다.
- 대회 규정·일정·채점 기준: [docs/ITDA3_참가안내서.md](docs/ITDA3_참가안내서.md)
- **운영진 Q&A 확정사항** (평가셋 500장, 부분점수, `NONE-MM-DD`, 일/월/년 규칙 등): [docs/QA_확정사항.md](docs/QA_확정사항.md)
- **전체 계획 · 일정 · 역할 · 작업 목록**: [docs/프로젝트_계획.md](docs/프로젝트_계획.md)
- **검증셋 라벨링 방법**: [labels/README.md](labels/README.md)
- **날짜 해석 규칙** (운영진: 모호한 값은 팀 규칙으로 채점 → 요약서 삽입용): [docs/날짜_해석_규칙.md](docs/날짜_해석_규칙.md)

---

## 1. 파이프라인 개요 — 2-Pass Hybrid

```
원본 이미지
  │
  ├─ ① 로드 + EXIF 회전 보정            데이터의 8.7%가 90도 회전 상태. cv2.imread 는 EXIF 를 무시하므로 PIL 로 연다. 24MP 는 draft 로 축소 디코딩
  │
  ├─ ② 1패스 검출: 긴 변 640px 축소본 → CRAFT 1회        (후보 없으면 1024px 로 한 번 더 — 사다리)
  │       └→ 인식: 큰 글자 박스부터 30개 (날짜 비슷한 게 없으면 50개까지). 완전한 날짜를 읽으면 그보다 훨씬 작은 박스는 생략
  │       └→ 같은 줄끼리 묶기               '30 12 23', '2020.12.28/16:35' 처럼 갈라진 조각을 한 줄로
  │       └→ 조각 복원                      도트 프린터 '20 2 7 . 0 4.13' → '2027.04.13' (공백 제거본을 함께 파싱)
  │       └→ 9자리 이상 숫자열 마스킹       품목보고번호(20130628…)·바코드(8801…)의 앞자리가 날짜로 읽히는 것 차단
  │       └→ 날짜 정규식 (3단계)            YYYY.MM.DD / YYYYMMDD / DD.MM.YYYY / YY.MM.DD  ▶  DD MM YY · 6자리  ▶  연·월만 · 월·일만
  │       └→ 연도 범위 2017~2031, 2자리 연도 상한 2027
  │       └→ 후보 0개면 영문 월 폴백        큰 박스 12개를 영문 포함으로 재인식 → 'NOV 29 2021' (1회, ~2초)
  │
  ├─ ③ 2패스 확인: 후보 단어 박스만 원본에서 재인식 (검출기 재실행 없음). 같은 값이면 신뢰도↑, 놓친 연도/일만 보완. **교체는 안 함**
  │
  ├─ ④ 선택: 패턴 등급이 가장 높은 후보들 중 가장 늦은 날짜     운영진 확정 규칙 — 병기 시 나중 것이 소비기한
  │
  └─ ⑤ 후보 없음 → NONE  /  월·일만 → NONE-MM-DD  /  연·월만 → YYYY-MM-NONE   (운영진 확정, 필드별 부분점수)
```

**설계 요점**

- **비싼 연산은 후보 영역에만.** CPU 비용의 대부분은 검출기(CRAFT)이고 픽셀 수에 비례합니다. 검출은 축소본에서 장당 1회만 돌리고, 정밀 인식은 후보 크롭에만 씁니다.
- **저해상도 검출이 오히려 정밀도를 올립니다.** 640px 에서는 영양성분표 잔글씨가 검출되지 않아 잡음 후보가 줄고, 큼직한 날짜 스탬프는 그대로 잡힙니다.
- **가장 위험한 오탐은 품목보고번호입니다.** `20130628332176` 의 앞 8자리는 완벽한 YYYYMMDD 입니다. 긴 숫자열을 파싱 전에 통째로 지웁니다.
- **2패스는 확인만 합니다.** 기준선 실측에서 2패스가 1패스 값을 덮어쓴 답의 완전일치가 61.7% vs 유지 72.3% 였습니다. 그래서 같은 값을 다시 읽으면 신뢰도만 올리고, 다른 값은 버립니다.
- **NONE 은 정답 값입니다.** 연도가 없는 제품(우유 `10.14 09:45`)의 정답은 `NONE-10-14` 이므로, NONE 을 회피하지 않고 "없으면 없다"고 답합니다.

---

## 2. 환경 구축

Python **3.10** 기준입니다. (개발 PC 3.11 에서도 동작 확인)

```bash
git clone https://github.com/LEEbyeongchul/itda3-CODE-subway.git
cd itda3-CODE-subway
python -m venv .venv
source .venv/bin/activate          # Windows Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
```

`requirements.txt` 는 CPU 전용 torch 를 고정합니다 (`--extra-index-url` 로 `+cpu` 휠 사용). macOS 는 `+cpu` 접미사를 제거하고 설치하세요.

---

## 3. 가중치 다운로드 — 오프라인 실행의 전제조건

채점 서버는 인터넷이 차단되어 있으므로 EasyOCR 가중치를 **노트북 실행 전에** 받아둬야 합니다.
인터넷이 되는 상태에서 아래를 1회 실행합니다.

```bash
bash download_weights.sh
```

`weights/` 에 다음 두 파일이 생기면 준비 완료입니다.

| 파일 | 역할 | 크기 |
| --- | --- | --- |
| `weights/craft_mlt_25k.pth` | 텍스트 검출기 (CRAFT) | ~79 MB |
| `weights/english_g2.pth` | 영문·숫자 인식기 | ~14 MB |

`predict.ipynb` 는 `download_enabled=False` 로 리더를 만들기 때문에 가중치가 없으면 즉시 실패합니다. 실행 중 몰래 다운로드하는 경로는 없습니다.

---

## 4. 추론 실행 — 운영진 채점 표준 명령

```bash
export ITDA_INPUT_DIR=./val_images
export ITDA_OUTPUT_PATH=./submission.csv

jupyter nbconvert --to notebook --execute predict.ipynb \
    --ExecutePreprocessor.timeout=2400 \
    --output /tmp/executed.ipynb
```

- `ITDA_INPUT_DIR` 안의 이미지(`jpg/jpeg/png/bmp/webp/tif`)를 전부 읽어 `ITDA_OUTPUT_PATH` 에 CSV 를 씁니다.
- `image_id` 는 확장자를 제외한 파일명 그대로입니다 (zero-padding 가정 없음).
- Windows Git Bash 에서는 앞에 `export PYTHONUTF8=1` 을 추가하면 한글 출력이 깨지지 않습니다.

---

## 5. 출력 스키마 (`submission.csv`)

| image_id | year | month | day | final_date |
| --- | --- | --- | --- | --- |
| 000001 | 2027 | 06 | 26 | 2027-06-26 |
| 000047 | NONE | 10 | 14 | NONE-10-14 |
| 000763 | NONE | NONE | NONE | NONE |

각 필드는 독립적으로 `NONE` 이 될 수 있고, `final_date` 는 세 필드를 `-` 로 이은 값입니다. 세 필드가 모두 `NONE` 이면 `final_date` 도 `NONE` 입니다. 인덱스는 저장하지 않습니다.

---

## 6. 개발자용

**장별 진단 출력**

```bash
ITDA_DEBUG=1 ITDA_INPUT_DIR=./val_images ITDA_OUTPUT_PATH=./submission.csv \
  jupyter nbconvert --to notebook --execute predict.ipynb --output /tmp/executed.ipynb
```

장마다 소요 시간, 모든 날짜 후보(값·패턴·출처·신뢰도·원문), 최종 선택을 출력합니다. 채점 환경에는 이 변수가 없으므로 출력이 조용합니다.

**주요 파라미터** (`predict.ipynb` 두 번째 셀)

| 이름 | 기본값 | 의미 |
| --- | --- | --- |
| `PASS1_LADDER` | `(640, 1024)` | 1패스 해상도 사다리. 640 에서 후보가 없을 때만 1024 로 재시도. 검출 시간은 픽셀 수에 비례 — 480→1.8s, 640→2.9s, 800→4.6s, 1024→7.8s, 1280→12.2s (4스레드 실측) |
| `MAX_BOXES` / `MAX_BOXES_HARD` | 30 / 50 | 1패스에서 인식기에 태우는 박스 상한. 날짜 비슷한 텍스트를 하나도 못 봤으면 50개까지. 인식은 박스당 ~0.17s 라 글자 많은 라벨에선 검출기보다 비쌈 |
| `EARLY_STOP_RATIO` | 0.6 | 글자 높이 내림차순으로 인식하다 연도 포함 날짜를 찾으면, 그 높이 × 비율 미만 박스는 건너뜀 (영양성분표 잔글씨 생략) |
| `LOAD_MAX_LONG` | 2000 | 2패스용 원본 상한. 이보다 큰 JPEG 은 디코딩 단계(draft)에서 축소 — 24MP 원본 디코딩+회전 2~3초 절감 |
| `PASS2_MARGIN` | 0.30 | 2패스 크롭 여백 (박스 크기 대비). 640px 박스를 원본 좌표로 환산하면 오차가 커서 넉넉히 |
| `MON_FALLBACK_BOXES` | 12 | 후보 0개일 때 영문 포함 allowlist 로 재인식하는 박스 수 |
| `YEAR_MIN / YEAR_MAX` | 2017 / 2031 | 연도 허용 범위 (라벨 실측 2017~2030). 넓히면 잡음이 미래 연도로 통과해 "가장 늦은 날짜" 규칙을 오염시킴 |
| `YY_SOFT_MAX` | 2027 | 2자리 연도가 모호할 때 이 해를 넘는 해석은 버림. `30/07/26` → 2026-07-30 |
| `MASK_DIGITS_GE` | 9 | 이 길이 이상 연속 숫자는 날짜가 아님 |
| `NONE_POLICY` | `"none"` | 후보 0개일 때 `"none"`(NONE) / `"prior"`(사전확률 날짜). 검증셋으로 비교 후 결정 |

**검증셋과 정확도** — 팀 라벨 `labels/labels_block*.csv` (800장, 해상도 층화). 버전별 정확도·속도와 오류 분석은 [docs/실험_기록.md](docs/실험_기록.md). 원본 데이터는 `images/` (gitignore).

---

## 7. 트러블슈팅

| 증상 | 원인 / 해결 |
| --- | --- |
| `download_weights.sh` 에서 `CERTIFICATE_VERIFY_FAILED` | Windows Python 의 인증서 번들 문제. `pip install certifi` 후 `SSL_CERT_FILE=$(python -c "import certifi;print(certifi.where())") bash download_weights.sh` |
| `UnicodeEncodeError: 'cp949'` | Windows 콘솔 인코딩. `export PYTHONUTF8=1` (스크립트에는 이미 포함) |
| 노트북 첫 셀에서 `FileNotFoundError` 가중치 | `download_weights.sh` 를 먼저 실행 |
| 실행이 매우 느림 | 첫 셀에서 `torch.get_num_threads()` 확인. 논리 코어 수만큼 쓰도록 설정되어 있음 |

---

## 8. 저장소 구조

```
├── predict.ipynb            # 메인 추론 노트북 (채점 대상, 첫 셀 CONFIG 수정 금지)
├── requirements.txt         # 버전 고정 의존성 (Python 3.10 wheel 확인됨, nbconvert·ipykernel 포함)
├── download_weights.sh      # EasyOCR 가중치 사전 다운로드
├── README.md
├── docs/
│   ├── ITDA3_참가안내서.md    # 대회 규정 원문
│   ├── QA_확정사항.md        # 운영진 답변 11건 — 설계 근거
│   ├── 날짜_해석_규칙.md      # 모호한 날짜의 결정 규칙 (요약서 삽입용)
│   ├── 실험_기록.md          # 버전별 정확도·속도, 오류 분석, 효과 없던 시도
│   ├── 프로젝트_계획.md       # 일정·역할·작업 목록
│   ├── 기술적_계획.md         # 탐지·인식기 고도화 계획 (본선용)
│   └── 아이디어.md           # 도메인 기획 (물류 입고 검수)
├── labels/
│   ├── README.md             # 라벨링 규칙
│   ├── sample.csv            # 라벨링 대상·블록 배정
│   └── labels_block*.csv     # 팀 라벨 (raw 가 원본, 나머지 열은 도구 규칙으로 재계산 가능)
├── notebooks/
│   ├── label.py              # 라벨링 도구 (해석 규칙의 정본 구현)
│   └── make_sample.py        # 층화 샘플링
├── weights/                 # 가중치 (gitignore, .gitkeep 만 추적)
├── images/                  # 배포 데이터 3,352장 (gitignore)
└── val_images/              # 검증용 샘플 (gitignore)
```

---

## 9. 제출 전 체크리스트

- [ ] 첫 셀 CONFIG 원문 유지 (`os.environ.get`, 값 직접 대입 금지)
- [ ] `bash download_weights.sh` → 네트워크 차단 → 표준 명령으로 Run All 완주
- [ ] 500장 기준 총 실행 시간이 2400초에 **충분히** 못 미침
- [ ] `submission.csv` 5개 컬럼, 인덱스 없음, 행 수 = 입력 이미지 수
- [ ] `git rev-parse HEAD` 로 제출 커밋 해시 확보
- [ ] 저장소 Public (또는 `b9511242000-blip` Collaborator 초대)
