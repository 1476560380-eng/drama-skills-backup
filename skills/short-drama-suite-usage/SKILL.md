---
name: short-drama-suite-usage
description: Use when 提到短剧创作、《末世选择》项目、短剧说明书. 路由全套 short-drama 技能并维护项目状态。
version: 2.9.0
---

# 部署状态
- 11 个技能已全部部署在 duanju profile：short-drama(总调度) / novel-analyze / develop / write / assets / image-prompts / **storyboard(升级版)** / video-prompts / produce / edit / review
- storyboard 是用户定制升级版（多「增强镜头规格」：三拍式运镜笔触、TTS配音指令、SEG段落、0.5s镜长、镜头时间码、节尾承接块、**生成包分组**，默认启用，「精简模式」可关）；来源备份仓库 1476560380-eng/drama-skills-backup（skills/=升级版，vendor/drama-skills-official-2026-10/=官方快照）
- v2.7.0 新增（2026-10-23，源自对标外部优秀分镜样本）：①镜头时间码（标题带全集时间轴）②节尾承接块（轴线锁定/未完成动作/下集待接）③生成包分组（SEG 边界切包+模型原生窗口约束+包间续接链，改片半径从赌单镜降到重一包）④video-prompts 按包输出任务单（出场人物声线锁定+首帧@绑定+位置承接+负面指令前置）
- v2.8.0 新增（2026-10-24，情绪工程层）：①先画曲线再分镜（references/rhythm-emotion-design.md）②四题材曲线形状库（爽文/悬疑/温情/群像，示例不是规定）③段间反差设计 ④声音当节奏工具（静音蓄力/J-cut/L-cut/声音减法）⑤三种蒙太奇压缩配方 ⑥防串味自检；SEG 可选「节奏定位」字段；lighting-craft 补段间色彩翻转+情绪-光色映射；keyframe-craft 补微表情六通道词表
- v2.9.0 新增（2026-10-24，镜头语言+段级调色，含一处契约修订）：①SEG 段「镜头基准」焦段/景深三层选法（段基准→逐镜破格→景别兜底表）②SEG 段「光线锚点」③关键帧画风句拆「全局质感锁 + 按段翻译的调色词」（10 组中文色调→英文 grade 对照）④微表情「动作后定格」写法+三条判例 ⑤帧尾可选情绪钩子；video-prompts 2.7.1 补「多镜容器正文声明总镜数」（未实测）
- 升级版未合并官方两条新改进：多镜「场景站位」规范、Seedance 2.0 参考 9 张上限裁剪——用户要合并时从 vendor 版 diff 补

# 契约避坑（实测踩过的，会全量报错）
- 视觉设定条目必须 `## 人物 · 林羽`，不能 `## 人物` + `### 林羽`（否则分镜视觉依据全失效）
- `画面代称：Lin Yu` 不能加粗，加粗后检查器认不出
- 分镜 IMG 项用 `IMG-XXX《标题原名》》，书名号且名称逐字等于《图片提示词.md》标题
- 冻结/收尾关键帧正文必须是 `> ` 引用块，裸段落不算
- 镜头标题必须 `## SHOT-EP001-001 · 中文名`
- 画外声明只能写 `；画外：人物「名字」`，不能带括号说明
- 「待补参考图」会硬性阻断视频提示词：需 REF（真图）/PLAN（出图计划）/明确文生视频 三选一

# 质量闸门（每份文档写完就跑）
```bash
python3 ~/.hermes/profiles/duanju/skills/short-drama/scripts/episode_lint.py 剧集/EP001
```
缺文档也能跑（缺的跳过不算错）；退出码 1 = 有问题。五份齐备后再跑官方 creator_markdown_check.py。
模板：`short-drama/templates/视觉设定模板.md`、`分镜模板.md`——从模板起写，不要从空白页起。
工序顺序：定模型+集长 → 出图 → 分镜 → 视频提示词 → 完整核对 → 审查。

