# -*- coding: utf-8 -*-
"""(s) 깨져 읽힌 줄 다시 읽기 — 판정용 2,852장 측정. predict.ipynb 는 건드리지 않고 이 파일에서 규칙을 덧씌운다 (채택되면 노트북으로 옮긴다).

    .venv/Scripts/python notebooks/exp_reread.py <K> <N>     → results/exp_rules4_<EXP_TAG>_<K>.csv  (K번째/N분할)
    채점: .venv/Scripts/python notebooks/score_rule.py <EXP_TAG> reread      (rvote 도 같은 방법)

무엇을 고치나: 1패스가 소비기한 줄을 '202.05.21' 처럼 깨뜨려 읽으면 날짜 후보가 되지 못하고, 2패스는 후보 줄만 다시 읽으므로
  그 줄은 원본 해상도로 다시 읽힐 기회가 없다 (000242: 제조일만 후보 → 제조일을 답함).
규칙: 1패스 줄 가운데 **후보를 하나도 못 낸 줄**에 날짜 모양 토막(숫자 6~12개 + 숫자 사이 구분자 . - / : 1개 이상)이 있으면
  그 줄을 세 가지로 다시 읽는다 — ① 단어 박스를 원본에서 ② 단어 박스를 1024px 축척에서 ③ 줄 박스 통째로 원본에서. 탐지기는 다시 돌리지 않는다.
  다시 읽은 글에서 등급 1 완전 날짜가 나오면 후보에 **추가**만 한다. 기존 후보는 지우지 않고, 고르는 일은 기존 select_date 가 한다.
  정답·라벨은 조건에 쓰지 않는다. 상수는 비용 상한(줄 4개)뿐.
열: cur = 현재 기본값(p1det) 재현 · reread = 세 읽기 중 하나라도 · rvote = 세 읽기 중 둘 이상이 같은 날짜.

(t) 연·월 사이 구분자 빠짐 — (s) 표적 45장에서 다시 읽어도 똑같이 틀리는 줄을 보니 '202104.19' '202110.04' '202201/14' 처럼
  연도와 월 사이 구분자만 빠진 읽기가 되풀이됐다. 파서는 뒤 구분자가 빠진 '2021.0419'(YMD_GLUED)·'27.102023' 은 받는데 이 꼴만 안 받는다.
규칙: 파싱 전에 20YY + 월(01~12) + 구분자 + 일(01~31) 을 20YY<구분자>MM<구분자>DD 로 고쳐 쓴다 (앞뒤에 숫자·구분자가 붙으면 제외).
열: ymsep = (t) 만 · both = (t) + (s) reread.  (t) 가 한 번도 발동하지 않은 장은 파이프라인을 한 번만 돌린다.
"""
import json, os, re, sys, time
import pandas as pd

