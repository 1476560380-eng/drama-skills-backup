#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验「只改排版、不改内容」。

做法：按镜号切块，取那一镜的 11 个字段值（首帧锁定/运镜/画面/镜头技术/动作情绪/位置承接/OS/画外音/音效/台词）
与包级风格提示词，去掉全部标点空白后逐字比对。结构、缩进、分隔符不计。
"""
import pathlib
import re

FIELDS = ["时间标识", "首帧锁定", "运镜", "画面", "镜头技术", "动作/情绪",
          "位置承接", "OS", "画外音", "音效", "台词"]


def squash(v):
    return re.sub(r"[^\w\u4e00-\u9fff]", "", v)


def fields_of(text):
    shots, styles = {}, []
    marks = list(re.finditer(r"(?:^镜头\d+ / |^### 镜头 \d+ · )(SHOT-[\w-]+)", text, re.M))
    for i, m in enumerate(marks):
        sid = m.group(1)
        blk = text[m.start(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        d = {}
        for f in FIELDS:
            mm = re.search(r"(?:【" + f + r"】|^- \*\*" + re.escape(f) + r"\*\*：)([^\n]*)", blk, re.M)
            if mm:
                d[f] = squash(mm.group(1))
        shots[sid] = d
    for m in re.finditer(r"(?:【本节风格提示词】|```text\n)([^\n]*)", text):
        v = squash(m.group(1))
        if "禁止出现字幕" in v:
            styles.append(v)
    return shots, styles


def main():
    ok = True
    for ep in ["EP001", "EP002", "EP003", "EP004", "EP005"]:
        for tag, fn in [("原", "多镜容器提示词-15秒包.md"), ("搞", "多镜容器提示词-15秒包-搞笑夸张版.md")]:
            old_p = pathlib.Path(f"/tmp/fmt_old/{ep}_{tag}.md")
            new_p = pathlib.Path(f"剧集/{ep}/{fn}")
            if not old_p.exists():
                continue
            so, sto = fields_of(old_p.read_text(encoding="utf-8"))
            sn, stn = fields_of(new_p.read_text(encoding="utf-8"))
            bad = []
            if set(so) != set(sn):
                bad.append(f"镜号集合不同：{sorted(set(so) ^ set(sn))[:4]}")
            for sid in sorted(set(so) & set(sn)):
                for f in FIELDS:
                    a, b = so[sid].get(f, "<缺>"), sn[sid].get(f, "<缺>")
                    if a != b:
                        bad.append(f"{sid}「{f}」不一致\n      旧:{a[:70]}\n      新:{b[:70]}")
            if sorted(sto) != sorted(stn):
                bad.append(f"风格句 {len(sto)} vs {len(stn)}")
            print(f"{ep} {tag}｜{len(so)} 镜 vs {len(sn)} 镜｜风格句 {len(sto)} vs {len(stn)}｜"
                  + ("✅ 等价" if not bad else "❌ 有差异"))
            for b in bad[:6]:
                print("   ", b)
            ok &= not bad
    print("\n" + ("✅ 十份全部只改排版、内容逐字一致" if ok else "❌ 存在内容差异，见上"))


if __name__ == "__main__":
    main()
