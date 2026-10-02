# 새 가상환경 재현 로그 (2026-09-30 밤 ~ 10-01 새벽)

> **10/2 추가: 이 실행의 출력은 공식 결과와 다르다.** `submission500_repro.csv` 를 라벨로 채점하면 69.4%(미인식 121장)로, 공식 86.2%(미인식 15장)보다 낮다. 공식 예측과 달랐던 111장을 같은 코드로 Windows 에서 다시 돌리면 모두 공식 예측과 같았으므로 맥 실행 환경 문제로 본다. 최종 재현은 [`../재현_2026-10-02/`](../재현_2026-10-02/README.md) — 새 venv 에서 봉인 500장이 공식 예측과 500장 모두 일치했다.

> 대회 안내서 "제출 전 필수 절차" — 새 가상환경에서 설치부터 실행까지 확인, 로그를 저장소에 포함.
> 본선보고서 초안 D 전체판 "제출 전 남은 일" #6 항목.

## 실행 환경

| 항목 | 값 |
| --- | --- |
| 머신 | 서영 맥북 (팀 개발 PC 1·2 와는 별도의 세 번째 머신) |
| OS | macOS 26.6.2 (BuildVersion 25G83) |
| CPU | Apple Silicon, 8코어 (스레드 제한 없이 실행 — 채점 서버는 4코어이므로 본문 5-1 의 "개발 PC 2" 4스레드 값이 시간 한도 판단 기준) |
| Python | 3.10.21 (새 `.venv`, `python3.10 -m venv .venv`) |
| 설치 | `pip install -r requirements.txt` (macOS 이므로 `+cpu` 접미사 제거, README 안내대로) |
| 핵심 패키지 버전 | torch 2.2.2 · torchvision 0.17.2 · paddlepaddle 3.3.1 · paddleocr 3.7.0 · paddlex 3.7.2 · easyocr 1.7.1 · opencv-python-headless/opencv-contrib-python 4.10.0.84 · pandas 2.2.2 · numpy 1.26.4 · pillow 10.3.0 · nbconvert 7.16.4 |
| 인터넷 | 가중치 다운로드까지만 사용, 이후 추론은 `ITDA_INPUT_DIR`/`ITDA_OUTPUT_PATH` 만 지정하고 오프라인 실행 |
| 입력 | 봉인 500장 (`labels/labels_block1~5.csv` 의 image_id 500개, `images/`에서 대회 배포본 그대로 사용) |
| ITDA_KO_LINE | 지정 안 함 → `predict.ipynb` 기본값(`"0"`, 꺼짐) 그대로 사용. 본선 최종 채택 구성과 동일 |

## 절차 및 소요 시간

| 단계 | 시작 | 끝 | 소요 |
| --- | --- | --- | --- |
| `python3.10 -m venv .venv` + `pip install -r requirements.txt` | 23:22:30 | 23:25:51 | 3분 21초 |
| `bash download_weights.sh` | 23:25:51 | 23:29:07 | 3분 16초 |
| `jupyter nbconvert --to notebook --execute predict.ipynb` (500장) | 23:29:07 | 23:45:10 | **16분 3초 (963초)** |
| 전체 | 23:22:28 | 23:45:10 | 약 23분 |

## 결과

- `submission500.csv` 501줄 (헤더 1 + 500장), 에러 없이 완주
- 스키마: `image_id,year,month,day,final_date` — README 5절 규격과 일치
- **장당 약 1.93초**, 500장 963초 → 채점 한도 2,500초의 **38.5%**
- 실행 로그 원본(가중치 다운로드 진행률 표시 제거한 정리본): `실행_로그_원본_정리.txt`
- 출력 결과: `submission500_repro.csv`

## 참고

- 이 실행은 완전히 새로 만든 가상환경 + `download_weights.sh` 로 받은 가중치로만 돌렸고, 팀이 미리 설치해 둔 기존 `venv/`(README 밖 별도 폴더)는 건드리지 않았다.
- `main` 브랜치에는 이 재현 과정에서 어떤 변경도 가하지 않았다 (`.venv/`, `weights/` 모두 gitignore 대상, 결과물은 이 커밋으로 직접 추가).
- 채점 서버(4코어)보다 빠른 머신일 수 있으므로, 이 결과는 "정상 완주 + 속도 여유" 근거로만 쓰고 본문 5-1 의 공식 숫자는 팀 개발 PC 2(4스레드, 79%) 기준을 유지할 것을 제안.