os.environ.setdefault("ITDA_THREADS", "4")
os.environ.setdefault("ITDA_KO_LINE", "1")
os.environ.setdefault("ITDA_KO_LINE_MODE", "p1det")
K, N = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
nb = json.load(open("predict.ipynb", encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
g = {"__name__": "__exp__", "os": os}
for i in (1, 2, 3, 4, 5):
    exec(cells[i], g)
load_image, pass1, pass2, select_date = g["load_image"], g["pass1"], g["pass2"], g["select_date"]
crop_with_margin, reader = g["crop_with_margin"], g["reader"]
_YM_GLUED = re.compile(r"(?<![\d.\-/])(20\d\d)(0[1-9]|1[0-2])([.\-/])(0[1-9]|[12]\d|3[01])(?!\d)")
_parse_orig = g["parse_dates"]
T_RULE = {"on": False, "fired": False}


def _parse_t(text, dmy_hint=False):
    if T_RULE["on"]:
        fixed = _YM_GLUED.sub(lambda m: m[1] + m[3] + m[2] + m[3] + m[4], text)
        if fixed != text:
            T_RULE["fired"] = True; T_RULE.setdefault("log", []).append((text, fixed)); text = fixed
    return _parse_orig(text, dmy_hint=dmy_hint)


g["parse_dates"] = _parse_t                         # 노트북 함수들은 전역 이름으로 찾으므로 파이프라인 전체에 적용된다
parse_dates = _parse_t
cv2, np, KIND_TIER = g["cv2"], g["np"], g["KIND_TIER"]
MARGIN, ALLOW, MID = g["PASS2_MARGIN"], g["ALLOW_P2"], g["P2_MID_SIZE"]
REREAD_MAX = 4                                     # 장당 다시 읽는 줄 수 상한 (비용 상한)
_SEP_BETWEEN = re.compile(r"\d[.\-/:]+\d")


def dateish_broken(text):
    """날짜 모양 토막이 있는가: 공백 없는 한 덩어리에 숫자 6~12개 + 숫자 사이 구분자."""
    return any(6 <= sum(ch.isdigit() for ch in tok) <= 12 and _SEP_BETWEEN.search(tok) for tok in text.split())


def broken_lines(img, p1_lines):
    """후보를 못 낸 날짜 모양 줄 [(원본 bbox, 원본 단어 박스들, 1패스 글, 일먼저 힌트)], 큰 글자 순 REREAD_MAX 개."""
    H, W = img.shape[:2]
    out = []
    for L, lines in p1_lines:
        try:
            Lnum = int(str(L).split("@")[-1])
        except ValueError:
            continue
        sc = min(1.0, Lnum / max(H, W))
        hint = any(g["has_dmy_hint"](ln["text"]) for ln in lines)
        for ln in lines:
            if not dateish_broken(ln["text"]) or parse_dates(ln["text"], dmy_hint=hint):
                continue
            bb = (ln["x0"] / sc, ln["y0"] / sc, ln["x1"] / sc, ln["y1"] / sc)
            if any(abs(bb[0] - o[0][0]) < 0.03 * W and abs(bb[1] - o[0][1]) < 0.03 * H for o in out):   # 사다리 단계 사이 중복
                continue
            out.append((bb, [(it["x0"] / sc, it["y0"] / sc, it["x1"] / sc, it["y1"] / sc) for it in ln["items"]], ln["text"], hint))
    out.sort(key=lambda o: -(o[0][3] - o[0][1]))
    return out[:REREAD_MAX]


def reread(img, cands, p1_lines):
    """반환: (하나라도 읽힌 새 후보, 둘 이상 일치한 새 후보, 다시 읽은 줄 수, 진단 글)."""
    targets = broken_lines(img, p1_lines)
    if not targets:
        return [], [], 0, ""
    sm = MID / max(img.shape[:2])
    crops, plan = [], []                           # plan: (줄 번호, 읽기 종류)
    for n, (bb, items, _t, _h) in enumerate(targets):
        for ib in items:
            cr = crop_with_margin(img, ib, MARGIN)
            if cr is None or not cr.size:
                continue
            crops.append(cr); plan.append((n, "word"))
            if sm < 1.0:
                crops.append(cv2.resize(cr, (max(2, int(cr.shape[1] * sm)), max(2, int(cr.shape[0] * sm))), interpolation=cv2.INTER_AREA)); plan.append((n, "mid"))
        cr = crop_with_margin(img, bb, MARGIN)
        if cr is not None and cr.size:
            crops.append(cr); plan.append((n, "line"))
    if not crops:
        return [], [], len(targets), ""
    pairs = reader._rec_many(crops, ALLOW)
    seen = {(c["y"], c["m"], c["d"]) for c in cands}
    new_any, new_vote, dbg = [], [], []
    for n, (bb, items, t1, hint) in enumerate(targets):
        reads = {}
        for (k, kind), (t, cf) in zip(plan, pairs):
            if k == n:
                reads.setdefault(kind, []).append((t, cf))
        votes, info = {}, {}
        for kind, lst in reads.items():
            text = " ".join(t for t, _ in lst); conf = float(np.mean([cf for _, cf in lst]))
            for (y, m, d, pk) in parse_dates(text, dmy_hint=hint):
                if y is None or d is None or KIND_TIER.get(pk, 9) > 1:
                    continue
                votes.setdefault((y, m, d), set()).add(kind)
                info.setdefault((y, m, d), (pk, conf, text))
        dbg.append(f"'{t1}' → " + " | ".join(f"{kind}:'{' '.join(t for t, _ in lst)}'" for kind, lst in reads.items()))
        for key, kinds in votes.items():
            if key in seen:
                continue
            pk, conf, text = info[key]
            c = {"y": key[0], "m": key[1], "d": key[2], "kind": pk, "conf": conf, "src": "reread", "text": text[:40], "bbox": bb, "items": [bb], "hint": hint}
            new_any.append(c)
            if len(kinds) >= 2:
                new_vote.append(c)
    return new_any, new_vote, len(targets), " ## ".join(dbg)


def pipeline(img):
    c1, seen = pass1(img)
    c2 = pass2(img, list(c1)) if c1 else []
    if g["KO_LINE"]:
        c2 = g["keyword_line_reread"](img, c2, seen)
    return c2, seen


def key(b):
    if not b:
        return "NONE"
    y = b["y"] if b["y"] is not None else "NONE"; d = "NONE" if b["d"] is None else f"{b['d']:02d}"
    return f"{y}-{b['m']:02d}-{d}"


if __name__ == "__main__":
    J = pd.read_csv("results/join_all3352_v6.csv", dtype=str, keep_default_na=False)
    T = J[~J.block.isin(["1", "2", "3", "4", "5"])]
    if os.environ.get("EXP_FIRST"):   # 먼저 돌릴 image_id 목록. 분할 전에 순서를 바꾸므로 모든 프로세스에 같은 목록을 줘야 한다
        first = set(open(os.environ["EXP_FIRST"], encoding="utf-8").read().split())
        T = pd.concat([T[T.image_id.isin(first)], T[~T.image_id.isin(first)]])
    T = T.iloc[K::N]
    out = f"results/exp_rules4_{os.environ.get('EXP_TAG', 'reread')}_{K}.csv"
    rows = []
    if os.environ.get("EXP_RESUME") == "1" and os.path.exists(out):
        prev = pd.read_csv(out, dtype=str, keep_default_na=False); rows = prev.to_dict("records"); T = T[~T.image_id.isin(prev.image_id)]
        print(f"resume: {len(prev)}장 저장됨, {len(T)}장 남음", flush=True)
    for n, (_, r) in enumerate(T.iterrows()):
        img = load_image(f"images/{r.file}")
        T_RULE.update(on=True, fired=False); ct, seen_t = pipeline(img); fired = T_RULE["fired"]
        T_RULE["on"] = False
        t0 = time.time()
        c2, seen = pipeline(img) if fired else (ct, seen_t)
        t1 = time.time()
        a, v, nl, dbg = reread(img, c2, seen)
        t2 = time.time()
        if fired:
            T_RULE["on"] = True; at = reread(img, ct, seen_t)[0]; T_RULE["on"] = False
        else:
            at = a
        sel = lambda cs: key(select_date(cs)) if cs else "NONE"
        rows.append(dict(image_id=r.image_id, label=r.final_date, tags=r.tags, cur=sel(c2), reread=sel(c2 + a), rvote=sel(c2 + v),
                         ymsep=sel(ct), both=sel(ct + at), t_fired=int(fired),
                         n_lines=nl, sec=round(t1 - t0, 2) if fired else "", sec_reread=round(t2 - t1, 3), dbg=dbg[:400]))
        if n % 5 == 0:
            print(n, len(T), flush=True); pd.DataFrame(rows).to_csv(out, index=False)
    pd.DataFrame(rows).to_csv(out, index=False)
    print("done", len(rows))
