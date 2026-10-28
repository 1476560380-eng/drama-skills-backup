#!/usr/bin/env python3
"""新项目开工：四项必答 → 建项目目录 + 写开工清单。

用户开新项目时先把四项问清（项目名 / 每集秒数 / 目标模型 / 题材），拿到答案后用本脚本建项目。
缺任何一项都拒绝执行，避免「先做起来再补配置」造成返工。

用法：
    python3 start_project.py --dir ~/duanju/新剧名 --title "新剧名" \
        --seconds 90 --episodes 10 --model seedance-2.0 --genre 复仇爽剧 \
        [--aspect-ratio 16:9] [--novel 输入/原著.txt] [--style "2D 国漫，冷灰调"]

输出：项目目录 + 项目开发/开工清单.md，并打印下一步该跑哪个技能。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent  # short-drama/


def find_project_tool() -> Path:
    """project_tool.py 是官方文件；备份仓库里只存改过的文件，所以要兜底找已安装的那份。"""
    candidates = [HERE / "project_tool.py"]
    candidates += sorted(Path.home().glob(".hermes/profiles/*/skills/short-drama/scripts/project_tool.py"))
    candidates += sorted(Path.home().glob(".hermes/skills/short-drama/scripts/project_tool.py"))
    for c in candidates:
        if c.exists():
            return c
    raise SystemExit("找不到 project_tool.py：先安装官方 short-drama 技能再运行本脚本")

STEP_BY_INPUT = {
    "novel": ("$short-drama-novel-analyze", "先拆原著：章节索引 → 改编价值快评（含题材赛道对照）→ 分集候选"),
    "idea": ("$short-drama-develop", "没有原著文本时从点子/梗概开发：故事引擎 → 分集地图 → 改编契约"),
}


def main() -> int:
    ap = argparse.ArgumentParser(description="新项目开工（四项必答）")
    ap.add_argument("--dir", required=True, help="项目目录")
    ap.add_argument("--title", required=True, help="项目名/剧名")
    ap.add_argument("--seconds", type=float, required=True, help="单集目标秒数")
    ap.add_argument("--episodes", type=int, default=None, help="集数（不知道可省略）")
    ap.add_argument("--model", required=True, help="目标视频模型，如 seedance-2.0 / kling / minimax-h3")
    ap.add_argument("--genre", required=True, help="题材赛道，如 复仇爽剧 / 甜宠 / 悬疑规则")
    ap.add_argument("--aspect-ratio", default="16:9", help="画幅，默认 16:9 横屏")
    ap.add_argument("--novel", default=None, help="原著文件路径或名称；有则走改编流程")
    ap.add_argument("--style", default=None, help="画风一句话（会写进画风统一句）")
    ap.add_argument("--prompt-language", default="en", help="关键帧正文语言，默认 en")
    ap.add_argument("--language", default="zh-CN", help="创作者可读文档语言")
    args = ap.parse_args()

    root = Path(args.dir).expanduser()
    if (root / "short-drama.json").exists():
        print(f"❌ 目录已是项目：{root}", file=sys.stderr)
        return 2

    cmd = [sys.executable, str(find_project_tool()), "init", str(root),
           "--title", args.title, "--aspect-ratio", args.aspect_ratio,
           "--target-seconds", str(args.seconds),
           "--language", args.language, "--prompt-language", args.prompt_language]
    if args.episodes:
        cmd += ["--episode-count", str(args.episodes)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout + r.stderr, file=sys.stderr)
        return r.returncode

    fmt = json.loads((root / "short-drama.json").read_text(encoding="utf-8"))["format"]
    branch = STEP_BY_INPUT["novel" if args.novel else "idea"]
    dev = root / "项目开发"
    dev.mkdir(parents=True, exist_ok=True)

    checklist = f"""# 开工清单 · {args.title}

> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 已确认的四项

| 项 | 值 |
|---|---|
| 项目名 | {args.title} |
| 画幅 | {fmt['aspect_ratio']} |
| 单集目标时长 | {args.seconds:g} 秒 |
| 集数 | {args.episodes or '未定'} |
| 目标视频模型 | {args.model} |
| 题材赛道 | {args.genre} |
| 画风 | {args.style or '未定'} |
| 关键帧正文语言 | {fmt['prompt_language']} |

## 原著来源

{args.novel or '无（从点子/梗概开发）'}

## 下一步

1. `{branch[0]}` —— {branch[1]}
2. 改编时保留原著核心人物的立场、核心关系与主线；原著没有的新增内容一律登记为 `add` 并列进简报
3. 题材赛道热度不足或未核对时，跑 `short-drama-novel-analyze/scripts/heat_probe.py`，无来源就写「未提供热度数据」
4. 分镜前先出定调图与身份板；没有图不要写满「待补参考图」

## 硬约束

- 画幅 `{fmt['aspect_ratio']}` 已写死，全项目关键帧/图片/视频提示词的画幅句必须一致；中途改画幅 = 已生成的图全部重画
- 单集 {args.seconds:g} 秒是镜长核对基准，节奏档案未接受前不核对数值
- 目标模型决定视频提示词方言与参考图张数上限，写视频提示词前先读该模型方言文件
"""
    (dev / "开工清单.md").write_text(checklist, encoding="utf-8")

    print(json.dumps({
        "project_root": str(root),
        "title": args.title,
        "aspect_ratio": fmt["aspect_ratio"],
        "target_seconds": args.seconds,
        "episodes": args.episodes,
        "model": args.model,
        "genre": args.genre,
        "next_skill": branch[0],
        "checklist": str(dev / "开工清单.md"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
