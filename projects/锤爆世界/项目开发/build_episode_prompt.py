#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为每一集生成本集自己的「图片提示词.md」：只收该集分镜实际引用到的卡，正文逐字搬运。
用法：python3 项目开发/build_episode_prompt.py EP002 [EP003 ...] [--write]
来源：剧集/EP001/图片提示词.md + 设定集/ 下五个卡片文件
"""
import re, pathlib, sys, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = [
    ROOT / "剧集/EP001/图片提示词.md",
    ROOT / "设定集/图片提示词-常驻人物.md",
    ROOT / "设定集/人物卡提示词-余下19张.md",
    ROOT / "设定集/场景道具提示词-P2批(EP002-005).md",
    ROOT / "设定集/地点卡提示词-余下9张(EP007-018).md",
    ROOT / "设定集/道具与载具提示词-扫尾21张.md",
]
KIND_NAME = {"C": "人物", "G": "群像", "L": "地点", "P": "道具", "M": "载具"}


def catalog():
    cat = {}
    for f in SRC:
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        for chunk in re.split(r"\n(?=## IMG-)", "\n" + t):
            m = re.match(r"## (IMG-\S+) · (.+)", chunk)
            if m:
                cat[m.group(1)] = (m.group(2).strip(), chunk.strip())
    return cat


def build(ep, cat, write):
    d = ROOT / "剧集" / ep
    fan = d / "分镜.md"
    if not fan.exists():
        print(f"{ep}: 缺分镜.md，跳过"); return
    t = fan.read_text(encoding="utf-8")
    refs = collections.OrderedDict()
    for cid in re.findall(r"(IMG-[\w\-]+)《", t):
        refs[cid] = None
    # 按类型排序：人物 → 群像 → 地点 → 道具 → 载具
    order = {"C": 0, "G": 1, "L": 2, "P": 3, "M": 4}
    def k(cid):
        m = re.search(r"-(C|G|L|P|M)\d+$", cid)
        return (order.get(m.group(1) if m else "Z", 9), cid)
    ids = [c for c in refs if c in cat]
    missing = [c for c in refs if c not in cat]
    ids.sort(key=k)

    L = []
    L.append(f"# {ep} 本集图片提示词")
    L.append("")
    def cnt(code):
        return sum(1 for c in ids if re.search("-" + code + r"\d+$", c))
    L.append(f"> **本集出图要用的 {len(ids)} 张卡**：{cnt('C')} 人物／{cnt('G')} 群像／{cnt('L')} 地点／{cnt('P')} 道具／{cnt('M')} 载具。")
    L.append(f"> **只收本集用到的**：卡正文逐字取自资产库（`设定集/` 与 EP001），编号与卡名一字未改，出图口径与全集一致。")
    L.append("> **画风口径**：3D 国漫半写实，渲染尾逐字 `3D Chinese animation style，semi-realistic，high-end CG，studio lighting，soft film grain`。")
    L.append("> **用法**：找到卡 → 复制【可复制提示词】下面那一整段 → 出图 16:9 / 4K。人物卡与群像卡**不挂参考图**；地点卡只挂 `ref-style-t01/t03` 裁切材质块（写明「不挂」的别挂）。")
    if missing:
        L.append(f"> ⚠️ 分镜里引用了但资产库里还没有的卡：{'、'.join(missing)}——出图前需要补卡或改引用。")
    L.append("")
    L.append("## 本集卡表")
    L.append("")
    L.append("| 编号 | 卡名 | 类别 |")
    L.append("|---|---|---|")
    for cid in ids:
        m = re.search(r"-(C|G|L|P|M)\d+$", cid)
        L.append(f"| {cid} | {cat[cid][0]} | {KIND_NAME.get(m.group(1) if m else '?', '—')} |")
    L.append("")
    L.append("---")
    L.append("")
    for cid in ids:
        L.append(cat[cid][1])
        L.append("")
    out = "\n".join(L) + "\n"
    if write:
        # 保留同名备份
        p = d / "图片提示词.md"
        if p.exists():
            import shutil, datetime
            shutil.copy2(p, d / f"图片提示词.md.bak-{datetime.datetime.now():%Y%m%d-%H%M}")
        p.write_text(out, encoding="utf-8")
        print(f"{ep}: ✅ 写入 {len(ids)} 张卡 → {p.relative_to(ROOT)}（{len(out.encode())/1024:.0f}KB）")
    else:
        print(f"{ep}: 干跑 {len(ids)} 张卡" + (f"，缺 {missing}" if missing else ""))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    cat = catalog()
    for ep in args:
        build(ep, cat, write)
