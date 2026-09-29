# -*- coding: utf-8 -*-
"""(u) 인식기 셋 다수결 실험 — 통합본(노트북 기본값)으로 답을 고른 뒤, **고른 후보의 글자 박스만** 파인튜닝 인식기와 한국어 인식기로
한 번씩 더 읽어, 두 인식기가 같은 날짜를 내고 그 날짜가 지금 답과 한 칸(연·월·일 중 하나)만 다르면 그 날짜로 바꾼다.

    .venv/Scripts/python notebooks/exp_vote3.py <K> <N>      → results/exp_vote3_<EXP_TAG>_<K>.csv

왜: 9/28 남은 오답 398장 중 한 칸만 틀린 것이 100장(숫자 한 글자 차이 70). 파인튜닝 인식기와 일만 다르게 읽은 74장은
    파인튜닝이 맞음 28 · 지금 인식기가 맞음 31 · 둘 다 오답 15 로 반반이라, 둘 중 누구를 믿을지 셋째 의견으로 가린다.
미리 정한 규칙 (열 v3, 측정 전에 고정 — 결과를 보고 바꾸지 않는다):
    - 읽기: 고른 후보의 단어 박스 크롭(2패스와 같은 크롭)을 원본 축척과 1024px 축척으로 각 인식기가 읽는다.
      한 인식기의 의견 = 두 축척에서 파싱된 날짜의 합집합 (고른 후보와 같거나 더 좋은 패턴 등급만).
    - 바꿈: 날짜 X 가 파인튜닝 의견과 한국어 의견에 **둘 다** 있고, 지금 답은 두 의견 **어디에도** 없고,
      X 가 지금 답과 정확히 한 칸만 다르고(빈 칸을 채우는 것 포함), 그런 X 가 하나뿐일 때만.
    - 파인튜닝 폴백·확대 재시도로 나온 답, 못 읽은 장(NONE)은 건드리지 않는다.
읽은 글자를 그대로 저장하므로(열 ft_full·ft_mid·ko_full·ko_mid) 다른 변형은 다시 돌리지 않고 계산할 수 있다 — 단 그 결과는 탐색용.

환경변수: EXP_TAG · EXP_FIRST(먼저 돌릴 image_id 목록) · EXP_RESUME=1
"""
import os, sys, time
import cv2
import pandas as pd

sys.argv = sys.argv[:1] + (sys.argv[1:3] if len(sys.argv) > 2 else ["0", "1"])
import exp_merged as M          # 노트북 셀을 실행하고 run(img, cfg)·key(b) 를 준다 (실행 셀의 장별 처리와 같은 순서)

g, K, N = M.g, M.K, M.N
TIER = g["KIND_TIER"]


def bgr(c):
    return cv2.cvtColor(c, cv2.COLOR_GRAY2BGR) if c.ndim == 2 else c


def read(model, crops, allow=None):
    if model is None or not crops:
        return ""
    texts = [r["rec_text"] for r in model.predict(input=[bgr(c) for c in crops], batch_size=len(crops))]
    if allow:
        texts = ["".join(ch if ch in allow else " " for ch in t) for t in texts]
    return " ".join(texts)


def dates(text, hint, tier_max):
    out = set()
    for (y, m, d, kind) in g["parse_dates"](text, dmy_hint=hint):
        if TIER.get(kind, 9) <= tier_max:
            out.add((y, m, d))
    return out


def fmt(t):
    y = f"{t[0]:04d}" if t[0] is not None else "NONE"
    d = "NONE" if t[2] is None else f"{t[2]:02d}"
    return f"{y}-{t[1]:02d}-{d}"


def vote(best, ft_set, ko_set):
    cur = (best["y"], best["m"], best["d"])
    if cur in ft_set or cur in ko_set:
        return None
    xs = [x for x in (ft_set & ko_set) if sum(a != b for a, b in zip(x, cur)) == 1 and all(v is not None for v, c in zip(x, cur) if c is not None)]
    return xs[0] if len(xs) == 1 else None


