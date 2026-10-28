#!/usr/bin/env python3
"""参考图生命周期核对（分类登记 → 解析报告 → 锚图 → 绑定）。

用法：
    python3 ref_check.py <项目根>                 # 全量核对，退出码 1 = 有问题
    python3 ref_check.py <项目根> --json          # 机器可读
    python3 ref_check.py <项目根> --change-anchor # 换锚传播账
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CLASSES = ("画风", "人物形象", "环境", "动作", "道具")
ALLOWED = {
    "画风": {"风格"},
    "人物形象": {"身份", "造型状态"},
    "环境": {"地理", "构图"},
    "道具": {"身份", "造型状态"},
    "动作": {"构图", "效果"},
}
REQUIRED_REPORT_FIELDS = ("分类", "色板", "光位", "质感", "冲突", "绑定")
ANCHOR_MARKS = ("✅", "√", "Y", "y", "是", "✓")


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def episode_dirs(root: Path) -> list[Path]:
    ep = root / "剧集"
    if not ep.is_dir():
        return []
    return sorted(d for d in ep.iterdir() if d.is_dir() and re.match(r"EP\d+", d.name))


def parse_registry(root: Path) -> list[dict]:
    p = root / "输入/参考图/登记表.md"
    if not p.exists():
        return []
    rows: list[dict] = []
    header: list[str] | None = None
    for line in read(p).splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        row = dict(zip(header, cells))
        if not row.get("文件"):
            continue
        rows.append(row)
    return rows


def parse_ref_slots(text: str) -> list[dict]:
    """抓 REF 槽位：REF-x（顺序：n）· 路径《名称》（用途：X；控制：…；不得控制：…）"""
    out = []
    pat = re.compile(
        r"REF-[^（(]+?[（(]顺序[：:]\s*(\d+)[）)]\s*·\s*([^《]+?)《([^》]+)》"
        r"[（(]用途[：:]\s*([^；;）)]+)([^）)]*)[）)]"
    )
    for m in pat.finditer(text):
        tail = m.group(5)
        c = re.search(r"控制[：:]\s*([^；;）)]*)", tail.replace("不得控制", ""))
        noc = re.search(r"不得控制[：:]\s*([^；;）)]*)", tail)
        out.append({
            "order": int(m.group(1)),
            "path": m.group(2).strip(),
            "name": m.group(3).strip(),
            "use": m.group(4).strip(),
            "control": c.group(1).strip() if c else "",
            "not_control": noc.group(1).strip() if noc else "",
        })
    return out


def split_secondary(cell: str) -> list[str]:
    """次类列可能是 `—`/空/`环境`/`环境、道具`/`环境/道具`。"""
    if not cell:
        return []
    cell = cell.strip().strip("—")
    parts = re.split(r"[、,，/／\s]+", cell)
    return [x.strip() for x in parts if x.strip() in CLASSES]


def allowed_for(row: dict) -> tuple[set, list[str]]:
    """一张图允许的用途集合 = 主类 + 已声明的次类。"""
    cls = row.get("主类", "").strip()
    sec = split_secondary(row.get("次类", ""))
    allowed = set(ALLOWED.get(cls, set()))
    for c in sec:
        allowed |= ALLOWED.get(c, set())
    return allowed, sec


def check(root: Path) -> dict:
    errors: list[str] = []
    hints: list[str] = []
    rows = parse_registry(root)

    if not rows:
        hints.append("无参考图登记（本集/本项目还没有参考图，按无参考流程走）")

    by_path: dict[str, dict] = {}
    anchors: dict[str, list[str]] = {}
    for r in rows:
        f, cls = r.get("文件", "").strip(), r.get("主类", "").strip()
        if cls not in CLASSES:
            errors.append(f"登记表：`{f}` 主类 `{cls}` 不合法（只能是 {'/'.join(CLASSES)}）")
            continue
        by_path[f] = r
        if r.get("锚", "").strip() in ANCHOR_MARKS:
            anchors.setdefault(cls, []).append(f)
        if not (root / f).exists():
            errors.append(f"登记表：文件不存在 `{f}`（登记了但项目里没有）")

    for cls, fs in anchors.items():
        if len(fs) > 1:
            errors.append(f"锚图：{cls} 类有 {len(fs)} 张锚（{'、'.join(fs)}），每类最多 1 张")

    report = root / "输入/参考图/解析.md"
    if rows and not report.exists():
        errors.append("解析报告缺失：有参考图但无 `输入/参考图/解析.md`")
    elif report.exists():
        rt = read(report)
        for k in REQUIRED_REPORT_FIELDS:
            if k not in rt:
                errors.append(f"解析报告缺少「{k}」（六项：分类、色板、光位、质感、冲突、绑定）")
        if "观察状态" not in rt and "未验证" not in rt:
            hints.append("解析报告未声明「观察状态」（实际看过图 / 未验证）")

    slots: list[dict] = []
    for ep in episode_dirs(root):
        for doc in ("图片提示词.md", "分镜.md"):
            t = read(ep / doc)
            if not t:
                continue
            for s in parse_ref_slots(t):
                s["src"] = f"{ep.name}/{doc}"
                slots.append(s)
                f = s["path"]
                if re.match(r"^(PLAN|IMG|SHOT)-", f):
                    errors.append(f"{s['src']}：`{f}` 写在 REF 槽位的路径位——外部图/条目引用不能称 REF，应改 PLAN-")
                    continue
                if f not in by_path:
                    if (root / f).exists():
                        errors.append(f"{s['src']}：`{f}` 未在登记表登记（先分类登记再绑定）")
                    else:
                        errors.append(f"{s['src']}：`{f}` 项目里不存在（失效引用）")
                    continue
                cls = by_path[f].get("主类", "").strip()
                allowed, sec_classes = allowed_for(by_path[f])
                if s["use"] not in allowed:
                    extra = ""
                    if sec_classes:
                        extra = f"；已有次类 {'/'.join(sec_classes)} 也未覆盖它"
                    errors.append(
                        f"{s['src']}：`{f}` 是 {cls} 类，用途却写 `{s['use']}`"
                        f"（{cls} 类只允许 {'/'.join(sorted(ALLOWED.get(cls, set())))}）"
                        f"——一图多槽须在登记表「次类」列先声明{extra}"
                    )

    uses: dict[str, set] = {}
    for s in slots:
        if s["path"] in by_path:
            uses.setdefault(s["path"], set()).add(s["use"])
    for f, us in uses.items():
        cls = by_path[f].get("主类", "").strip()
        ok, sec = allowed_for(by_path[f])
        cross = us - ok
        if cross:
            hints.append(
                f"一图多槽：`{f}`（主类 {cls}）被当作 {'、'.join(sorted(us))}，其中 {'、'.join(sorted(cross))} 超出主类+次类范围"
            )
        elif len(us) > 1:
            hints.append(
                f"一图多槽：`{f}`（主类 {cls}，次类 {'/'.join(sec) or '无'}）同时用作 {'、'.join(sorted(us))}，每个槽位用途单一即合规"
            )

    # 画风参考必须带负面词：分镜按镜头块查，图片提示词按条目块查（设定卡正文在后者）
    for ep in episode_dirs(root):
        for doc, head in (("分镜.md", r"\n(?=## SHOT-)"), ("图片提示词.md", r"\n(?=## IMG-)")):
            text = read(ep / doc)
            if "REF-" not in text:
                continue
            for blk in re.split(head, text):
                m = re.match(r"## (SHOT-\S+|IMG-\S+)", blk)
                if not m or "REF-" not in blk:
                    continue
                style_ref = any(
                    by_path.get(s["path"], {}).get("主类", "").strip() == "画风" or s["use"] == "风格"
                    for s in parse_ref_slots(blk)
                )
                if style_ref and not re.search(r"不复制|do not copy", blk, re.I):
                    hints.append(
                        f"{ep.name}/{doc}：{m.group(1)} 挂了画风参考，正文缺「不复制参考中的人物与场景内容」负面词"
                    )

    for cls, fs in anchors.items():
        for f in fs:
            if f not in uses:
                hints.append(f"锚图：{cls} 锚 `{f}` 还没被任何 REF 槽位引用")

    return {
        "root": str(root),
        "registry_rows": len(rows),
        "anchors": anchors,
        "ref_slots": len(slots),
        "errors": errors,
        "hints": hints,
    }


def change_anchor(root: Path) -> int:
    state_p = root / ".short-drama/ref_anchors.json"
    cur = check(root)
    cur_anchors = cur["anchors"]
    old_anchors: dict = {}
    if state_p.exists():
        try:
            old_anchors = json.loads(read(state_p))
        except Exception:
            old_anchors = {}
    changed = {}
    for cls in set(cur_anchors) | set(old_anchors):
        a, b = old_anchors.get(cls, []), cur_anchors.get(cls, [])
        if a != b:
            changed[cls] = {"旧": a, "新": b}
    if not changed:
        print("锚图无变化")
    else:
        print("锚图变更（只影响变更之后的条目，历史集数不回写）：")
        for cls, d in changed.items():
            print(f"  - {cls}：{'、'.join(d['旧']) or '（无）'} → {'、'.join(d['新']) or '（无）'}")
        touched = []
        for ep in episode_dirs(root):
            for doc in ("图片提示词.md", "分镜.md"):
                t = read(ep / doc)
                olds = [f for v in changed.values() for f in v["旧"] if f]
                if any(o in t for o in olds):
                    touched.append(f"{ep.name}/{doc}")
        print("  受影响文件：" + ("、".join(touched) if touched else "（无引用旧锚的条目）"))
    state_p.parent.mkdir(parents=True, exist_ok=True)
    state_p.write_text(json.dumps(cur_anchors, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("用法：ref_check.py <项目根> [--json] [--change-anchor]", file=sys.stderr)
        return 2
    root = Path(args[0]).expanduser().resolve()
    if not root.is_dir():
        print(f"目录不存在：{root}", file=sys.stderr)
        return 2
    if "--change-anchor" in args:
        return change_anchor(root)
    res = check(root)
    if "--json" in args:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 1 if res["errors"] else 0
    print(f"参考图核对 · {root.name}")
    print(f"登记 {res['registry_rows']} 张 ｜ 锚 {len(res['anchors'])} 类 ｜ REF 槽位 {res['ref_slots']} 处")
    for a, fs in res["anchors"].items():
        print(f"  锚 · {a}：{'、'.join(fs)}")
    if res["errors"]:
        print(f"\n发现 {len(res['errors'])} 个问题：")
        for e in res["errors"]:
            print(f"  ✗ {e}")
    else:
        print("\n✅ 分类、锚图、绑定全部通过")
    if res["hints"]:
        print(f"\n提示 {len(res['hints'])} 条：")
        for h in res["hints"]:
            print(f"  ⓘ {h}")
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
