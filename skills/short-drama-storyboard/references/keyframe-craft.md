# Frozen Keyframe Craft

## 目录

- [Boundary and instant tests](#boundary-and-instant-tests)
- [Purpose](#purpose)
- [Ordered recipe](#ordered-recipe)
- [尾帧：什么时候可以有，以及它换来什么代价](#尾帧什么时候可以有以及它换来什么代价sht-17)
- [Start-only drafting discipline](#start-only-drafting-discipline)
- [Static test](#static-test)

## Boundary and instant tests

- `SHT-05` — Project exactly one accepted shot boundary and bind the exact
  Character/Look, Location/View, and Prop/State variants visible there.
- `SHT-06` — Describe one freezeable instant. Ordered action, expression arcs,
  camera movement, and transforming weather belong to motion, not the keyframe.

## Purpose

Describe one frame that can exist at a single instant and accurately anchors the
accepted shot. A keyframe is not a compressed video prompt.

## Ordered recipe

1. **Purpose:** what the audience must notice now.
2. **Focal subject:** exact asset and variant IDs.
3. **Frame:** shot size, angle, lens intent, aspect-aware composition.
   镜头语言在这里落地。lens intent 不是器材参数，是**渲染指令**——它控制画面
   的空间感、透视和焦点分配，选法分三层，全部 `craft_default`：

   | 层 | 选法 | 例子 |
   |---|---|---|
   | ① 段基准 | SEG 段落头声明本段基准焦段/景深口径，段内帧默认继承——重复即设计，跨镜一致性白送 | 「本段基准 35mm 深焦」 |
   | ② 逐镜破格 | 本镜有特殊戏剧意图时点名破格+写理由（镜头语言是叙事决定） | 恐怖入侵感=广角近拍；孤独=长焦压缩；心理扭曲=畸变 |
   | ③ 兜底表 | 段基准未定时按景别起步：远景/奇观 35mm deep focus；全景 35mm；中近景 50mm f/2.8；近景 85mm f/2.0；特写 85mm f/1.8（macro 可用）——只兜底，不主动套用 |

   破格的判断顺序：先问这一镜要让观众**感觉**到什么（攻击性？孤立？窥视？平静？），
   再选服务这个感觉的镜头语言；答不出特殊意图才落兜底表。同一场景重复同一焦段
   本身是设计（观众第三次看到就知道「又来了」），不要为变化而变化。

   落进英文正文的写法：镜头声明紧跟画风句（`Shot on 35mm lens, f/5.6, deep focus` /
   `Shot on 85mm lens, f/1.8`），焦点分配写在主体描述之后（`Razor-sharp on his eyes,
   the background dissolving into soft bokeh` / `subject sharp, background softly
   blurred`）。焦段只写 24/35/50/85 四档锚点——图像模型不是真光学系统，档位更细
   是浪费 token；f 值只用语义轴：深焦 f/5.6 以上、叙事 f/2.8、浅焦 f/2.0 以下。
   UI 板/平面文字类镜头可用 `flat view` 覆盖整个镜头声明。
4. **Geography:** Location/View, fixed anchors, foreground/background zones.
5. **Boundary projection:** exact start position, body facing, pose, gaze, hands,
   held props. Give body facing for every person — it fixes which screen side they
   hold and which side the next reverse cuts from; `gaze` does not cover it. Add
   head facing only when it differs from body facing.
6. **Performance instant:** one visible expression/tension state, not an arc.
   Pick a channel the current shot size can actually read — gaze, breath, body
   set, object handling, or a held decision. A wide shot cannot carry an eyelid;
   a close-up cannot carry a full-body retreat. Naming only the emotion ("愤怒")
   leaves the translation to a downstream stage, and the keyframe is the first
   frame — a mistranslation there is wrong from frame one.
   情绪名不是画面。落到正文时从一个**可见通道**里选词，候选词表（按部位，当前
   景别读得出的才用）：

   | 通道 | 候选词 |
   |---|---|
   | 眼 | 瞳孔猛缩、目光钉在、避开视线、眼眶发红、眨眼频率变快、失焦 |
   | 眉/额 | 眉心拧起、眉梢挑起、额头绷紧、抬眉停住 |
   | 口鼻 | 嘴角抽动、嘴唇抿成线、唇色发白、喉结滚动、咬住下唇、呼吸变浅 |
   | 手 | 指节攥白、指尖发抖、手指收拢又松开、拇指摩挲、手停在半空 |
   | 肩背 | 肩膀绷直、肩膀垮下来、微微后缩、脊背挺住不动 |
   | 整体 | 僵住、晃了一下、重心前压、退了半步又站定 |

   词表是候选库不是公式：同一个「克制」可以走手（拇指摩挲）也可以走肩（绷直），
   选当前景别和人物性格读得出的那一个。写在正文里的是那个具体通道的词，不是
   情绪名本身——「愤怒」留给镜头职责字段，「指节攥白」才进关键帧。
7. **Light and atmosphere:** inherit accepted direction/time/weather; add only
   frame-relevant detail.
8. **Text policy:** readable/symbolic/blank/postproduction for visible surfaces.
9. **Exclusions:** contradictions or drift likely for this frame.

Identity and boundary facts remain source references. The keyframe owns focal,
composition, camera/lens, frame-only staging, and exclusions.

### 写完之后过一遍可渲染检查

检查接手的人能否读出当前帧必须保持的可见事实。按构图和镜头职责核对下表，
只补本帧实际需要的内容：

| 检查内容 | 信息缺失时的风险 |
|---|---|
| 每个人在哪、彼此距离多少（"站在他正前方约两步"） | 人物间距逐镜漂移，观众读成换了场地 |
| 构图需要纵深时，前景、中景、背景分别承载什么 | 层次不明，主体与背景混在一起 |
| 视线该落在哪（本镜的视觉重点） | 画面平均用力，观众不知道该看谁 |
| 构图方式与景别 | 同一场每镜构图随机，剪不到一起 |
| 机位在轴线哪一侧、俯仰角度、焦段意图 | 越轴；正反打方向对不上 |
| 光从哪来、什么质感 | 同场光位逐镜跳变 |
| 每个在场者的姿态、朝向、手部、持物 | 下一镜接不住，道具凭空易手 |
| 与上一镜连续的关键状态在本帧具体是什么 | 只写“同上”，当前正文无法独立说明状态 |

连续性核对时可以与上一镜比较；可复制正文仍须写出当前帧的位置、持物和其他必要状态，
不能用“与上一镜相同”代替执行端本次需要的事实。

**`craft_default`：一件事只说一次。** 合并能自然衔接的句子，删除重复事实和不帮助确定画面的铺垫。
不设通用字数门槛；保留当前帧所需的身份、空间、构图、光线、文字和连续性事实。

以下合成片段示意构图与静态事实的组织方式：

```text
竖屏 9:16 中近景。机位在轴线左侧、高约一米二，平视略低约五度，中焦 50mm。前景是长凳
扶手与半张湿报纸（占下缘约六分之一）；中景是两人对峙；背景是虚焦的候车牌。三分构图，
她落在右三分线上。她：坐长凳右端，双手交叠压膝，身体朝向正前，视线落在对方鞋尖，
无持物。人物乙：站她正前方约两步、略偏画面左，双手插袋，身体朝向她，头略偏向出口。
光自画面右上顶棚缝隙斜下为主光（硬），左侧留暗，无补光。视觉重点在她压膝的双手。
排除：无动作过程，无雨丝拖影。
```

Every visible entry the finished frame carries is listed in the shot's required
`视觉依据` field, resolving to a real `视觉设定.md` entry; an `IMG-...` prompt item
in `图片提示词.md` is a separate axis and does not stand in for it, and
`视觉设定.md` itself does not define `IMG-...` IDs. Write that list from the
finished frame, not from the shot's intent — the subject that gets missed is the
one that entered the composition while the frame was being written. A frozen frame may determine whether the surface
is legible in this composition; it may not replace the exact wording or policy
with an untraceable prose instruction. If the policy is still undecided, say so
instead of inventing a hidden candidate state.

## 曝光校准（Exposure Lock）

**每条关键帧正文必须有一句曝光句。** 只写 `moody` / `dark` / `low-key` / `night` 而不给曝光指令，模型会按最省事的方式渲染：暗部糊成一片、高光烧白、肤色发灰。实测三集 80 条关键帧里 52 条含暗调词、**0 条**含曝光控制——这就是出图偏暗的直接原因。

### 固定句式（按光况选一条，紧跟画风句与镜头声明之后）

| 光况 | 固定句 |
|---|---|
| 夜景／低照度 | `Exposure balanced for night: shadows open with visible detail, practical lights protected from clipping` |
| 日景／强光 | `Exposure balanced for daylight: highlights held on sunlit surfaces, faces not crushed into shadow` |
| 火光／强源光 | `Exposure balanced for firelight: flame cores not blown out, faces readable in the falloff` |
| 雪/水面/白墙反光 | `Exposure balanced for high-albedo surfaces: whites held just below clipping, texture kept` |
| 主动剪影（设计如此） | `Intentional silhouette: figure edges readable against the lit background, no detail inside the silhouette` |

### 三条硬边界

- **暗部不允许糊死**：夜景也要写 `shadow detail`；真正要黑的地方写清是"暗但可辨"还是"纯黑剪影"，二者不可混写。
- **高光不允许烧白**：光源（路灯、车灯、光幕、火焰核心）必须写 `protected from clipping`；光幕/UI 类另加 `text remains legible, no bloom washing out the characters`。
- **面部受光要交代来源**：人物在画面里时写 `face lit by <光源>`（侧逆光、手机屏、火光），否则夜景人脸的曝光由模型瞎定，同一集内会忽明忽暗。

### 段头配套：曝光基准

SEG 段落头建议加一行「曝光基准」，写本段的整体亮度口径，段内帧默认继承：

```text
曝光基准：夜景低照度但保暗部，高光不剪（路灯暖点最亮）
```

段内确有亮度变化（如从暗室走向火海）时，在该镜正文单独写破格的曝光句，不靠段头糊过去。

---

## 尾帧：什么时候可以有，以及它换来什么代价（`SHT-17`）

默认每镜一张首帧，冻结 `start_boundary`。交付工作流需要首尾帧时，再补一张投影
`end_boundary` 的尾帧；两帧之间的运动仍按分镜边界和运动提示词实现。

**`structural_invariant`**：《分镜.md》的首帧与收尾关键帧分别指向同一镜头已接受的起点与终点。
**尾帧是 `end_boundary` 的投影，
不是新的终点事实**——它与首帧对 `start_boundary` 的关系完全一样：可以决定这一帧怎么构图、
用什么景别镜头、光怎么落，不能决定人在哪、手里有什么、看着谁。尾帧与镜头终点不一致时，
错的是尾帧。

每镜的关键帧数量**不是固定的**。默认一张首帧；只有当交付工作流真的要消费尾帧时才加一张，
不为凑齐而画。补尾帧不改变 `SHT-10`：首帧仍然只能写 start 事实，尾帧只能写 end 事实，
两张各自守自己的边界，不互相借用。

**代价要说清楚：交出一对首尾帧，等于把两帧之间的运动交给了执行端插值**。 而运动路径本来
是运动规格拥有的东西。所以选了首尾帧接续的镜头，其运动规格不是"照旧再写一遍"，而是被
两端夹住了：它仍然要写清中间必须发生什么（动作顺序、对白落点、摄影机行为），但要意识到
执行端会优先满足两端的画面一致性。因此——

- 中间必须被看到的动作**不要只靠插值兑现**。如果一个动作是本镜存在的理由，两端之间没有
  任何东西保证它会发生，就该拆镜，或者让该动作落在其中一端。
- 两端差异越大，插值越自由，中间越不可控。首尾帧接续适合"状态改变清楚、路径无所谓"的
  镜头（转身、递交完成、坐下），不适合"路径本身是戏"的镜头。
- 终点报告仍然对照镜头 `end_boundary`，不对照尾帧。尾帧只是它的投影，不能自证到达。

## Start-only drafting discipline

**`SHT-10 · reviewed_invariant`**: rendered keyframe prose may contain only facts
from the boundary that frame declares. 首帧写进任何由运动或终点首次产生的事实是漂移；
尾帧写进在它之前就已经消耗掉的事实同样是漂移。两帧各守各的边界，不互相借用。

关键帧默认投影镜头起点，不能直接选取“本镜最有戏的时刻”。为避免提前写入终点事实：

1. 先明确本帧冻结 `SHOT-...` 的起点，草拟正文时暂不读终点与运动描述；
2. 只填起点已成立的位置、姿态、目光、双手、持物和可见状态；
3. 再对照终点，找出动作后才产生的事实，确保它们未进入起始关键帧正文；
4. 写完 Markdown 后从自然语言反向提取手位、持物、目光和可见状态，与镜头起点再比一次；
   不能只看条目说明而忽略真正交付的正文。

反例：start 是“右手空置、看对方”，end 是“右手握铃绳、看门”。冻结帧写
“手已握铃绳”会提前写入终点事实，属于边界漂移。

## Static test

Ask: could a still photographer capture every described fact at once?

Move these to motion:

- ordered verbs (先、再、随后、最终);
- expression changing from A to B;
- camera push/pan/track over time;
- entering/leaving/turning/reaching sequences;
- dialogue delivery arc or sound progression;
- light/weather transforming during the shot.

A single held pose may imply tension, but it must not require several moments.

### 微表情的静帧化（判例与禁句）

Static test 的边缘地带：`mouth corner twitching` 这类「一次微动作」写法。它描述的是
一个可冻结的瞬间，不违反 Static test，但图像模型容易渲染成运动模糊脸或夸张鬼脸。
处理办法二选一，按 `craft_default`：

1. **动作后定格**（优先）：把进行时改写为动作刚完成的状态——`mouth corner caught
   just after a single twitch` / `eyes just snapped back into focus`。语义还是那一下，
   但渲染指令是静止的。
2. **具体禁句**兜底：动作必须保持进行时写法时，句尾加 `no motion blur on face` /
   `tears stay in her eyes, never fall` 这类**说结果**的禁句。禁句要具体到画面结果，
   「静止」「不模糊」这类抽象禁令模型不执行；「never fall」之所以有效是因为它说了
   泪该在哪。

判例：`snatching`（抢夺中）→ 改 `fingers locked on the handle mid-grab`；
`falling to knees` → `caught at the instant knees hit the floor`；`smiling
wider and wider` → 改成单一定格宽度 `smile stretched ear to ear`（后者本身
就是静帧合法写法，因为「拉到最宽」是状态不是过程）。

## Prompt economy

Do not restate full character or location 设定集s. Bind accepted variants and
repeat only facts the frame needs to prevent ambiguity: distinguishing anchor,
current Look, crucial spatial anchor, held prop, light direction, text state.

Generic “cinematic, 8K, masterpiece” language cannot replace subject identity,
geography, composition, or continuity.

## 画风句与段级调色（质感锁 + 调色可覆盖）

关键帧的画风统一句拆成两截，各自的生命周期不同：

- **质感锁**（全局统一，永不变）：`photorealistic cinematic still, soft film
  grain` 这类管「介质质感」的词。全集共用，保证「像同一部片」。
- **调色词**（段级可覆盖）：`teal-and-amber grade` 这类管「色彩氛围」的词，
  **从 SEG 段落头的色调设计按段翻译**，不再全局锁死。火海段可以整段
  `fire-orange grade`，夜视段整段 `green night-vision grade`。

为什么必须拆：段落头的色彩翻转设计（v2.8.0）如果进不了英文帧，就只是中文说明，
渲染层永远全局一个色调——设计与执行两张皮。段内帧继承本段调色词，段间按翻转设计
切换，这才闭环。同一段落内调色词必须一致；翻转没有叙事动机时不得换词（那是穿帮
不是设计，见 lighting-craft 的段间色彩翻转）。

常用中文色调 → 英文 grade 词对照（起步词表，可扩展）：

| 段落色调设计 | 英文调色词 |
|---|---|
| 暖黄室内 / 治愈温暖 | warm amber grade |
| 冷蓝夜色 / 骤冷恐怖 | cold blue-grey grade |
| 火光 / 爆发 / 橙红战场 | fire-orange grade |
| 灰烬 / 战后死寂 | desaturated ash-grey grade |
| 夜视 / 科技监控 | green night-vision grade |
| 系统UI / 电蓝 | electric-blue grade |
| 晨光 / 平静收口 | dawn-grey grade / soft morning-light grade |
| 诡异绿 / 异变 | sickly green grade |
| 夕阳情绪收口 | golden-hour grade |
| 无特定设计 | moody teal-and-amber grade（默认，段头未声明时） |

**光线时间锚点**（同批处理）：SEG 段落头加一行「光线锚点」——`night / moonlit /
lamplit / dawn / blue hour / overcast / harsh noon`——段内帧继承进正文。夜戏帧
没有夜光词，图像模型就按默认白昼渲染；时间锚点是段的口径，不是每帧自由发挥。

帧尾**情绪钩子**（可选，`craft_default`）：正文收尾处加一个 mood 词
（`ominous / tense / serene / awe-struck / melancholic`），给调色和氛围一个明确
的渲染方向。一帧只加一个，不堆砌；情绪已经由画面内容说清时不加。

## Failure examples

- incompatible Looks appear in the same frame;
- “turns, runs, then looks back” appears in a still;
- the start hand/prop differs from the shot boundary;
- background changes location identity or orientation;
- light direction resets without source change;
- readable evidence is paired with no-text;
- prompt lists subjects but not their spatial relationship;
- framing has no focal hierarchy.
- structured projection matches start but rendered prompt describes a fact that
  first appears in the shot end or motion.
