import pathlib
import re

p = pathlib.Path("剧集/EP003/分镜-搞笑夸张版.md")
t = p.read_text(encoding="utf-8")

# 切出 SHOT-007 ~ SHOT-011 五块（含各自的小标题与正文）
ids = [f"SHOT-EP003-{i:03d}" for i in range(7, 12)]
pos = {sid: t.index(f"\n## {sid}") + 1 for sid in ids}
end = t.index("\n## SHOT-EP003-012")
blocks = {}
for i, sid in enumerate(ids):
    start = pos[sid]
    stop = pos[ids[i + 1]] if i + 1 < len(ids) else end
    blocks[sid] = t[start:stop]

# 新顺序：砸天窗 → 我不敢 → 垫后踹人 → 尖叫像鸡 → 抓缆绳
new_order = [ids[3], ids[0], ids[1], ids[2], ids[4]]   # 010,007,008,009,011
merged = "".join(blocks[sid] for sid in new_order)

# 用新顺序整体替换旧区间
t = t[:pos[ids[0]]] + merged + t[end:]

# 重新编号（按出现顺序 007 起）
counter = [7]
def renum(m):
    sid = f"SHOT-EP003-{counter[0]:03d}"
    counter[0] += 1
    return sid
t = re.sub(r"SHOT-EP003-0(?:07|08|09|10|11)\b", renum, t)

# 砸天窗那镜的职责句里加一句理由，说明顺序为什么在跳机之前
t = t.replace("本版加的笑点——他先砸天窗，碎玻璃兜头浇在还在开车的冯彩虹脸上，他边开边吐玻璃碴。",
              "本版加的笑点——他先砸天窗（顺序在跳机之前），碎玻璃兜头浇在还在开车的冯彩虹脸上，他边开边吐玻璃碴。")
p.write_text(t, encoding="utf-8")
print("EP003 顺序调整完成：砸天窗 → 我不敢 → 垫后踹人 → 尖叫 → 抓缆绳")
