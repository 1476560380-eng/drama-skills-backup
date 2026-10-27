Obsidian vault 路径：/Users/zhishu/zhishiku/。文件夹结构：复盘（日/周/月）、项目、待办、日程、收件箱。
§
hermes技能管理：用户自建skill(非curator-managed)无法被agent自动更新。要启用自动维护需运行 hermes curator adopt <skill名>。
§
GitHub 推送被墙时走系统代理 127.0.0.1:7897（Clash类，系统代理已启用）。git 默认不走代理，需加 -c http.proxy=http://127.0.0.1:7897。
§
备份触发词规则：说"短剧/项目备份"→只推 drama-skills-backup 仓库（本地 ~/drama-skills-backup）；说"Hermes/配置备份"→只推 hermes-backup（~/.hermes）；模糊说法"备份到 git"→全部跑。切勿混库。
§
本机 Hermes 双 Profile：default=~/.hermes/（主，gateway running，技能/记忆更全，含天枢/Tushare/飞书，是 11 的超集）；11=~/.hermes/profiles/11/（当前会话所在，是 default 子集）。对比方法见 skill hermes-profile-management。
§
飞书 API 接入方法（已跑通）：凭证 FEISHU_APP_ID/SECRET 存于 default profile 的环境文件（cli_aaf99d6da3b89d01），duanju 会话可直接读取。应用已开 docx+drive 权限。流程：tenant_access_token → /docx/v1/documents 建文档 → /docx/v1/documents/{id}/blocks/{id}/children 分批写块（每批≤40）→ 清空用同路径 children/batch_delete + start_index/end_index。API 建的文档在应用云空间，必须给用户 open_id 加 full_access 才可见；用户 open_id 可用手机号走 contact/v3/users/batch_get_id 查到。
§
短剧创作系统（常驻上下文）：12 个 short-drama 技能已全部部署在 duanju profile（storyboard 为用户定制升级版）。备份仓库 drama-skills-backup（本地 ~/drama-skills-backup，四区：skills=升级版、vendor=官方快照、projects=项目文本、docs=说明书）；短剧相关内容一律进该库。推送走代理 127.0.0.1:7897。
§
文档偏好：给用户的说明书/手册要写成「别人也能看懂能上手」的完整操作文档——按步骤走、每步给出对 AI 说的原话示例、含状态表和接手必读约定，而不只是给自己的速记。
§
版本号铁律（用户明确要求）：每一次改进或完善都必须给版本号。规则：MAJOR=契约/格式破坏性变更，MINOR=新增能力，PATCH=修bug/文字。每次改完同步：①VERSION ②CHANGELOG.md ③说明书版本号+PDF ④git tag push。CHANGELOG 每条按三段式记：改了哪些/优化了哪些/兼容性验证。
§
updream 接入（B站系 AI 视频创作平台 www.updream.cn）：无开放 API，对接方式=技能移植（Skill 社区）+ 项目文件平移到画布。updream 技能（updream-skill-ops/publishing）和一切 updream 相关文件**不备份**（用户 2026-10-23 明确要求）。登录需用户本人在弹窗里手动完成，聊天里发来的账号密码一律不使用、不外存。
§
本地浏览器弹窗工作流（2026-10-20 跑通）：让用户亲眼看到并亲手输密码的浏览器窗口，需 ①系统默认浏览器必须是 Chrome（原为夸克，已改 LSHandlers plist 的 http/https→com.google.chrome 并 killall -HUP lsd）②hermes config set browser.use_real_profile true --profile duanju ③browser.headed true ④先 pkill 残留的 headless chrome（匹配 user-data-dir=...browser-profile）和 agent-browser 守护进程，否则旧 headless 进程被复用永远不弹窗、且 agent-browser 缓存旧 CDP 端口报 connection refused。弹窗后用户手输登录，登录态留在会话里供后续自动化。用户习惯直接在聊天里发密码/验证码——必须拒绝使用聊天里的凭据，改走此弹窗通道。
§
短剧工作流纪律（用户反复强调）：①讨论方案时"先不要部署/先讨论不要改东西"是硬约束，他点头才动文件；②让他看效果=给A/B/C对照案例让他复制去自己的工具出图，不是替他改文件；③偏离具体例子回到技能层讨论时他会纠偏（"我们讨论的是完善技能的问题不是具体例子的问题"）；④改进技能前先机器审计现有产出取证（如58帧统计镜头词0次），用数据说话。
§
改动外部仓库/技能/项目文件前先给方案+代价，等用户逐项确认；他反复强调「不要私自部署」「先让我确认好」。只读分析不限。
§
短剧系统补录：①对标研究——MarkQWu 复刻线不采但三层控制模型可借鉴；nianjiang888/storywright 的 ShotLock 15 条规则实测有料。②ShotDeck（收费）已入工作流：每镜「ShotDeck 参考」行=逐词中英对照，放生成包行下一行。③多镜容器生成器已固化：/Users/zhishu/duanju/锤爆世界/项目开发/gen_containers.py（v2.23.0 起，改容器只改生成器重跑、不手改产物）。
§
多镜容器 v2 七项规则（v2.23.0 写死在 gen_containers.py）：①风格块=首镜质感锁原文(含 Horizontal 16:9)+三项禁止，段头色调只作块外「本段色彩意图」行，禁止叠进可复制块(mid/low-key打架) ②每镜【镜头参数】=源分镜 Shot on 句(含黑血 never red) ③时间锚=本镜Xs(本包Ys中的a–bs)+包级硬切声明 ④位置承接按人名归属中文句，空镜写无人物 ⑤容器禁元话语(理由/本镜职责/破格/动作链见)，留分镜给剪辑 ⑥本镜画内人物=视觉依据∪英文首帧点名(映射读视觉设定「画面代称」，漏登记自动兜底标⚠️) ⑦中英人名双轨保留。
