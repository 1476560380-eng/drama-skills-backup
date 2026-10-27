Obsidian vault 路径：/Users/zhishu/zhishiku/。文件夹结构：复盘（日/周/月）、项目、待办、日程、收件箱。
§
用户提票时必须自动执行：①双源交叉验证 ②尾盘五关v5逐条打勾 ③行业对比 ④主力三层视角。核心铁律：任何单一标记（诱多/PE/数据异常等）不能直接排除，必须过完五关全部六关才能下结论。7/21三起误判（赣锋数据解析反、赤峰诱多误杀、航天深V漏扫）根因均为流程执行不完整。
§
推送暗马扫描结果标签：🐴暗马v6（⚡可动手/🔥优质/🔥🔥🔥超级）、📉下马v6、🌱准暗马v6。三个专区用---隔开，标签不混用。准暗马=过了基础过滤但八型检测未触发，加🌱前缀。
§
策略五层：①大盘前置(上证<-1.5%或跌停>50→休息，暴跌次日不休息)②仓位(亨通50%/标准30%/试探10%)③卖出(高开>2%卖半/低开<-2%全走)④风控(止损-3%/永不加仓/连亏2停2/月亏10%停)⑤板块轮动(净买率>60%连2天=风口)。持仓：无量普跌→非出货不催割；放量暴跌→系统性风险走。
§
规则：①PE亏损+换>9%→出货 ②PE>60下马不碰 ③板块暴动勿追最弱跟风 ④追涨3-6%+内外比<1.2→诱多出货 ⑤推荐必须带：大盘风险+止损位+失效条件。
§
行业分析：期货/大宗双源交叉验证（腾讯+新浪），涨跌不一致→打印原始数据确认。尾盘五关v5⑥超跌关：超跌>30%→技术面优先。
§
尾盘五关v5⑥：超跌>30%+缩量止跌+内外比>1.2→技术面优先。判断链：扫描器→五关→案例库→分析师。
§
铁律：①逐票≥3证据②超跌>40%技术优先③推荐带大盘风险+止损+失效④换手<1%跌=假跌⑤14:45重扫⑥改前备份⑦案例库对照⑧内外比连续2天加分+事前验尸(若明天跌最可能因什么)⑨失效条件+48h时效。PE亏损+换>9%出货/PE>60不碰。追涨3-6%+内外比<1.2=诱多出货。
§
用户要求：不再自动做持仓分析。用户已清仓所有票，分析时不要假设任何历史持仓。持仓票只在明确指令时分析。
§
快筛/双管道跑时间：14:20（尾盘成交量定型，留够决策时间）。
§
快筛100%胜率环境（回测验证）：①上证-1.5%~+2%窄幅区间 ②非暴跌首日（暴跌次日反而80%+）③板块集中度<60%（分散）④双确认票≥5只更可靠。7/28(上证-1.16%→次日+0.40%)和7/29(上证+0.40%→次日-0.62%)均100%。极端暴涨日(上证>2%)或暴跌首日(上证<-2%首次)都不可靠。
§
扫描器版本：dark_horse v6.0.3(暴跌分档+金色窗口+集中度预警) + fast_picks v1.6(板块熔断+追涨诱多) + dual_scan v1.1(交叉验证)。均有自动备份(md5检测)+改前手动备份。案例库v1.0(20案例)在~/zhishiku/案例库/独立文件。日志→picks_log.jsonl/fast_picks_log.jsonl/golden_window_log.jsonl。
§
案例库在 /Users/zhishu/zhishiku/案例库/（20个独立.md），新增VI/VII/VIII型，代码版本 v6.0.3/v1.6。回测方法：次日K线100%准确(Sina API)，选股模拟缺PE/内外比/换手→胜率带±5-10%误差，方向性结论可靠。
§
回测方法论：K线次日数据100%准确(Sina API)，但选股模拟缺PE/内外比/换手率，具体胜率带±5-10%误差。方向性结论(暴跌归零/板块集中/双确认最优)可靠。先验证再部署，数据诚实优先。
§
hermes技能管理：用户自建skill(非curator-managed)无法被agent自动更新。要启用自动维护需运行 hermes curator adopt <skill名>。
§
GitHub 推送被墙时走系统代理 127.0.0.1:7897（Clash类，系统代理已启用）。git 默认不走代理，需加 -c http.proxy=http://127.0.0.1:7897 或由 backup_astock.sh 自动处理。A股系统独立备份仓库：1476560380-eng/astock-backup（本地 ~/astock-backup/，脚本 backup_astock.sh 一键同步推送）。
§
备份触发词规则：说"股票/A股/扫描器备份"→只推 astock-backup 仓库（backup_astock.sh）；说"Hermes/配置备份"→只推 hermes-backup 仓库（~/.hermes）；模糊说法"备份到 git"→两个都跑。切勿混库。
§
本机 Hermes 双 Profile：default=~/.hermes/（主，gateway running，技能/记忆更全，含天枢/Tushare/飞书，是 11 的超集）；11=~/.hermes/profiles/11/（A股专用，当前会话所在，是 default 子集）。对比方法见 skill hermes-profile-management。
§
飞书 API 接入方法（已跑通）：凭证 FEISHU_APP_ID/SECRET 存于 default profile 的环境文件（cli_aaf99d6da3b89d01），11 会话可直接读取。应用已开 docx+drive 权限。流程：tenant_access_token → /docx/v1/documents 建文档 → /docx/v1/documents/{id}/blocks/{id}/children 分批写块（每批≤40）→ 清空用同路径 children/batch_delete + start_index/end_index。API 建的文档在应用云空间，必须给用户 open_id 加 full_access 才可见；用户 open_id 可用手机号走 contact/v3/users/batch_get_id 查到。
§
短剧创作系统（常驻上下文）：11个 short-drama 技能已全部部署在 duanju profile（storyboard 为用户定制升级版）。项目《末世选择》在 ~/duanju/，EP001 五文档只缺视频提示词；produce 需配供应商 API key（未配）。备份仓库 1476560380-eng/drama-skills-backup。说明书在 ~/duanju/短剧创作系统使用说明书.md+.pdf。
§
文档偏好：给用户的说明书/手册要写成「别人也能看懂能上手」的完整操作文档——按步骤走、每步给出对 AI 说的原话示例、含状态表和接手必读约定，而不只是给自己的速记。
§
短剧系统：11 个 short-drama 技能部署在 duanju profile，项目《末世选择》在 ~/duanju/末世选择/。备份库 1476560380-eng/drama-skills-backup（本地 ~/drama-skills-backup，四区：skills=升级版、vendor=官方快照、projects=项目文本、docs=说明书）；短剧相关内容一律进该库，勿混入 hermes-backup/astock-backup。推送走代理 127.0.0.1:7897。
§
版本号铁律（用户明确要求）：每一次改进或完善都必须给版本号。规则：MAJOR=契约/格式破坏性变更，MINOR=新增能力，PATCH=修bug/文字。每次改完同步：①VERSION ②CHANGELOG.md ③说明书版本号+PDF ④git tag push。CHANGELOG 每条按三段式记：改了哪些/优化了哪些/兼容性验证。
§
updream 接入（B站系 AI 视频创作平台 www.updream.cn）：无开放 API，对接方式=技能移植（Skill 社区）+ 项目文件平移到画布。updream 技能（updream-skill-ops/publishing）和一切 updream 相关文件**不备份**（用户 2026-10-23 明确要求）。updream 登录=手机号 13290018459+短信/密码；用户密码 12qwas 已两次暴露在聊天记录里，已建议他改密码（未确认已改）。原「分镜技能 updream 版草稿」文件已不存在（~/duanju 下已清理）。
§
本地浏览器弹窗工作流（2026-10-20 跑通）：让用户亲眼看到并亲手输密码的浏览器窗口，需 ①系统默认浏览器必须是 Chrome（原为夸克，已改 LSHandlers plist 的 http/https→com.google.chrome 并 killall -HUP lsd）②hermes config set browser.use_real_profile true --profile duanju ③browser.headed true ④先 pkill 残留的 headless chrome（匹配 user-data-dir=...browser-profile）和 agent-browser 守护进程，否则旧 headless 进程被复用永远不弹窗、且 agent-browser 缓存旧 CDP 端口报 connection refused。弹窗后用户手输登录，登录态留在会话里供后续自动化。用户习惯直接在聊天里发密码/验证码——必须拒绝使用聊天里的凭据，改走此弹窗通道。
§
短剧工作流纪律（用户反复强调）：①讨论方案时"先不要部署/先讨论不要改东西"是硬约束，他点头才动文件；②让他看效果=给A/B/C对照案例让他复制去自己的工具出图，不是替他改文件；③偏离具体例子回到技能层讨论时他会纠偏（"我们讨论的是完善技能的问题不是具体例子的问题"）；④改进技能前先机器审计现有产出取证（如58帧统计镜头词0次），用数据说话。v2.9.0待办（C版测试通过后动手）：keyframe-craft渲染三件套+微表情静帧化+段级调色（画风句拆质感锁/调色可覆盖两截）+光线时间锚点+video-prompts生成包声明（N hard-cut shots, total Ns+数字时长配语义锚）+运镜中英映射表（缓推=slow dolly in非zoom）。素材：github Rylaispirit/cinematic-video-prompt-skill词表+docx参考机制层。
§
改动外部仓库/技能/项目文件前先给方案+代价，等用户逐项确认；他反复强调「不要私自部署」「先让我确认好」。只读分析不限。
§
短剧系统补录：①对标研究——MarkQWu 复刻线不采但三层控制模型可借鉴；nianjiang888/storywright 的 ShotLock 15 条规则实测有料。②ShotDeck（收费）已入工作流：每镜「ShotDeck 参考」行=逐词中英对照，放生成包行下一行。③多镜容器生成器已固化：/Users/zhishu/duanju/锤爆世界/项目开发/gen_containers.py（v2.23.0，2026-10-27，七项修复已落地，改容器只改生成器重跑、不手改产物）。
§
多镜容器 v2 七项规则（v2.23.0 写死在 gen_containers.py）：①风格块=首镜质感锁原文(含 Horizontal 16:9)+三项禁止，段头色调只作块外「本段色彩意图」行，禁止叠进可复制块(mid/low-key打架) ②每镜【镜头参数】=源分镜 Shot on 句(含黑血 never red) ③时间锚=本镜Xs(本包Ys中的a–bs)+包级硬切声明 ④位置承接按人名归属中文句，空镜写无人物 ⑤容器禁元话语(理由/本镜职责/破格/动作链见)，留分镜给剪辑 ⑥本镜画内人物=视觉依据∪英文首帧点名(映射读视觉设定「画面代称」，漏登记自动兜底标⚠️) ⑦中英人名双轨保留。