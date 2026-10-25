#!/usr/bin/env python3
"""生成/刷新《项目卡》——一屏读完的项目口径索引。

用法：
    python3 project_card.py <项目根目录>          # 生成或刷新 项目开发/项目卡.md
    python3 project_card.py <项目根目录> --check   # 只检查卡片是否过期（退出码 1=过期）

设计边界：卡是索引不是真相。真相仍在 short-drama.json、开工清单与各集文档里。
本脚本只读这些源文件，把口径汇总成一屏，并把互相矛盾的地方列进「待裁决」。
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

DOCS = ("剧本.md", "视觉设定.md", "图片提示词.md", "分镜.md", "视频提示词.md")


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def fmt_sec(v) -> str:
    """秒数格式化：100 / 100.0 / 90.5 都正确，不会再出现 100→1s。"""
    if v in (None, ""):
        return "（未定）"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return f"{v}"
    return f"{int(f)}s" if f == int(f) else f"{f:g}s"


def pick(pattern: str, text: str, default: str = "") -> str:
    m = re.search(pattern, text, re.M)
    return m.group(1).strip() if m else default


def episode_dirs(root: Path) -> list[Path]:
    ep = root / "剧集"
    if not ep.is_dir():
        return []
    return sorted(d for d in ep.iterdir() if d.is_dir() and re.match(r"EP\d+", d.name))


def collect(root: Path) -> dict:
    cfg_path = root / "short-drama.json"
    cfg = json.loads(read(cfg_path) or "{}")
    fmt = cfg.get("format") or {}
    checklist_p = root / "项目开发/开工清单.md"
    checklist = read(checklist_p)
    rules_p = root / "项目开发/文件规则.md"
    rules = read(rules_p)

    episodes = []
    for d in episode_dirs(root):
        sb = read(d / "分镜.md")
        vs = read(d / "视觉设定.md")
        eps = {
            "name": d.name,
            "docs": [n for n in DOCS if (d / n).exists()],
            "shots": len(re.findall(r"^## SHOT-", sb, re.M)) if sb else 0,
            "total": pick(r"镜长合计约?\s*([\d.]+)s", sb),
            "style": pick(r"画风统一句[^`]*`([^`]+)`", sb),
            "strict": pick(r"^- (?:\*\*)?(?:强制项|规格)(?:\*\*)?[：:]\s*(.+)$", sb),
            "voices": pick(r"配音音色总表[：:]\s*(.+)", sb),
            "people": re.findall(r"^## (?:人物|造型) · (.+)$", vs, re.M) if vs else [],
            "aliases": dict(re.findall(r"^- 画面代称[：:]\s*(.+)$", vs, re.M) and [] or []),
        }
        # 画面代称：按条目块取
        alias_map = {}
        if vs:
            for m in re.finditer(r"^## (?:人物|造型) · (.+?)\s*\n(.*?)(?=^## |\Z)", vs, re.M | re.S):
                a = re.search(r"(?:\*\*)?画面代称(?:\*\*)?[：:]\s*(.+)", m.group(2))
                if a:
                    alias_map[m.group(1).strip()] = a.group(1).strip()
        eps["alias_map"] = alias_map
        episodes.append(eps)

    model_check = pick(r"\|\s*目标视频模型\s*\|\s*([^|]+)\|", checklist)
    style_check = pick(r"\|\s*画风\s*\|\s*([^|]+)\|", checklist)
    lang_check = pick(r"\|\s*关键帧正文语言\s*\|\s*([^|]+)\|", checklist)
    genre = pick(r"\|\s*题材赛道\s*\|\s*([^|]+)\|", checklist)

    prod = (cfg.get("creator_authority") or {}).get("production_profile") or {}
    choices = prod.get("choices") or {}

    return {
        "title": cfg.get("title") or root.name,
        "json_model": choices.get("target_video_model", ""),
        "json_model_status": prod.get("status", "unset"),
        "json_lang": (fmt.get("prompt_language") or cfg.get("prompt_language", "")),
        "json_aspect": fmt.get("aspect_ratio", ""),
        "json_seconds": fmt.get("target_seconds_per_episode"),
        "json_eps": fmt.get("episode_count"),
        "checklist_model": model_check.strip(),
        "checklist_style": style_check.strip(),
        "checklist_lang": lang_check.strip(),
        "genre": genre.strip(),
        "episodes": episodes,
        "rules": rules,
        "rules_exists": rules_p.exists(),
        "sources": [cfg_path, checklist_p, rules_p] + [root / "剧集" / e["name"] / n
                                             for e in episodes for n in ("分镜.md", "视觉设定.md")
                                             if (root / "剧集" / e["name"] / n).exists()],
    }


def build(root: Path, data: dict) -> str:
    eps = data["episodes"]
    latest = eps[-1] if eps else None
    style = next((e["style"] for e in reversed(eps) if e.get("style")), "")
    strict = next((e["strict"] for e in reversed(eps) if e.get("strict")), "")
    aliases = {}
    people = []
    voices = ""
    for e in eps:
        for k, v in (e.get("alias_map") or {}).items():
            aliases[k] = v
        for p in e["people"]:
            if p not in people:
                people.append(p)
        if e.get("voices") and not voices:
            voices = e["voices"]

    conflicts = []
    if data["json_model"] and data["checklist_model"] and data["json_model"] not in data["checklist_model"]:
        conflicts.append(f"视频模型：json `{data['json_model']}` ↔ 开工清单 `{data['checklist_model']}`")
    if not data["json_model"] and data["checklist_model"] and not data["checklist_model"].startswith("未定"):
        conflicts.append(f"视频模型：json 未写（`{data['json_model_status']}`）但开工清单写 `{data['checklist_model']}`")
    # 关键帧正文语言（开工清单）与图片提示词语言（json.prompt_language）是两个口径，不判冲突
    for e in eps:
        sb = read(root / "剧集" / e["name"] / "分镜.md")
        head_moody = "moody" in (e.get("style") or "")
        body_midkey = "mid-key exposure" in sb
        if sb and head_moody and body_midkey:
            conflicts.append(f"画风句（{e['name']}）：头部仍写 `moody`，但关键帧正文已改成 `mid-key exposure`——同集内两处口径不一致")
    # 设定图口径：json 的 prompt_language 与文件规则要求的口径是否打架
    lang = (data["json_lang"] or "").lower()
    rules_text = data.get("rules") or ""
    if lang and lang not in ("zh-cn", "zh") and "中文商业设定卡" in rules_text:
        kinds = [k for k in ("T-CHA", "T-PRP", "T-LOC", "T-UI") if k in rules_text]
        conflicts.append(
            f"设定图口径：`prompt_language` 是 `{data['json_lang']}`（英文身份板），但《文件规则》要求走中文商业设定卡"
            f"（{('、'.join(kinds)) or '卡式'}：版式+HEX 色板+留白档案卡）；两者不可混写，需创作者裁决"
        )
    if data["checklist_style"] and data["checklist_style"] not in ("未定", "—", "") and style and data["checklist_style"] not in style:
        conflicts.append(f"画风：开工清单 `{data['checklist_style']}` ↔ 分镜头部画风句不一致")

    L = []
    L.append(f"# 项目卡 · {data['title']}")
    L.append("")
    L.append(f"> 生成于 {time.strftime('%Y-%m-%d %H:%M')} ｜ 本卡由 `scripts/project_card.py` 生成，**手改无效**（下次生成会覆盖）。")
    L.append("> 卡是索引不是真相：口径以 `short-drama.json`、`项目开发/开工清单.md` 与各集文档为准。")
    L.append("")
    L.append("## 制作口径")
    L.append("")
    model = data["json_model"] or data["checklist_model"] or "（未定）"
    L.append(f"- 画幅：**{data['json_aspect'] or '（未定）'}** ｜ 集长：**{fmt_sec(data['json_seconds'])}** ｜ 集数：**{data['json_eps'] or '（未定）'}**")
    L.append(f"- 目标视频模型：**{model}** ｜ 题材：{data['genre'] or '（未填）'}")
    L.append(f"- 关键帧正文语言：**{data['checklist_lang'] or '（未填）'}** ｜ 图片提示词语言：**{data['json_lang'] or '（未填）'}**（两者本就不同口径）")
    L.append("")
    L.append("## 画风统一句（逐字继承，不重写）")
    L.append("")
    styles = [(e["name"], e.get("style")) for e in eps if e.get("style")]
    if styles:
        uniq = {}
        for name, st in styles:
            uniq.setdefault(st, []).append(name)
        for st, names in uniq.items():
            L.append(f"- **{'、'.join(names)}**：`{st}`")
    else:
        L.append("（分镜头部未写）")
    L.append("")
    L.append("## 强制项（写新镜自动带）")
    L.append("")
    L.append(f"{strict or '（分镜头部未写强制项 → 按默认全强制：轴线锁、亮度口径）'}")
    L.append("")
    L.append("## 文件规则（每个文件写什么、必须遵守什么）")
    L.append("")
    if data.get("rules"):
        L.append("> 规则正文源头：`项目开发/文件规则.md`（此处整段抄录，改规则改那个文件；卡里手改下次覆盖）。")
        L.append("")
        body = data["rules"]
        # 去掉规则文件自身的标题行与首段引用块，避免在卡里重复两级标题
        lines = body.splitlines()
        i = 0
        while i < len(lines) and (lines[i].startswith("# ") or lines[i].startswith(">")):
            i += 1
        # 规则正文里的二级标题降为三级，避免撑破项目卡自身的章节层级
        L.append("\n".join(lines[i:]).strip().replace("\n## ", "\n### "))
    else:
        L.append("（项目里还没有 `项目开发/文件规则.md`——规则只散落在对话里，换个人接手就丢）")
    L.append("")
    if people:
        L.append("## 人物与画面代称")
        L.append("")
        L.append("| 条目 | 画面代称 |")
        L.append("|---|---|")
        for p in people:
            L.append(f"| {p} | {aliases.get(p, '—')} |")
        L.append("")
    if voices:
        L.append("## 配音音色")
        L.append("")
        L.append(f"```text\n{voices}\n```")
        L.append("")
    L.append("## 当前进度")
    L.append("")
    L.append("| 集 | 已有文档 | 镜头 | 时长 |")
    L.append("|---|---|---|---|")
    for e in eps:
        L.append(f"| {e['name']} | {'、'.join(e['docs']) or '（空）'} | {e['shots'] or '—'} | {e['total'] + 's' if e['total'] else '—'} |")
    if not eps:
        L.append("| — | 还没有剧集目录 | — | — |")
    L.append("")
    L.append("## 待裁决（源文件互相矛盾，不要自行挑一个）")
    L.append("")
    if conflicts:
        for c in conflicts:
            L.append(f"- ⚠️ {c}")
    else:
        L.append("无")
    L.append("")
    L.append("## 源文件（卡过期就比 mtime）")
    L.append("")
    for p in data["sources"]:
        try:
            st = p.stat()
            L.append(f"- `{p.relative_to(root)}` · {time.strftime('%Y-%m-%d %H:%M', time.localtime(st.st_mtime))}")
        except Exception:
            pass
    L.append("")
    return "\n".join(L)


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：project_card.py <项目根目录> [--check]", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).expanduser().resolve()
    check = "--check" in sys.argv
    if not root.is_dir():
        print(f"目录不存在：{root}", file=sys.stderr)
        return 2
    data = collect(root)
    card = root / "项目开发/项目卡.md"
    if check:
        if not card.exists():
            print(f"项目卡不存在：{card}")
            return 1
        card_m = card.stat().st_mtime
        stale = [p for p in data["sources"] if p.exists() and p.stat().st_mtime > card_m + 1]
        if stale:
            print("项目卡已过期，以下源文件比卡新：")
            for p in stale:
                print(f"  - {p.relative_to(root)}")
            return 1
        print("项目卡是最新的")
        return 0
    card.parent.mkdir(parents=True, exist_ok=True)
    new = build(root, data)
    if card.exists():
        old = read(card)
        strip = lambda t: "\n".join(l for l in t.splitlines() if not l.startswith("> 生成于"))
        if strip(old) == strip(new):
            print(f"内容无变化，跳过写入：{card}")
            return 0
    card.write_text(new, encoding="utf-8")
    print(f"已生成 {card}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
