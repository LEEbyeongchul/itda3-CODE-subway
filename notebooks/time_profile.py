# -*- coding: utf-8 -*-
"""통합본 단계별 시간 프로파일 — predict.ipynb 실행 셀의 장별 처리(exp_merged.py 의 run 과 같은 순서)에 단계별 타이머를 달아
어느 단계가 장당 몇 초를 쓰는지 잰다. 다른 Paddle 프로세스가 없을 때 1프로세스로 돌린다.

    .venv/Scripts/python notebooks/time_profile.py <장수> <출력 CSV>

판정용 2,852장에서 무작위(seed 7) <장수>장. 노트북 기본값 그대로(시간 예산 가드는 걸지 않음). 사진 읽기 시간은 뺀다.
단계: p1(1패스 사다리) · dot(도트 폴백: 원본 재인식 + 전처리 변형) · redet(이웃 줄 재탐지) · p2(2패스) · kol(한국어 2차 의견) ·
      rr(깨진 줄 다시 읽기) · ft(파인튜닝 폴백 = 1패스·2패스 통째로 한 번 더) · retry(확대 재시도)."""
import json, os, sys, time
import pandas as pd

os.environ.setdefault("ITDA_THREADS", "4")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
OUT = sys.argv[2] if len(sys.argv) > 2 else "results/time_profile.csv"
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__prof__", "os": os}
for i in (1, 2, 3, 4, 5):
    exec(cells[i], g)

DOT = {"t0": None}            # 이 장에서 도트 폴백이 처음 시작된 시각 (pass1 안에서 dotfix_image 또는 hires 재귀가 불릴 때)
_dotfix, _pass1 = g["dotfix_image"], g["pass1"]


def dotfix_image(*a, **k):
    if DOT["t0"] is None:
        DOT["t0"] = time.time()
    return _dotfix(*a, **k)


def pass1(img, *a, **k):                     # 인자는 그대로 넘긴다 (ladder·hires·det_kw 등)
    hires = k.get("hires", a[1] if len(a) > 1 else False)
    if hires and DOT["t0"] is None:          # 원본 해상도 재인식(DOTFIX_EXTRA)도 폴백에 넣는다
        DOT["t0"] = time.time()
    return _pass1(img, *a, **k)


g["dotfix_image"], g["pass1"] = dotfix_image, pass1


def key(b):
    if not b:
        return "NONE"
    y = f"{b['y']:04d}" if b["y"] is not None else "NONE"
    d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"


def timed_pass1(img, T, tag):
    DOT["t0"] = None
    t = time.time(); out = g["pass1"](img); e = time.time()
    dot = (e - DOT["t0"]) if DOT["t0"] is not None else 0.0
    T[tag + "dot"] = T.get(tag + "dot", 0) + dot
    T[tag + "p1"] = T.get(tag + "p1", 0) + (e - t - dot)
    return out


def run(img):
    T = {}
    def lap(name, f, *a):
        t = time.time(); r = f(*a); T[name] = T.get(name, 0) + time.time() - t; return r
    cands, p1_lines = timed_pass1(img, T, "")
    if cands and g["REDETECT"] and not any("dotfix_img" in c for c in cands):
        t = time.time()
        if g["has_neighbor_line"](img, cands, p1_lines):
            cands = cands + g["redetect_neighbors"](img, cands)
        T["redet"] = time.time() - t
    if cands:
        cands = lap("p2", g["pass2"], img, cands)
        if g["KO_KEYWORD"]:
            cands = g["keyword_filter"](img, cands)
    if g["KO_LINE"]:
        cands = lap("kol", g["keyword_line_reread"], img, cands, p1_lines)
    if g["RULE_REREAD"]:
        cands = lap("rr", g["broken_line_reread"], img, cands, p1_lines)
    best = g["select_date"](cands)
    stage = "main"
    if best is None and g["rec_fallback"] is not None:
        stage = "ft"; t = time.time()
        g["reader"].rec, g["rec_fallback"] = g["rec_fallback"], g["reader"].rec
        try:
            cands, p1_lines = g["pass1"](img)
            if cands:
                cands = g["pass2"](img, cands)
            for c in cands:
                c["src"] = "ft/" + c["src"]
            best = g["select_date"](cands)
        finally:
            g["reader"].rec, g["rec_fallback"] = g["rec_fallback"], g["reader"].rec
        T["ft"] = time.time() - t
    if best is None and g["RETRY_NONE"]:
        stage = "retry"; t = time.time()
        cands, p1_lines, _ = g["retry_none"](img)
        if cands:
            cands = g["pass2"](img, cands)
            best = g["select_date"](cands)
        T["retry"] = time.time() - t
    return best, T, stage


if __name__ == "__main__":
    J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
    S = J[~J.block.isin(["1", "2", "3", "4", "5"])].sample(n=N, random_state=7)
    print("기본값", {k: g[k] for k in ("RULE_SEPMIX", "RULE_TAIL", "RULE_YMSEP", "RULE_REREAD", "KO_LINE", "KO_LINE_MODE", "REDETECT", "RETRY_NONE")}, "| 폴백 인식기", g["rec_fallback"] is not None, flush=True)
    imgs = [(r.image_id, r.final_date, g["load_image"](f"images/{r.file}")) for r in S.itertuples()]
    run(imgs[0][2])                      # 첫 호출의 준비 비용은 버린다
    rows = []; COLS = ["p1", "dot", "redet", "p2", "kol", "rr", "ft", "retry"]
    for n, (iid, lab, img) in enumerate(imgs):
        t = time.time(); best, T, stage = run(img); tot = time.time() - t
        rows.append(dict(image_id=iid, label=lab, pred=key(best), src=(best or {}).get("src", ""), last_stage=stage, sec=round(tot, 2),
                         **{c: round(T.get(c, 0), 3) for c in COLS}, wh=f"{img.shape[1]}x{img.shape[0]}"))
        if n % 20 == 19:
            print(n + 1, N, flush=True); pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8-sig")
    D = pd.DataFrame(rows); D.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"장당 평균 {D.sec.mean():.2f}s · 중앙 {D.sec.median():.2f}s · p90 {D.sec.quantile(.9):.2f}s · 최대 {D.sec.max():.1f}s → 500장 환산 {D.sec.mean() * 500:.0f}s")
    for c in COLS:
        print(f"  {c:6s} 장당 {D[c].mean():.3f}s ({D[c].sum() / D.sec.sum():5.1%}) · 쓴 장 {int((D[c] > 0.005).sum())} · 쓴 장 평균 {D[c][D[c] > 0.005].mean() if (D[c] > 0.005).any() else 0:.2f}s")
    print("done")
