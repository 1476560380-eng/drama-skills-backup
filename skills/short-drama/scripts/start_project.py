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

# 文件规则模板：预填创作者历次明确交代的写法要求（源头=锤爆世界/末世选择历次会话），
# 新项目开工即生成，不再是空文件。项目特有规则（如特定画风）开工后再往里补。
RULES_TEMPLATE = """# 文件规则 · {title}

> 本文件是**每个创作文件必须遵守的规则的唯一载体**。项目卡会把它整段抄进去（脚本生成，卡里手改无效），改规则只改这里。
> 规则来源：创作者历次明确交代的写法要求，不是技能默认值；与技能冲突时以本文件为准，并把冲突列进项目卡的「待裁决」。

---

## 通用（全项目）

- 画幅 **{aspect} 横屏**，写死。关键帧、图片提示词、视频提示词的画幅句必须逐字一致（`Horizontal {aspect}`）。中途改画幅 = 已生成的图全部重画。
- 创作者可读文档用中文；提示词正文语言按各文件口径（见下）。
- 时间**按剧情拍子排，不按集长配额砍戏**。戏需要多长就多长，装不下就改口径或拆集，不许为凑秒数删拍。
- 每写完一份文件立刻跑局部校验（`episode_lint.py <集目录> --only <文件名>`），不攒到最后。
- 术语（IMG/REF/关键帧/任务单/SEG/生成包）每次出现要用大白话 + 表格解释，不假设创作者懂行话。
- 交付时主动给文件卡片，不等创作者问。

---

## 剧本.md

- 一级标题 `# EPxxx 集名`；场景标题 `## EPxxx-SCxxx 内/外 · 地点 · 时间/天气`。
- 对白一律 `角色（可执行提示）：台词`。**冒号前必须带括号提示**——写成裸的「角色名：台词」会被索引判成 `ambiguous_dialogue_or_action`，整份索引进 review_required。
- 生产标签只用 `[VO]` `[OS]` `[SFX]` `[画面文字]` `[连续性]` `[转场]`。
- 每场首行写一条 HTML 注释，标出本场拍点数量与该场实际需要的秒数。
- 动作写现在时、可见可拍；不用解释替代行动，不把演过的机制再复述一遍。

## 视觉设定.md

- 条目必须是二级标题 `## 类别 · 名称`，类别只能是 人物 / 造型 / 地点 / 道具。**禁止** `## 人物` 分区 + `### 名字`（跨文档检查器只认前者，写成后者会让分镜所有视觉依据集体失效）。
- 每个人物与造型条目必须有一行 `- 画面代称：X`（不加粗），英文拼写全集唯一、大小写统一；正文从不点名就写 `画面代称：无`。
- 先写「识别锚点」（什么不变使它还是同一个资产），再写「本集状态」（起始 → 变化 → 结束）。
- 连续性锁只锁**跨镜不变的可见事实**，锁面用提示词语言写成最小名词短语，下游原样抄进关键帧正文。
- 世界观层面的可见规则（如本剧的黑墨状血）写成独立道具条目，不当成描写细节随手带过。

## 图片提示词.md（设定图）

- **两种口径二选一，不许混写**：
  - `prompt_language: zh-CN` → 走中文商业设定卡规则（下面全套）；
  - `prompt_language: en` → 走英文身份板。
  本项目当前是 `{prompt_lang}`{lang_note}
- 四个子模板按资产类型选，不硬套：**T-CHA** 人物/怪物卡（左主立绘+留白档案卡／中四视图／右表情或特征拆分+色板／底动态+线稿）、**T-PRP** 道具卡（微距特写+比例尺）、**T-UI** 界面板（单帧正视+状态对照）、**T-LOC** 场景四分格（同一母场景四视角，地理 100% 一致）。
- 每条正文的结构骨架：①【全局规格与画幅】+ 绝对防合图规则（画面只允许这一个独立资产）②【本体锁定】1:1 逐条识别锚点 ③【版式排布】分区描述 ④【负向提示词】。
- **档案卡一律留白**，不渲染文字；档案信息（姓名/归属/用途）写在提示词外的「图外标注」行，防模型生成乱码。
- **色板必给 HEX**，每个资产 4-6 色。
- 双语渲染增强尾：卡片/UI 类末尾加 `。PBR材质，physically accurate lighting，8k，ultra-detailed，octane render`；场景类去掉 `octane render`（避免双渲染器关键词打架）。
- 负向词末尾统一追加 `，distorted，blurry，text error，garbled text`。
- 状态变体卡必须写【基准锁定】+【本状态差异（逐条对照）】，负向词含「基准脸变化」。
- UI 板是**唯一允许 readable 文字**的特例，逐字列出界面文字。
- **氛围词无效、不要堆**（雾/留白/负空间单独加反而变差，实测过）；**镜头语言有效**（焦段/景深/焦点分配），要写就写到焦段这一级。
- `IMG-...` 编号与《标题》**逐字保留**，重写后要核对分镜里每个 `IMG-...《...》` 引用都还能找到同名标题。
- `EPxxx图片提示词.md` 与 `图片提示词.md` 是镜像，改一个必须同步另一个。

## 分镜.md

- 头部必写 `- 强制项：轴线锁、亮度口径`（默认全强制，fail-closed）。要豁免必须创作者亲口说，写 `- 规格：legacy`。
- 每个 `SEG-` 段头必写：情绪基调／色调／场景设计 + **轴线账**（`轴线：甲 ↔ 乙｜机位：…｜甲 画面左 / 乙 画面右`）+ 镜头基准（本段默认焦段/景深）+ 光线锚点（night/dawn/lamplit…）+ 曝光基准。写不出轴线账的场次不得拆分镜。
- **镜头语言逐镜选、逐镜写理由**，严禁按景别套模板（「镜头是根据剧情和表现力来的，不是套用相同的」）。焦段只用 24/35/50/85 四档，f 值只用三条语义轴（深焦 f/5.6+ ／叙事 f/2.8 ／浅焦 f/2.0-）。同段可重复同一焦段——重复本身是设计，但要能说出为什么。
- **静帧化**：动作进行时一律改成「动作后定格」；必须保留进行时时，句尾加具体结果禁句（`no motion blur on face`、`tears stay in her eyes, never fall`），不写「静止」「不模糊」这类抽象禁令。
- **亮度四层**：①调色词拆「色相 + 明度」，禁止单用 `moody`/`muted`/`dark` 代表亮度 ②每镜写 `key:` 与 `fill:` 两个光源，夜景/逆光必须有补光，人脸对背景 ≤1:4 ③负面词 `underexposed, crushed blacks, murky shadows` ④曝光句 `Exposure balanced for …`。
- **画风句拆两截**：质感锁 `photorealistic cinematic still, soft film grain` 全片统一；调色词按 SEG 段头逐段翻译，同段一致、段间按翻转设计切换。段内确有变化时在那一镜正文写「刻意破格」，并保留段头调色词。
- 每镜必写字段：职责、来源（剧本真实场景 ID 开头）、时长（0.5s 精度）、景别/机位、**运镜（带理由）**、镜头技术捕捉（起幅→意图→落幅交接）、起点 → 唯一动作 → 终点、声音、配音指令（角色｜音色｜状态｜语速）、视觉依据、图片提示词项、输入参考图、**ShotDeck 参考**（逐词中英对照 `英文·中文 + 英文·中文`，6-8 组）、时间码。
- 有人物出场的镜必须写画面位置句（`on screen-left` / `on screen-right` / `facing screen-…`）；走位穿场镜加 `not part of the dialogue axis`；全景重设轴线写 `axis resets`。禁写变体（`on the left side`、`at frame left`、中文「画面左侧三分之一」）不被接受。
- 对白只写一遍：`声音` 字段只写索引（`[OS] 画外对白×2（约3s，内容见配音指令）`），逐字全文只出现在 `配音指令`。
- 生成包分组：目标模型已声明且有单镜最短时长下限时才做，沿 SEG 边界切包、每包落在模型原生窗口内，头部写「生成包总表」、每镜字段区首行写 `生成包`。
- 镜长三方对账：头部合计 = 逐镜相加 = 各 SEG 段头之和。时间码必须连续无断点。

## 视频提示词.md（模型定了再建）

- 必须按目标视频模型的方言写（MiniMax H3 / Seedance / Wan 各有方言文件）；模型未定不写，不用通用模板硬凑。
- 生成包正文顶部声明 `N hard-cut shots, total Ns`，每个切点配数字时长 + 语义锚。
- 运镜用具体行为词，不用机位不明的词：缓推 = `slow dolly in`，**禁用 `zoom`**；横移 = `tracking`；摇 = `pan`。
- @资产绑定任务单的原料来自分镜的「运镜」「起点→唯一动作→终点」「配音指令」三行，不重新翻译。

---

## 项目卡.md

- 由 `short-drama/scripts/project_card.py` 生成，**手改无效**（下次生成会覆盖）。规则正文的源头就是本文件。
- 卡是索引不是真相：口径以 `short-drama.json`、`项目开发/开工清单.md` 与各集文档为准。
- 源文件互相矛盾时列进「待裁决」，不许自行挑一个往下做。
"""


def write_rules_template(root: Path, title: str, aspect: str, prompt_lang: str) -> Path:
    """开工时生成预填历次规则的文件规则.md（幂等：已存在不覆盖）。"""
    rules_p = root / "项目开发" / "文件规则.md"
    if rules_p.exists():
        return rules_p
    if prompt_lang and prompt_lang.lower() in ("zh-cn", "zh"):
        lang_note = "，走中文商业设定卡（下面全套规则生效）。"
    else:
        lang_note = "，走英文身份板，卡式规则暂不生效；若要切中文卡需创作者裁决后改 `prompt_language`。"
    text = RULES_TEMPLATE.format(title=title, aspect=aspect,
                                 prompt_lang=prompt_lang or "（未填）", lang_note=lang_note)
    rules_p.parent.mkdir(parents=True, exist_ok=True)
    rules_p.write_text(text, encoding="utf-8")
    return rules_p


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
    rules_p = write_rules_template(root, args.title, fmt["aspect_ratio"], fmt.get("prompt_language", ""))

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
        "rules_file": str(rules_p),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
