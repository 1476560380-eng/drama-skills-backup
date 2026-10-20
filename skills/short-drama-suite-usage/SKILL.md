---
name: short-drama-suite-usage
description: Use when 提到短剧创作、《末世选择》项目、短剧说明书. 路由全套 short-drama 技能并维护项目状态。
---

# 部署状态
- 11 个技能已全部部署在 duanju profile：short-drama(总调度) / novel-analyze / develop / write / assets / image-prompts / **storyboard(升级版)** / video-prompts / produce / edit / review
- storyboard 是用户定制升级版（多「增强镜头规格」：三拍式运镜笔触、TTS配音指令、SEG段落、0.5s镜长，默认启用，「精简模式」可关）；来源备份仓库 1476560380-eng/drama-skills-backup（skills/=升级版，vendor/drama-skills-official-2026-10/=官方快照）
- 升级版未合并官方两条新改进：多镜「场景站位」规范、Seedance 2.0 参考 9 张上限裁剪——用户要合并时从 vendor 版 diff 补

# 题材热度取数
用户问「现在什么题材火 / 查热度 / 哪个赛道热」时，跑 `~/.hermes/profiles/duanju/skills/short-drama-novel-analyze/scripts/heat_probe.py --quiet`（无第三方依赖）。
- 可用免费源（实测）：百度热搜、头条热榜、B站热搜、豆瓣在播剧、番茄小说榜（书名+简介，小说侧最准）
- 抓不到需创作者供：红果短剧、抖音短剧榜、云合、DataEye、艺恩、猫眼（登录/付费/App）
- 不可用：微博热搜 403、知乎需认证、抖音需签名、七猫 404、猫眼 403
- 铁律：热度必须带来源+ fetched_at；无来源写「未提供热度数据」，绝不编造榜单/播放量。详见 novel-analyze/references/heat-sources.md

# 项目状态（2026-10-20）
- 项目《末世选择》在 ~/duanju/末世选择/，short-drama.json + 项目开发/ 三件套齐
- EP001 五文档：剧本✅ 视觉设定✅ 图片提示词✅ 分镜✅ 视频提示词❌（下一步）
- produce 需要项目外 adapter+供应商 API key（未配置）；跑生产前先问用户用哪家

# 使用方式
用户说人话即可路由：拆原著→novel-analyze；点子变项目→develop；写/改剧本→write；拆角色场景道具→assets；图片提示词→image-prompts；拆分镜/关键帧→storyboard；视频提示词→video-prompts；跑图/视频/配音→produce(必须用户明确确认，花钱)；剪辑→edit；审稿→review(只报不改)；跨阶段/进度→short-drama。
五份文档是唯一真相（剧集/<EP>/ 下的文件，不是对话草稿）。
说明书落在 ~/duanju/短剧创作系统使用说明书.md，说「短剧说明书」即读。
技能再升级时：用户说「把升级同步到备份仓库」→ cd ~/drama-skills-backup && cp 新文件 && git commit && git push（走代理 127.0.0.1:7897）。