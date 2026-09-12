# 803장 튜닝셋에서 미검출(NONE)·오답 이미지를 매니페스트(크롭 최소 편집거리)와 대조해
# "탐지·인식이 날짜 근처까지는 갔다(dist<=3)" vs "아예 못 읽었다(dist 큼 / 크롭 없음)" 로 나눈다.
import pandas as pd, sys
ev = pd.read_csv("results/eval_rest803_2026-09-10.csv", dtype=str, keep_default_na=False).set_index("image_id")
man = pd.read_csv("data/rec_train/manifest.csv", dtype=str, keep_default_na=False).set_index("image_id")
man["dist"] = man["dist"].astype(int)
j = ev.join(man[["dist", "kept", "ocr_text", "label"]], how="left")
j["dist"] = j["dist"].fillna(-2).astype(int)   # -2 = NONE 라벨 등으로 매니페스트에 없음
def bucket(d):
    if d == 0: return "정확히 읽힘"
    if 1 <= d <= 3: return "근접 오독 (dist 1~3)"
    if d >= 4: return "크게 오독 (dist 4+)"
    if d == -1: return "크롭 없음"
    return "매니페스트 없음"
j["bucket"] = j["dist"].map(bucket)
print("=== 오답 유형 x 크롭 매칭 (803장)")
print(pd.crosstab(j["err_type"].replace("", "정답"), j["bucket"]).to_string())
w = j[j.err_type == "미검출(NONE)"]
print(f"\n미검출 {len(w)}장 중 근접 오독(dist<=3) = {(w.dist.between(1,3)).sum()}  → 인식기 파인튜닝으로 회복 가능성 있는 몫")
print(f"미검출 중 dist 4+ 또는 크롭 없음 = {((w.dist>=4)|(w.dist==-1)).sum()}  → 탐지 또는 인식 완전 실패")
print("\n미검출 근접 오독 예시:"); print(w[w.dist.between(1,3)][["raw","ocr_text","dist"]].head(12).to_string())