# 题材热度取数
用户问「现在什么题材火 / 查热度 / 哪个赛道热」时，跑 `~/.hermes/profiles/duanju/skills/short-drama-novel-analyze/scripts/heat_probe.py --quiet`（无第三方依赖）。
- 可用免费源（实测）：百度热搜、头条热榜、B站热搜、豆瓣在播剧、番茄小说榜（书名+简介，小说侧最准）
- 抓不到需创作者供：红果短剧、抖音短剧榜、云合、DataEye、艺恩、猫眼（登录/付费/App）
- 不可用：微博热搜 403、知乎需认证、抖音需签名、七猫 404、猫眼 403
- 铁律：热度必须带来源+ fetched_at；无来源写「未提供热度数据」，绝不编造榜单/播放量。详见 novel-analyze/references/heat-sources.md

# 开工前必须问清的四项（缺一项不动手）
用户一说「我要做新项目」就**主动**问，不要等用户想起来交代。按这个顺序问，一次问完：
1. 「新项目叫什么？」（项目名/剧名）
2. 「每集多少秒？共几集？」
3. 「用什么视频模型？」（Seedance / 可灵 / MiniMax / 即梦…）
4. 「什么题材？」（复仇爽剧 / 甜宠 / 悬疑规则 / 逆袭…）
默认已定不用问：画幅 **16:9 横屏**、关键帧正文英文。用户主动说了别的则从用户。

拿到四项后直接跑一键开工（缺参数会拒绕，不要手拼 project_tool）：
```bash
python3 ~/.hermes/profiles/duanju/skills/short-drama/scripts/start_project.py \
  --dir ~/duanju/<剧目> --title "<剧目>" --seconds 90 --episodes 10 \
  --model seedance-2.0 --genre "复仇爽剧" [--novel <原著路径>] [--style "2D 国漫，冷灰调"]
```
它建目录 + 写 `项目开发/开工清单.md`（四项落档）+ 打印下一步技能。

# 小说改编优先（用户的默认路径）
用户的项目几乎都从**小说改编**开始。一开工就要往改编方向靠：
1. 先问原著（文件/书名/链接），进 `$short-drama-novel-analyze`：章节索引 → 改编价值快评 → 分集候选
2. 快评必须带「题材赛道对照」，取数跑 `heat_probe.py`；无来源写「未提供热度数据」，绝不编造
3. 是否值得改 → 判改编密度（screen_ready / prose_only）与制作负担，不只看热度
4. 进 `$short-drama-develop` 立**改编契约**：保留原著核心人物立场/核心关系/主线；新增内容一律登记 `add` 并列入简报
5. 写剧本时保留原著的事实与台词能用的部分，不把原著改成另一个故事

# 项目状态
- **《末世选择》只是示例/样品，不是真实项目**（`~/duanju/末世选择/`）。可用作格式样板（已转为 16:9 横屏、已过局部校验），但不要当成用户的正式作品推进，也不要建议它下一步做什么
- 用户真实项目开工时，按上面四项先确认再建目录
- produce 需要项目外 adapter+供应商 API key（未配置）；跑生产前先问用户用哪家

# 使用方式
用户说人话即可路由：拆原著→novel-analyze；点子变项目→develop；写/改剧本→write；拆角色场景道具→assets；图片提示词→image-prompts；拆分镜/关键帧→storyboard；视频提示词→video-prompts；跑图/视频/配音→produce(必须用户明确确认，花钱)；剪辑→edit；审稿→review(只报不改)；跨阶段/进度→short-drama。
五份文档是唯一真相（剧集/<EP>/ 下的文件，不是对话草稿）。
说明书落在 ~/duanju/短剧创作系统使用说明书.md，说「短剧说明书」即读。
技能再升级时：用户说「把升级同步到备份仓库」→ cd ~/drama-skills-backup && cp 新文件 && git commit && git push（走代理 127.0.0.1:7897）。