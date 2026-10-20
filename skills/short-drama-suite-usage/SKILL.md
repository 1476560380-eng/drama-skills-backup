---
name: short-drama-suite-usage
description: Use when 提到短剧创作、《末世选择》项目、短剧说明书. 路由全套 short-drama 技能并维护项目状态。
---

# 部署状态
- 11 个技能已全部部署在 duanju profile：short-drama(总调度) / novel-analyze / develop / write / assets / image-prompts / **storyboard(升级版)** / video-prompts / produce / edit / review
- storyboard 是用户定制升级版（多「增强镜头规格」：三拍式运镜笔触、TTS配音指令、SEG段落、0.5s镜长，默认启用，「精简模式」可关）；来源备份仓库 1476560380-eng/drama-skills-backup（skills/=升级版，vendor/drama-skills-official-2026-10/=官方快照）
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
用户开新项目时会主动交代，但没说的必须问：
1. **画幅**：用户一律 **16:9 横屏**（已确认，写入 `format.aspect_ratio`）；不要再默认竖屏
2. **单集时长 + 集数**：没定就不排版镜长（写了也要返工）
3. **目标视频模型**（Seedance / 可灵 / MiniMax / 即梦…）：决定视频提示词方言与参考图张数上限
4. **画风与题材**：画风统一句全项目逐字一致；题材决定 genre-card
另：prompt_language（关键帧正文语言，默认 en）、交付面/叠加区。

# 项目状态
- **《末世选择》只是示例/样品，不是真实项目**（`~/duanju/末世选择/`）。可用作格式样板（已转为 16:9 横屏、已过局部校验），但不要当成用户的正式作品推进，也不要建议它下一步做什么
- 用户真实项目开工时，按上面四项先确认再建目录
- produce 需要项目外 adapter+供应商 API key（未配置）；跑生产前先问用户用哪家

# 使用方式
用户说人话即可路由：拆原著→novel-analyze；点子变项目→develop；写/改剧本→write；拆角色场景道具→assets；图片提示词→image-prompts；拆分镜/关键帧→storyboard；视频提示词→video-prompts；跑图/视频/配音→produce(必须用户明确确认，花钱)；剪辑→edit；审稿→review(只报不改)；跨阶段/进度→short-drama。
五份文档是唯一真相（剧集/<EP>/ 下的文件，不是对话草稿）。
说明书落在 ~/duanju/短剧创作系统使用说明书.md，说「短剧说明书」即读。
技能再升级时：用户说「把升级同步到备份仓库」→ cd ~/drama-skills-backup && cp 新文件 && git commit && git push（走代理 127.0.0.1:7897）。