# drama-skills-backup

[ZenStory AI Drama Skills](https://github.com/zenstory-ai/drama-skills) 的个人定制版本备份仓库。
这里存放的是**经过本地升级的 skill 文件**，与官方原版的差异都在本仓库里留档。

- 上游官方仓库：https://github.com/zenstory-ai/drama-skills
- 我的 GitHub 账号：`1476560380-eng`
- 本仓库：私有，仅自用备份

---

## 这个仓库里有什么

```text
drama-skills-backup/
├── skills/                          ← 我的升级版（实际使用的文件）
│   ├── short-drama-storyboard/SKILL.md
│   ├── short-drama-novel-analyze/   ← 题材赛道对照 + heat_probe.py + heat-sources.md
│   └── short-drama-suite-usage/SKILL.md   ← 本地导航技能（非官方）
├── projects/                        ← 短剧项目创作内容
│   └── 末世选择/                    ← short-drama.json + 剧集/EP001 五文档 + 项目开发/
├── docs/                            ← 使用说明书
│   └── 短剧创作系统使用说明书.md
└── vendor/                          ← 官方原版全量快照（纯官方，未修改）
    └── drama-skills-official-2026-10/   ← 快照日期版本，共 11 个 skill
        ├── short-drama/SKILL.md
        ├── short-drama-storyboard/SKILL.md   ← 注意：vendor 里是官方原版
        └── ...（共 11 个 skill，231 个文件）
```

`skills/` 只备份**被修改过的文件**；官方原版未改动的 skill（short-drama、short-drama-write、
short-drama-assets 等）不重复备份，可随时用官方命令重新安装，或从 `vendor/` 取原版。

---

## 本地升级说明（与官方原版的差异）

升级位置：`skills/short-drama-storyboard/SKILL.md` 中新增的
**「增强镜头规格（本项目默认启用）」**章节。

升级来源：对比分析《天文台异象》分镜提示词（一份手写的高水准分镜文档）后，
把它的优点吸收进 skill 的标准格式。四项增强：

| 增强项 | 内容 | 作用 |
|---|---|---|
| **镜头技术捕捉** | 每镜三拍式摄影师笔触：起幅（从什么状态/前景/焦点起）→ 运镜意图（为什么这样动或不动）→ 落幅交接（停在哪一格、下一镜从哪里接） | 分镜不只是信息表，还能直接指导生成/拍摄 |
| **配音指令** | 凡镜头有对白/VO/OS，逐句标注 `角色｜音色｜状态｜语速` | 攒起来就是 TTS 配音任务清单，可直接喂给语音合成 |
| **SEG 段落** | 每 3–5 镜归入一个段落头，写总时长、情绪基调与色调（如「压抑对峙 + 冷灰调」）+ 一句场景设计 | 控制整段戏的情绪与光色统一，防止逐镜生成时画风漂移 |
| **镜长精度 0.5s** | 镜长从整秒细化到 `X.Ys`；对白镜先按发声时间估再排停顿 | 更精确的节奏控制 |

以上增强**默认启用**；在对话里明确要求精简时可整组关闭（SKILL.md 中有写）。

保留的官方结构能力（未改动）：连续性锁、视觉依据逐镜回链、IMG/REF 双轴引用、
冻结/收尾关键帧、剧本场景来源 ID 回链、机械检查器对接。

---

## 怎么使用（在新电脑 / 新会话恢复）

1. 安装官方全套 skill（会装到当前目录的 `.agents/skills/`）：

   ```bash
   npx skills add zenstory-ai/drama-skills -y
   ```

2. 用本仓库的升级版覆盖对应文件：

   ```bash
   # 在项目目录下执行，.agents/skills/ 换成实际安装路径
   curl -o .agents/skills/short-drama-storyboard/SKILL.md \
     https://raw.githubusercontent.com/1476560380-eng/drama-skills-backup/main/skills/short-drama-storyboard/SKILL.md
   ```

   （私有仓库需要登录态；也可以直接 `git clone` 本仓库后复制文件。）

3. 覆盖后 Agent 重新加载 skill 即生效——之后每集分镜自动按增强规格输出。

---

## 怎么更新备份

以后 skill 再升级，在本地项目目录对话里说一句「把升级同步到备份仓库」即可，流程固定为：

```bash
cd ~/drama-skills-backup
cp ~/duanju/.agents/skills/<技能名>/SKILL.md skills/<技能名>/SKILL.md
git add -A
git commit -m "backup: <改了什么>"
git push
```

约定：
- 只备份**被修改过**的文件，并在本 README 的「升级记录」里记一笔
- 每次改了哪个 skill、改了什么，提交信息写清楚

---

## 升级记录

| 日期 | 文件 | 内容 |
|---|---|---|
| 2026-10-20 | `skills/short-drama-storyboard/SKILL.md` | 新增「增强镜头规格」：镜头技术捕捉 / 配音指令 / SEG 段落 / 0.5s 镜长（初版提交 `50df594`） |
| 2026-10-20 | `skills/short-drama-novel-analyze/SKILL.md` | S1 改编价值快评新增「题材赛道对照」一行：报告原著所属短剧赛道与是否在热门序列；热度只认可核对来源，无来源写「未提供热度数据」，不得编造榜单；该行只作选题参照，不参与改编密度判据 |
| 2026-10-20 | `skills/short-drama-novel-analyze/scripts/heat_probe.py` + `references/heat-sources.md` | 题材热度探针：聚合百度热搜/头条热榜/B站热搜/豆瓣在播剧/番茄小说榜五个免费源，按 16 条短剧赛道统计命中数；文档记录云合/DataEye/红果等需登录源、微博/抖音/猫眼不可用源与引用规范 |
| 2026-10-20 | `skills/short-drama-suite-usage/SKILL.md` | 新增本地导航技能备份：11 技能路由表、项目状态、热度探针用法（本技能为本地自建，非官方） |
| 2026-10-20 | `skills/short-drama/SKILL.md` + `scripts/episode_lint.py` + `templates/` | 阶段闸门：局部校验器（缺文档也能跑）+ 视觉设定/分镜模板骨架 + 固定工序顺序，解决「五份齐了才敢检查」和格式漂移 |
| 2026-10-20 | `skills/short-drama-storyboard/SKILL.md` | 加「交付前必跑」：分镜写完立即跑 `episode_lint.py --only 分镜` |
| 2026-10-20 | `projects/末世选择/剧集/EP001/` | 视觉设定转契约格式（14 个 `## 类别 · 名称` 条目、画面代称去粗）；分镜补 24 个中文名+运镜字段、IMG 书名号与原名对齐、冻结关键帧转引用块、修 92s→100s 与 SEG-03 20.0→18.0、补 3 处画外声明 |
| 2026-10-20 | 画幅支持（`short-drama/SKILL.md`、`short-drama-storyboard/SKILL.md` + `references/shot-craft.md`、`short-drama-develop/references/genre-cards/*`、`templates/分镜模板.md`） | 把 16:9 横屏改成一等公民：画幅必须问不要默认竖屏；景别谱系按画幅分支（横屏全谱系可用、竖屏中近特为主）；15 张题材卡 `form: 竖屏连续短剧` 改为跟随项目画幅 |
| 2026-10-20 | `projects/末世选择/` | 示例项目转 16:9 横屏：`aspect_ratio`→16:9、分镜 27 处画幅句 + 图片提示词 11 处改 `Horizontal 16:9`、brief/story-engine 表述同步 |
| 2026-10-20 | `vendor/drama-skills-official-2026-10/` | 新增官方原版全量快照（11 个 skill / 231 文件）；其中 storyboard 从官方 GitHub main 拉取纯原版替换 |

---

## 相关但不在本仓库的内容

- 《末世选择》的生成素材（图片/视频/配音等 `制作成果/` 媒体文件）体积大，不并入本仓库；仓库只存文本创作文档
- 官方未改动的其余 10 个 skill 由上游维护，直接随官方更新

## 日常同步

```bash
cd ~/drama-skills-backup
cp ~/.hermes/profiles/duanju/skills/<技能>/SKILL.md skills/<技能>/SKILL.md   # 技能改动
rsync -a --exclude='制作成果' ~/duanju/末世选择/ projects/末世选择/            # 项目文本
git add -A && git commit -m "backup: <改了什么>"
git -c http.proxy=http://127.0.0.1:7897 push                                # 走本地代理
```
