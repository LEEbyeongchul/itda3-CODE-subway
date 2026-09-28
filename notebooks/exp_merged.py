# -*- coding: utf-8 -*-
"""통합본 측정 — predict.ipynb 실행 셀의 장별 처리(재탐지·2패스·한국어 2차 의견·다시 읽기·파인튜닝 폴백·확대 재시도)를
그대로 따라 판정용 2,852장(블록 1~5 봉인 제외)을 돈다. exp_rules4.py 는 재탐지·폴백·재시도를 부르지 않아 통합본을 못 잰다.

    .venv/Scripts/python notebooks/exp_merged.py <K> <N>      → results/exp_merged_<EXP_TAG>_<K>.csv  (K번째/N분할)

환경변수
  EXP_TAG    결과 파일 이름표
  EXP_CFGS   잴 구성, 쉼표 구분 (기본 "fin")
               fin  = 노트북 기본값 그대로 (재탐지 + 확대 재시도 + 한국어 2차 의견 p1det + 후처리 규칙 4개)
               int  = fin 에서 후처리 규칙 4개 (q)(r)(s)(t) 만 끔  → 병철 9/28 통합본과 같은 구성
               nok  = fin 에서 한국어 2차 의견만 끔
  EXP_ONLY   image_id 목록 파일. 주면 그 사진만 돈다 (답이 갈린 장의 책임 가르기용)
  EXP_RESUME 1 이면 저장된 장은 건너뛴다
시간 예산 가드는 걸지 않는다 (FAST_LEVEL 0 고정). 열 sec_<구성> 은 그 구성의 장당 처리 시간(사진 읽기 제외).
"""
import json, os, sys, time
import pandas as pd

os.environ.setdefault("ITDA_THREADS", "4")
K, N = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__exp__", "os": os}
for i in (1, 2, 3, 4, 5):
    exec(cells[i], g)
RULES = ["RULE_SEPMIX", "RULE_TAIL", "RULE_YMSEP", "RULE_REREAD"]
DEFAULTS = {f: g[f] for f in RULES + ["KO_LINE"]}
OFF = {"fin": [], "int": RULES, "nok": ["KO_LINE"]}


def run(img, cfg):
    """실행 셀의 장별 처리와 같은 순서. 반환: 선택된 후보 또는 None."""
    for f, v in DEFAULTS.items():
        g[f] = False if f in OFF[cfg] else v
    cands, p1_lines = g["pass1"](img)
    if cands and g["REDETECT"] and not any("dotfix_img" in c for c in cands) and g["has_neighbor_line"](img, cands, p1_lines):
        cands = cands + g["redetect_neighbors"](img, cands)
    if cands:
        cands = g["pass2"](img, cands)
        if g["KO_KEYWORD"]:
            cands = g["keyword_filter"](img, cands)
    if g["KO_LINE"]:
        cands = g["keyword_line_reread"](img, cands, p1_lines)
    if g["RULE_REREAD"]:
        cands = g["broken_line_reread"](img, cands, p1_lines)
    best = g["select_date"](cands)
    if best is None and g["rec_fallback"] is not None:
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
    if best is None and g["RETRY_NONE"]:
        cands, p1_lines, _ = g["retry_none"](img)
        if cands:
            cands = g["pass2"](img, cands)
            best = g["select_date"](cands)
    return best


def key(b):
    if not b:
        return "NONE"
    y = f"{b['y']:04d}" if b["y"] is not None else "NONE"
    d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"


if __name__ == "__main__":
    CFGS = os.environ.get("EXP_CFGS", "fin").split(",")
    J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
    T = J[~J.block.isin(["1", "2", "3", "4", "5"])]
    if os.environ.get("EXP_ONLY"):
        only = set(open(os.environ["EXP_ONLY"], encoding="utf-8").read().split())
        T = T[T.image_id.isin(only)]
    T = T.iloc[K::N]
    out = f"results/exp_merged_{os.environ.get('EXP_TAG', 'merged')}_{K}.csv"
    rows = []
    if os.environ.get("EXP_RESUME") == "1" and os.path.exists(out):
        prev = pd.read_csv(out, dtype=str, keep_default_na=False); rows = prev.to_dict("records"); T = T[~T.image_id.isin(prev.image_id)]
        print(f"resume: {len(prev)}장 저장됨, {len(T)}장 남음", flush=True)
    print("구성", CFGS, "| 기본값", {k: g[k] for k in RULES + ["KO_LINE", "KO_LINE_MODE", "REDETECT", "RETRY_NONE"]}, "| 폴백 인식기", g["rec_fallback"] is not None, flush=True)
    for n, (_, r) in enumerate(T.iterrows()):
        img = g["load_image"](f"images/{r.file}")
        rec = dict(image_id=r.image_id, label=r.final_date, tags=r.tags)
        order = CFGS if n % 2 == 0 else CFGS[::-1]            # 구성을 사진마다 번갈아 (순서 효과 상쇄)
        for cfg in order:
            t = time.time(); b = run(img, cfg)
            rec[cfg] = key(b); rec["sec_" + cfg] = round(time.time() - t, 2); rec["src_" + cfg] = b["src"] if b else ""
        rows.append(rec)
        if n % 25 == 0:
            print(n, len(T), flush=True); pd.DataFrame(rows).to_csv(out, index=False)
    pd.DataFrame(rows).to_csv(out, index=False)
    print("done", len(rows))
