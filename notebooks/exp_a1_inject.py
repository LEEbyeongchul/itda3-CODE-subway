# -*- coding: utf-8 -*-
# A1 오류 주입: 실제 인쇄 = 라벨 g, 기대값 E = g + δ 로 두고 모델 답 p 가 E 와 같으면 '놓침'
# 실행: python notebooks/exp_a1_inject.py <pred500·debug500 CSV 가 있는 폴더>  (byeongchul-final 의 results/ 에 있음)
import pandas as pd, glob, sys, datetime as dt, collections
SP = sys.argv[1]
L = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False, encoding="utf-8-sig") for f in glob.glob("labels/labels_block*.csv")])
L["block"] = L.block.astype(int)
L = L.drop_duplicates("image_id").set_index("image_id")

def d(s):
    try:
        y, m, dd = s.split("-"); return dt.date(int(y), int(m), int(dd))
    except Exception:
        return None

def shift(g, kind):
    try:
        if kind == "일+1": return g + dt.timedelta(days=1)
        if kind == "일-1": return g - dt.timedelta(days=1)
        if kind == "일+2": return g + dt.timedelta(days=2)
        if kind == "일-2": return g - dt.timedelta(days=2)
        if kind == "주+1": return g + dt.timedelta(days=7)
        if kind == "월+1": return g.replace(year=g.year + (g.month == 12), month=g.month % 12 + 1)
        if kind == "월-1": return g.replace(year=g.year - (g.month == 1), month=(g.month - 2) % 12 + 1)
        if kind == "연+1": return g.replace(year=g.year + 1)
        if kind == "연-1": return g.replace(year=g.year - 1)
        if kind == "일↔월": return g.replace(month=g.day, day=g.month) if g.day <= 12 and g.day != g.month else None
    except ValueError:
        return None
KINDS = ["일+1", "일-1", "일+2", "일-2", "주+1", "월+1", "월-1", "연+1", "연-1", "일↔월"]

def run(name, df, cands=None):
    df = df.copy(); df["g"] = df.image_id.map(L.final_date); df["tags"] = df.image_id.map(L.tags).fillna("")
    df = df[df.g.notna()]
    full = df[df.g.map(lambda s: d(s) is not None)].copy()
    full["gd"] = full.g.map(d); full["pd_"] = full.p.map(d)
    n = len(full)
    ok = (full.p == full.g); none = (full.p == "NONE"); part = (~ok) & (~none) & full.pd_.isna(); wrong = (~ok) & full.pd_.notna()
    print(f"\n[{name}] 라벨이 완전한 날짜인 사진 {n}장 (전체 {len(df)}장)")
    print(f"  정상 인쇄일 때: 통과 {ok.mean()*100:.1f}% | 사람 확인 {100-ok.mean()*100:.1f}% = 미인식 {none.mean()*100:.1f}% + 일부만 읽음 {part.mean()*100:.1f}% + 완전한 날짜로 틀림 {wrong.mean()*100:.1f}% (놓침의 최악 상한)")
    p1 = ok.mean()
    print(f"  세 장 규칙(독립 가정): 사람 확인 {(1-p1)*(1-p1*p1)*100:.1f}%, 추가 촬영 점검당 {(1-p1)*2:.2f}장")
    rows = []
    for k in KINDS:
        E = full.gd.map(lambda g: shift(g, k)); v = E.notna()
        miss = (full.pd_[v] == E[v])
        rows.append((k, int(v.sum()), int(miss.sum()), miss.mean() * 100))
    print("  오류 유형별 놓침(한 장 판정): " + " · ".join(f"{k} {c}/{nn}장({r:.2f}%)" for k, nn, c, r in rows))
    tot = sum(c for _, _, c, _ in rows); den = sum(nn for _, nn, _, _ in rows)
    print(f"  유형 합계 {tot}/{den} = {tot/den*100:.2f}%")
    # 틀린 답이 정답과 어떻게 다른가
    diff = collections.Counter()
    for g, p in zip(full.gd[wrong], full.pd_[wrong]):
        f = [g.year != p.year, g.month != p.month, g.day != p.day]
        diff["연만" if f == [1,0,0] else "월만" if f == [0,1,0] else "일만" if f == [0,0,1] else "둘 이상"] += 1
    print("  완전한 날짜로 틀린 답의 모양:", dict(diff))
    dual = full.tags.str.contains("2")
    print(f"  병기 {dual.sum()}장 통과 {ok[dual].mean()*100:.1f}% / 비병기 통과 {ok[~dual].mean()*100:.1f}%")
    if cands is not None:
        cs = full.image_id.map(cands)
        inc = pd.Series([g in (c or set()) for g, c in zip(full.gd, cs)], index=full.index)
        print(f"  [후보 대조] 기대값이 후보 목록에 있으면 통과: 정상 인쇄 통과 {inc.mean()*100:.1f}% (한 답 대조 {ok.mean()*100:.1f}%), 병기 {inc[dual].mean()*100:.1f}%")
        rows = []
        for k in KINDS:
            E = full.gd.map(lambda g: shift(g, k)); v = E.notna()
            miss = pd.Series([e in (c or set()) for e, c in zip(E[v], cs[v])])
            rows.append((k, int(v.sum()), int(miss.sum()), miss.mean() * 100))
        print("    놓침: " + " · ".join(f"{k} {c}/{nn}({r:.2f}%)" for k, nn, c, r in rows))
        tot = sum(c for _, _, c, _ in rows); den = sum(nn for _, nn, _, _ in rows)
        print(f"    유형 합계 {tot}/{den} = {tot/den*100:.2f}%")

# 봉인 500장 (병철 9/28 통합본)
p = pd.read_csv(f"{SP}/pred500_2026-09-28_merged.csv", dtype=str, keep_default_na=False).rename(columns={"final_date": "p"})
dbg = pd.read_csv(f"{SP}/debug500_2026-09-28_merged.csv", dtype=str, keep_default_na=False)
def parse_c(s):
    out = set()
    for t in s.split("|"):
        x = d(t.split(":")[0]) if t else None
        if x: out.add(x)
    return out
cand = dict(zip(dbg.image_id, dbg.cands.map(parse_c)))
run("봉인 500장, 9/28 통합본", p[["image_id", "p"]], cand)
# 판정용 (이 PC 통합본, exp_vote3 의 fin 열)
v = pd.read_csv("results/exp_vote3_2026-09-28_0.csv", dtype=str, keep_default_na=False, encoding="utf-8-sig").rename(columns={"fin": "p"})
run(f"판정용 {len(v)}장, 이 PC 통합본", v[["image_id", "p"]])
