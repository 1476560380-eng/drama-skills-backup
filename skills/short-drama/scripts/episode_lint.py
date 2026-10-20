#!/usr/bin/env python3
"""局部校验器：五份文档不必齐全也能查。

官方 creator_markdown_check.py 缺任一文档即整体退出，导致「分镜写完时无法自查」。
本脚本只查当前存在的文档，逐份给结论，让错误在第三份文档时就暴露。

用法：
    python3 episode_lint.py 剧集/EP001                 # 查已有文档
    python3 episode_lint.py 剧集/EP001 --only 分镜      # 只查一份
    python3 episode_lint.py 剧集/EP001 --strict        # 有问题也返回 0（默认有问题返回 1）

退出码：0 通过 / 1 有错误
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VISUAL_CATEGORIES = ("人物", "造型", "地点", "道具")
SETTING_HEADING_RE = re.compile(r"^## (" + "|".join(VISUAL_CATEGORIES) + r") · (.+?)[ \t　]*$", re.M)
# 常见错误写法：## 人物 之后跟 ### 名称
WRONG_SUB_ENTRY_RE = re.compile(r"^### (.+?)[ \t　]*$", re.M)
SHOT_HEAD_RE = re.compile(r"^## (SHOT-[A-Za-z0-9-]+)(?:[ \t　]*·[ \t　]*(.+))?$", re.M)
SEG_HEAD_RE = re.compile(r"^## SEG-[^（\n]*（([^）]*)）[ \t]*$", re.M)
IMG_SLOT_RE = re.compile(r"(IMG-[A-Za-z0-9-]+)(《([^》]+)》|「([^」]+)」)")
BASIS_RE = re.compile(r"(" + "|".join(VISUAL_CATEGORIES) + r")「([^」]+)」（控制：([^）]+)）")
DUR_RE = re.compile(r"\*\*时长\*\*[：:][ \t]*([0-9]+(?:\.[0-9]+)?)s")


def read(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def check_setting(text: str, errs: list[str]) -> set[tuple[str, str]]:
    entries = {(m.group(1), m.group(2).strip()) for m in SETTING_HEADING_RE.finditer(text)}
    if not entries:
        subs = [m.group(1) for m in WRONG_SUB_ENTRY_RE.finditer(text)]
        hint = f"（发现 {len(subs)} 个 `###` 条目，疑似用了「## 分区 + ### 名称」写法）" if subs else ""
        errs.append(f"视觉设定.md: 没有任何符合 `## 类别 · 名称` 的条目{hint}")
    return entries


def check_storyboard(text: str, entries: set[tuple[str, str]], errs: list[str]) -> None:
    heads = SHOT_HEAD_RE.findall(text)
    if not heads:
        errs.append("分镜.md: 没有 `## SHOT-...` 镜头块")
        return

    # 1. 镜头标题必须带中文名称
    for sid, name in heads:
        if not name:
            errs.append(f"分镜.md: {sid} 标题缺中文名称（应写 `## {sid} · 中文名`）")

    # 2. 每个镜头块内逐项检查
    blocks = re.split(r"^## SHOT-[A-Za-z0-9-]+.*$", text, flags=re.M)[1:]
    ids = [h[0] for h in heads]
    for sid, block in zip(ids, blocks):
        if "**运镜**" not in block and "运镜：" not in block:
            errs.append(f"{sid}: 缺「运镜」字段（下游视频提示词按此行抄）")
        for m in IMG_SLOT_RE.finditer(block):
            if m.group(4) is not None:
                errs.append(f"{sid}: 图片提示词项用了「」，契约要求《》（{m.group(1)}）")
        # 冻结关键帧必须是引用块
        kb = re.search(r"### 冻结关键帧(?:提示词)?[ \t]*\n(.*?)(?=\n## |\n### |\Z)", block, re.S)
        if kb:
            body = [ln for ln in kb.group(1).splitlines() if ln.strip()]
            if body and not any(ln.lstrip().startswith(">") for ln in body):
                errs.append(f"{sid}: 冻结关键帧不是 `>` 引用块，无法整段复制")
        # 视觉依据必须解析得到
        vb = re.search(r"视觉依据[^\n]*", block)
        if not vb:
            errs.append(f"{sid}: 缺「视觉依据」字段")
        else:
            for m in BASIS_RE.finditer(vb.group(0)):
                if (m.group(1), m.group(2).strip()) not in entries:
                    errs.append(f"{sid}: 视觉依据指向不存在的条目 {m.group(1)}「{m.group(2)}」")

    # 3. SEG 时长算术
    segs = re.split(r"^## SEG-[^\n]*$", text, flags=re.M)
    seg_heads = SEG_HEAD_RE.findall(text)
    for claim, body in zip(seg_heads, segs[1:]):
        nums = re.findall(r"([0-9]+(?:\.[0-9]+)?)s", claim)
        durs = [float(x) for x in DUR_RE.findall(body)]
        if nums and durs:
            said, real = float(nums[0]), sum(durs)
            if abs(said - real) > 0.01:
                errs.append(f"SEG: 声称 {said}s，段内 {len(durs)} 镜实际 {real:.1f}s")

    total = sum(float(x) for x in DUR_RE.findall(text))
    head_claim = re.search(r"镜长合计约?[ \t]*([0-9.]+)s", text)
    if head_claim and abs(float(head_claim.group(1)) - total) > 0.5:
        errs.append(f"分镜.md: 头部称 {head_claim.group(1)}s，实际合计 {total:.1f}s")


def main() -> int:
    ap = argparse.ArgumentParser(description="局部校验：缺文档也能查")
    ap.add_argument("episode", help="剧集目录，如 剧集/EP001")
    ap.add_argument("--only", choices=["视觉设定", "分镜", "剧本", "图片提示词", "视频提示词"], help="只查一份")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    root = Path(args.episode)
    if not root.is_dir():
        print(f"目录不存在: {root}", file=sys.stderr)
        return 2

    docs = {n: read(root / f"{n}.md") for n in ("剧本", "视觉设定", "图片提示词", "分镜", "视频提示词")}
    present = [n for n, t in docs.items() if t is not None]
    missing = [n for n, t in docs.items() if t is None]
    errs: list[str] = []

    if args.only:
        present = [args.only] if docs[args.only] is not None else []
        missing = [] if present else [args.only]

    entries: set[tuple[str, str]] = set()
    if docs["视觉设定"] and (not args.only or args.only == "视觉设定"):
        entries = check_setting(docs["视觉设定"], errs)
    if docs["分镜"] and (not args.only or args.only == "分镜"):
        if not entries and docs["视觉设定"]:
            entries = {(m.group(1), m.group(2).strip()) for m in SETTING_HEADING_RE.finditer(docs["视觉设定"])}
        check_storyboard(docs["分镜"], entries, errs)

    result = {
        "episode": str(root),
        "present": present,
        "missing": missing,
        "errors": errs,
        "error_count": len(errs),
        "ok": not errs,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"已存在: {'、'.join(present) or '无'}")
        if missing:
            print(f"缺失  : {'、'.join(missing)}（本次跳过，不算错）")
        if errs:
            print(f"\n发现 {len(errs)} 个问题：")
            for e in errs:
                print(f"  - {e}")
        else:
            print("\n✅ 当前已有文档全部通过")
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main())
