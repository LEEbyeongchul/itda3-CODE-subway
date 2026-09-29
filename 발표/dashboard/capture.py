"""대시보드 화면을 PNG 로 저장한다 (발표 슬라이드에 넣을 캡처).

    python 발표/dashboard/capture.py

Chrome 을 창 없이 띄워 1600x900 화면을 2배 해상도(3200x1800)로 찍는다.
결과는 발표/dashboard/captures/ 에 저장된다.
"""
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
OUT = HERE / "captures"
CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
# (파일 이름, 주소 뒤에 붙는 화면 지정)
SHOTS = [
    ("01_전략맵", "strategy"),
    ("02_판매자_A1_촬영", "seller/A/1"),
    ("02_판매자_A2_자동입력", "seller/A/2"),
    ("02_판매자_A3_확인", "seller/A/3"),
    ("02_판매자_A4_게시글", "seller/A/4"),
    ("02_판매자_B2_확신낮음_빈칸", "seller/B/2"),
    ("02_판매자_B3_입력대조", "seller/B/3"),
    ("02_판매자_C2_틀리게읽음", "seller/C/2"),
    ("02_판매자_C3_판매자수정", "seller/C/3"),
    ("02_판매자_D2_병기", "seller/D/2"),
    ("02_판매자_D4_게시보류", "seller/D/4"),
    ("02_판매자_E2_못읽음_빈칸", "seller/E/2"),
    ("02_판매자_E4_게시글", "seller/E/4"),
    ("03_운영현황_운영기준", "ops/ops/d1"),
    ("03_운영현황_읽히면채움", "ops/none/d1"),
    ("03_운영현황_0.9이상", "ops/c09/d1"),
    ("03_운영현황_최근30일", "ops/ops/d30"),
    ("04_검토큐_입력값다름", "queue/0"),
    ("04_검토큐_오독교정", "queue/1"),
    ("04_검토큐_기한경과", "queue/2"),
    ("05_비용과확장", "cost"),
]


def main():
    chrome = next((c for c in CHROME if Path(c).exists()), None)
    if not chrome:
        sys.exit("Chrome 또는 Edge 를 찾지 못했습니다")
    OUT.mkdir(exist_ok=True)
    base = "file:///" + quote((HERE / "index.html").as_posix(), safe="/:")
    for name, route in SHOTS:
        png = OUT / f"{name}.png"
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1600,900",
             "--force-device-scale-factor=2", "--virtual-time-budget=4000", f"--screenshot={png}", f"{base}#{route}"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        print("saved", png.name)


if __name__ == "__main__":
    main()