if __name__ == "__main__":
    J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
    T = J[~J.block.isin(["1", "2", "3", "4", "5"])]
    if os.environ.get("EXP_FIRST"):
        first = set(open(os.environ["EXP_FIRST"], encoding="utf-8").read().split())
        T = pd.concat([T[T.image_id.isin(first)], T[~T.image_id.isin(first)]])
    T = T.iloc[K::N]
    out = f"results/exp_vote3_{os.environ.get('EXP_TAG', 'vote3')}_{K}.csv"
    rows = []
    if os.environ.get("EXP_RESUME") == "1" and os.path.exists(out):
        prev = pd.read_csv(out, dtype=str, keep_default_na=False); rows = prev.to_dict("records"); T = T[~T.image_id.isin(prev.image_id)]
        print(f"resume: {len(prev)}장 저장됨, {len(T)}장 남음", flush=True)
    rec_ft, rec_ko = g["rec_fallback"], g["rec_ko"]
    print("인식기: 파인튜닝", rec_ft is not None, "· 한국어", rec_ko is not None, "| 기본값", {k: g[k] for k in ("RULE_SEPMIX", "RULE_TAIL", "RULE_YMSEP", "RULE_REREAD", "KO_LINE_MODE", "REDETECT", "RETRY_NONE")}, flush=True)
    assert rec_ft is not None and rec_ko is not None
    for n, (_, r) in enumerate(T.iterrows()):
        img = g["load_image"](f"images/{r.file}")
        t0 = time.time(); best = M.run(img, "fin"); t1 = time.time()
        rec = dict(image_id=r.image_id, label=r.final_date, tags=r.tags, fin=M.key(best), v3=M.key(best), src=(best or {}).get("src", ""), kind=(best or {}).get("kind", ""),
                   ft_full="", ft_mid="", ko_full="", ko_mid="", ft_dates="", ko_dates="")
        if best is not None and not best.get("src", "").startswith("ft/") and "retry" not in best.get("src", ""):
            src = best.get("dotfix_img", img)
            crops = [cr for cr in (g["crop_with_margin"](src, ib, g["PASS2_MARGIN"]) for ib in best.get("items", [])) if cr is not None and cr.size]
            if crops:
                sm = g["P2_MID_SIZE"] / max(src.shape[:2])
                mids = [cv2.resize(cr, (max(2, int(cr.shape[1] * sm)), max(2, int(cr.shape[0] * sm))), interpolation=cv2.INTER_AREA) for cr in crops] if sm < 1.0 else []
                hint = best.get("hint", False); tm = max(1, TIER.get(best["kind"], 9))
                rec["ft_full"] = read(rec_ft, crops, g["ALLOW_P2"]); rec["ft_mid"] = read(rec_ft, mids, g["ALLOW_P2"])
                rec["ko_full"] = read(rec_ko, crops); rec["ko_mid"] = read(rec_ko, mids)
                ft_set = dates(rec["ft_full"], hint, tm) | dates(rec["ft_mid"], hint, tm)
                ko_set = dates(rec["ko_full"], hint, tm) | dates(rec["ko_mid"], hint, tm)
                rec["ft_dates"] = ";".join(sorted(fmt(x) for x in ft_set)); rec["ko_dates"] = ";".join(sorted(fmt(x) for x in ko_set))
                x = vote(best, ft_set, ko_set)
                if x is not None:
                    rec["v3"] = fmt(x)
                for c in ("ft_full", "ft_mid", "ko_full", "ko_mid"):
                    rec[c] = rec[c][:80]
        rec["sec"] = round(t1 - t0, 2); rec["sec_vote"] = round(time.time() - t1, 3)
        rows.append(rec)
        if n % 25 == 0:
            print(n, len(T), flush=True); pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    print("done", len(rows))
