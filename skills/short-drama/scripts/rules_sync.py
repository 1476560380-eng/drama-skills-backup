#!/usr/bin/env python3
"""规则同步检查：项目《文件规则》是否落后于技能模板。

问题背景：项目开工时把技能模板复制一份到 `项目开发/文件规则.md`，之后模板升级，
项目那份就停在旧版本，没人知道差在哪。本脚本把差异摊出来。

用法：
    python3 rules_sync.py <项目目录>            # 检查（默认只读）
    python3 rules_sync.py <项目目录> --apply    # 把模板真缺的规则并进项目（只加不删，先备份）
    python3 rules_sync.py <项目目录> --adopt    # 旧手写规则文件纳管：只加标记，内容一字不改

边界（重要）：
- 只比对 `<!-- RULES:INHERITED-START -->` 与 `<!-- RULES:INHERITED-END -->` 之间的内容；
  `## 项目特化` 段一个字都不碰。
- 措辞不同不当缺失：同一条规则换了个说法，报「改写过」，不算落后、不自动覆盖。
- 没有标记的旧版手写文件：--adopt 纳管，或只报告版本不改写。

退出码：0=同步（或只有措辞差异）；1=真缺规则；2=无规则文件/无法比对。
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
sys.path.insert(0, str(HERE))
from start_project import RULES_TEMPLATE_NAME, RULES_TEMPLATE_VERSION  # noqa: E402

MARK_START = "<!-- RULES:INHERITED-START -->"
MARK_END = "<!-- RULES:INHERITED-END -->"
VER_RE = re.compile(r"继承自：技能 v(\d+\.\d+\.\d+)")
SIM_THRESHOLD = 0.72  # 相似度 >= 此值视为同一条规则的另一种措辞，不算缺失


# ---------- 模板渲染 ----------

def render_template(root: Path) -> str:
    tpl_p = SKILL_DIR / "templates" / RULES_TEMPLATE_NAME
    if not tpl_p.exists():
        raise SystemExit(f"找不到规则模板：{tpl_p}")
    cfg: dict = {}
    cfg_p = root / "short-drama.json"
    if cfg_p.exists():
        try:
            cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cfg = {}
    fmt = cfg.get("format") or {}
    title = cfg.get("title") or root.name
    aspect = fmt.get("aspect_ratio") or "16:9"
    lang = fmt.get("prompt_language") or "en"
    if str(lang).lower() in ("zh-cn", "zh"):
        lang_note = "，走中文商业设定卡（下面全套规则生效）。"
    else:
        lang_note = "，走英文身份板，卡式规则暂不生效；若要切中文卡需创作者裁决后改 `prompt_language`。"
    return (tpl_p.read_text(encoding="utf-8")
            .replace("{{TITLE}}", str(title))
            .replace("{{ASPECT}}", str(aspect))
            .replace("{{PROMPT_LANG}}", str(lang))
            .replace("{{LANG_NOTE}}", lang_note)
            .replace("{{VERSION}}", RULES_TEMPLATE_VERSION)
            .replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d")))


# ---------- 解析 ----------

def extract_block(text: str):
    if MARK_START not in text or MARK_END not in text:
        return None
    return text.split(MARK_START, 1)[1].split(MARK_END, 1)[0]


def base_sec(title: str) -> str:
    """小节名去掉括号补充：`视频提示词.md（本集未建，规则先立）` -> `视频提示词.md`。"""
    return re.split(r"[（(]", title, 1)[0].strip()


def parse_sections(block: str) -> dict:
    """返回 {小节基础名: [规则条目原文]}；保留首次出现顺序。"""
    sections: dict = {}
    cur = "（无小节）"
    sections[cur] = []
    for raw in block.split("\n"):
        line = raw.rstrip()
        if line.startswith("## "):
            cur = base_sec(line[3:])
            sections.setdefault(cur, [])
        elif line.startswith("- ") or (line.startswith("|") and not set(line) <= set("|-: ")):
            # 规则条目既可能是列表也可能是表格行（如「谁在挡」对照表）；表头分隔行不算
            sections[cur].append(line)
    if not sections.get("（无小节）"):
        sections.pop("（无小节）", None)
    return sections


def norm(bullet: str) -> str:
    t = bullet.lstrip("- ").strip()
    if t.startswith("|"):
        t = re.sub(r"\s*\|\s*", " | ", t).strip()
    return re.sub(r"\s+", " ", t)


# ---------- 比对 ----------

def match_bullets(tpl_b: list, proj_b: list):
    """返回 (真缺失, 改写过[(模板原文,项目原文,相似度)], 项目自加)。"""
    proj_n = [(b, norm(b)) for b in proj_b]
    used = set()
    missing = []
    modified = []
    for tb in tpl_b:
        tn = norm(tb)
        best_i, best_r = None, 0.0
        for i, (_pb, pn) in enumerate(proj_n):
            if i in used:
                continue
            r = difflib.SequenceMatcher(None, tn, pn).ratio()
            if r > best_r:
                best_i, best_r = i, r
        if best_r >= 0.999:
            used.add(best_i)
        elif best_r >= SIM_THRESHOLD:
            used.add(best_i)
            modified.append((tb, proj_n[best_i][0], best_r))
        else:
            missing.append(tb)
    extra = [pb for i, (pb, _pn) in enumerate(proj_n) if i not in used]
    return missing, modified, extra


def compare(root: Path, text: str):
    tpl = parse_sections(extract_block(render_template(root)) or "")
    proj = parse_sections(extract_block(text) or "")
    missing, modified, extra = {}, {}, {}
    for sec, bullets in tpl.items():
        m, mo, _ = match_bullets(bullets, proj.get(sec, []))
        if m:
            missing[sec] = m
        if mo:
            modified[sec] = mo
    for sec, bullets in proj.items():
        _, _, ex = match_bullets(tpl.get(sec, []), bullets)
        if ex:
            extra[sec] = ex
    return tpl, proj, missing, modified, extra


def check(root: Path):
    rules_p = root / "项目开发/文件规则.md"
    if not rules_p.exists():
        return 2, [f"❌ {root.name}: 没有 项目开发/文件规则.md（规则只活在会话里，换人接手就丢）"]
    text = rules_p.read_text(encoding="utf-8")
    m = VER_RE.search(text)
    proj_ver = m.group(1) if m else "（未标）"
    if extract_block(text) is None:
        return 2, [f"⚠️ {root.name}: 规则文件是手写版（无继承标记），无法逐条比对；模板当前 v{RULES_TEMPLATE_VERSION}。"
                   f"要纳管跑 `rules_sync.py {root} --adopt`（只加标记，内容一字不改）。"]

    _tpl, _proj, missing, modified, extra = compare(root, text)
    drift = proj_ver != RULES_TEMPLATE_VERSION
    if not missing and not modified and not extra and not drift:
        return 0, [f"✅ {root.name}: 规则与模板 v{RULES_TEMPLATE_VERSION} 完全一致"]

    msgs = [f"{'⚠️' if missing else 'ℹ️'} {root.name}: 项目规则 v{proj_ver} ↔ 模板 v{RULES_TEMPLATE_VERSION}"]
    for sec, bullets in missing.items():
        msgs.append(f"  · 【{sec}】模板有、项目真缺 {len(bullets)} 条：")
        for b in bullets:
            msgs.append(f"      + {norm(b)[:76]}")
    for sec, items in modified.items():
        msgs.append(f"  · 【{sec}】同一规则措辞不同 {len(items)} 条（不算落后，不自动覆盖）：")
        for tb, pb, r in items:
            msgs.append(f"      ~ 模板：{norm(tb)[:60]}")
            msgs.append(f"        项目：{norm(pb)[:60]}  相似度 {r:.2f}")
    for sec, bullets in extra.items():
        msgs.append(f"  · 【{sec}】项目自加 {len(bullets)} 条（换部剧也成立就说「技能升级」升格进模板）：")
        for b in bullets:
            msgs.append(f"      ? {norm(b)[:76]}")
    if drift and not missing:
        msgs.append("  · 版本号落后但条目齐：--apply 会顺带更新头部版本行")
    return (1 if missing else 0), msgs


# ---------- 写入 ----------

def _backup(rules_p: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = rules_p.with_suffix(f".md.bak-{stamp}")
    n = 2
    while bak.exists():
        bak = rules_p.with_suffix(f".md.bak-{stamp}-{n}")
        n += 1
    shutil.copy2(rules_p, bak)
    return bak


def adopt(root: Path):
    """旧手写规则纳管：只加继承标记 + 项目特化段，原有内容一字不改。"""
    rules_p = root / "项目开发/文件规则.md"
    if not rules_p.exists():
        return 2, ["无规则文件，无需纳管（新项目开工即自动带标记）"]
    text = rules_p.read_text(encoding="utf-8")
    if extract_block(text) is not None:
        return 0, ["已有继承标记，无需纳管；直接跑检查或 --apply"]
    lines = text.split("\n")
    start_i = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    head, body = lines[:start_i], lines[start_i:]
    existing = next((i for i, l in enumerate(body) if l.startswith("## 项目特化")), None)
    if existing is None:
        tail = ["", "---", "", "## 项目特化（只本剧生效，永不回流技能层）", "",
                "> 只对本剧成立的写法要求写在这里；`rules_sync.py` 不会改动本段。", "",
                "- （本项目特有规则从这里往下写）", ""]
        end_i = len(body)
        body = body + tail
    else:
        end_i = existing
    new_text = "\n".join(head + [MARK_START] + body[:end_i] + [MARK_END] + body[end_i:])
    new_text = VER_RE.sub(f"继承自：技能 v{RULES_TEMPLATE_VERSION}", new_text)
    if "继承自：技能 v" not in new_text:
        new_text = new_text.replace("\n\n", f"\n\n> 继承自：技能 v{RULES_TEMPLATE_VERSION} 模板（纳管于 "
                                               f"{datetime.now().strftime('%Y-%m-%d')}）\n\n", 1)
    bak = _backup(rules_p)
    rules_p.write_text(new_text, encoding="utf-8")
    return 0, [f"✅ 已纳管（原有内容一字未改，只加标记）：备份 {bak.name}",
               f"   下一步：`python3 rules_sync.py {root}` 看还差哪几条"]


def apply(root: Path):
    """只追加模板真缺的条目（措辞不同不算缺），不删不改已有句子。写入前备份。"""
    rules_p = root / "项目开发/文件规则.md"
    if not rules_p.exists():
        return 2, ["无规则文件，无法 apply（新项目直接跑 start_project.py 即自动生成）"]
    text = rules_p.read_text(encoding="utf-8")
    if extract_block(text) is None:
        return 2, ["手写版规则文件不做自动写入——先跑 --adopt 纳管，再 apply"]
    tpl, proj, missing, _mod, _extra = compare(root, text)
    if not missing:
        new_text = VER_RE.sub(f"继承自：技能 v{RULES_TEMPLATE_VERSION}", text)
        if new_text != text:
            _backup(rules_p)
            rules_p.write_text(new_text, encoding="utf-8")
            return 0, [f"✅ 条目已齐，只更新头部版本为 v{RULES_TEMPLATE_VERSION}（已备份）"]
        return 0, ["无变化，未写入"]

    lines = text.split("\n")
    out = []
    cur = "（无小节）"
    pending = {k: list(v) for k, v in missing.items()}
    for line in lines:
        if line.startswith("## "):
            sec = base_sec(line[3:].strip())
            if cur in pending:
                while out and out[-1].strip() == "":
                    out.pop()
                out.extend(pending.pop(cur))
                out.append("")
            cur = sec
        if line == MARK_END:
            if cur in pending:
                while out and out[-1].strip() == "":
                    out.pop()
                out.extend(pending.pop(cur))
                out.append("")
            for sec, bullets in list(pending.items()):
                out.append(f"## {sec}")
                out.append("")
                out.extend(bullets)
                out.append("")
                pending.pop(sec)
        out.append(line)
    new_text = VER_RE.sub(f"继承自：技能 v{RULES_TEMPLATE_VERSION}", "\n".join(out))
    bak = _backup(rules_p)
    rules_p.write_text(new_text, encoding="utf-8")
    total = sum(len(v) for v in missing.values())
    return 0, [f"✅ 并入模板真缺的 {total} 条规则，版本更新 v{RULES_TEMPLATE_VERSION}；备份 {bak.name}",
               "   建议接着跑 project_card.py 刷新项目卡"]


def main() -> int:
    ap = argparse.ArgumentParser(description="项目文件规则 vs 技能模板 同步检查")
    ap.add_argument("project", help="项目目录")
    ap.add_argument("--apply", action="store_true", help="并入模板真缺的条目（只加不删，先备份）")
    ap.add_argument("--adopt", action="store_true", help="旧手写规则文件加继承标记（内容不改，先备份）")
    args = ap.parse_args()
    root = Path(args.project).expanduser()
    if not root.is_dir():
        print(f"❌ 目录不存在：{root}", file=sys.stderr)
        return 2
    if args.adopt:
        code, msgs = adopt(root)
    elif args.apply:
        code, msgs = apply(root)
    else:
        code, msgs = check(root)
    print("\n".join(msgs))
    return code


if __name__ == "__main__":
    sys.exit(main())
