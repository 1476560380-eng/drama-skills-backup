#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从「剧集/EPxxx/分镜.md」生成多镜容器提示词（15 秒包 · 平台 @ 引用版）。

通用版：任意集，只要该集有 分镜.md + 视觉设定.md。
用法：python3 gen_containers.py EP001 [--write]

数据来源（只读）：
  剧集/<EP>/分镜.md      —— 镜头时间码、SEG、生成包总表、逐镜字段
  剧集/<EP>/视觉设定.md  —— 资产名白名单（人物/造型/地点/道具）
输出：剧集/<EP>/多镜容器提示词-15秒包.md
"""
import argparse, re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

STYLE_HEAD = ("3D 国漫半写实高级 CG 风格，轻度风格化，影视动画人物资产级渲染，"
              "整体参考高规格角色资产图与游戏角色设定图的渲染效果")
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import voice_cast

BAN = "禁止出现字幕，禁止出现背景音乐，禁止出现水印"
MAX_SEC, MIN_SEC = 15.0, 4.0

def field(block, name):
    m = re.search(rf"^- \*\*{name}\*\*：(.+)$", block, re.M)
    return m.group(1).strip() if m else None

META_PAT = re.compile(r"(本版|原版|正式版|呼应 ?EP\d+|相对原版|这一版)")


def strip_meta(v):
    """把元说明从要进容器的字段里剥掉，避免模型把「解释原版」读成指令。"""
    if not v:
        return v
    v = re.sub(r"（[^）]*(?:本版|原版|正式版|呼应 ?EP\d+|破格|动作链见)[^）]*）", "", v)
    v = re.sub(r"[；，]?(?:本版新增的笑点|本版的笑点核心|本版)[－—-]?", "", v)
    v = re.sub(r"(?:此镜|这一镜)?新增的|新加的", "", v)
    v = re.sub(r"[；，]?\s*理由：[^；。]*", "", v)
    return v.strip(" ；。")


def warn_meta(tag, v):
    if v and META_PAT.search(v):
        print(f"   ⚠️ 字段里仍有元话语（{tag}）：{v[:40]}…")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep"); ap.add_argument("--write", action="store_true")
    ap.add_argument("--src", default=None, help="自定义源分镜路径"); ap.add_argument("--out", default=None, help="自定义输出文件名")
    a = ap.parse_args()
    ep_dir = ROOT / "剧集" / a.ep
    fan_p = pathlib.Path(a.src) if a.src else ep_dir / "分镜.md"
    sheet_p = ep_dir / "视觉设定.md"
    if not fan_p.exists(): sys.exit(f"缺 {fan_p}")
    fan = fan_p.read_text(encoding="utf-8")
    sheet = sheet_p.read_text(encoding="utf-8") if sheet_p.exists() else ""

    # 资产白名单（视觉设定条目名）
    assets = {}
    for kind, name in re.findall(r"^## (人物|造型|地点|道具) · (.+?)\s*$", sheet, re.M):
        assets.setdefault(kind, set()).add(name)

    # 全局口径
    style_lock = re.search(r"画风统一句（质感锁，每条关键帧共用）：`([^`]+)`", fan)
    style_lock = style_lock.group(1) if style_lock else ""
    voice_line = re.search(r"^- 配音音色总表：(.+)$", fan, re.M)
    voice_line = voice_line.group(1).strip() if voice_line else ""
    voices = {}
    for part in voice_line.split("｜"):
        if "=" in part:
            k, v = part.split("=", 1); voices[k.strip()] = v.strip()

    # 生成包总表
    pkg_table = []
    for m in re.finditer(r"^\| (\d+) \| (SHOT-(\d+)~(\d+)) \| ([\d.]+)s \|(.*)\|?$", fan, re.M):
        pkg_table.append((int(m.group(1)), m.group(2), float(m.group(5)), m.group(6).strip(), m.group(3), m.group(4)))

    # SEG 与镜头
    segs = {}   # seg_id -> (title, color)
    for m in re.finditer(r"^## (SEG-\d+) (.+?)（SHOT-[\d~]+ · ([\d.]+)s）", fan, re.M):
        segs[m.group(1)] = (m.group(2), None)
    seg_colors = {}
    for chunk in re.split(r"\n(?=## )", fan):
        if chunk.startswith("## SEG-"):
            sid = chunk.split(" ")[1]
            mc = re.search(r"色调：([^。；\n]+)", chunk)
            if mc: seg_colors[sid] = mc.group(1).strip()
    cur_seg = None
    shots = []
    for chunk in re.split(r"\n(?=## )", fan):
        if chunk.startswith("## SEG-"):
            cur_seg = chunk.split(" ")[1]
        m = re.match(r"## (SHOT-{}-\d+) · (.+?)（([\d.]+)[–\-]([\d.]+)s）".format(a.ep), chunk)
        if m:
            shots.append(dict(sid=m.group(1), title=m.group(2), t1=float(m.group(3)),
                              t2=float(m.group(4)), seg=cur_seg, block=chunk))
    if not shots: sys.exit("分镜里没解析到镜头")

    # 每镜资产（从视觉依据行抽资产名）
    def assets_of(block):
        out = {"人物": [], "造型": [], "地点": [], "道具": []}
        vis = field(block, "视觉依据") or ""
        for kind, name in re.findall(r"[·；]\s*(人物|造型|地点|道具)「([^」]+)」", "·" + vis):
            if name not in out[kind]: out[kind].append(name)
        return out

    # 中英人名映射：从视觉设定「画面代称」读，源头唯一
    en2cn = {}
    for m in re.finditer(r"^## 人物 · (.+?)\s*$(.*?)(?=^## |\Z)", sheet, re.M | re.S):
        mm = re.search(r"画面代称：([A-Za-z][A-Za-z .()]*?)\s*$", m.group(2), re.M)
        if mm: en2cn[mm.group(1).strip()] = m.group(1).strip()
    EN_PAT = "|".join(sorted((re.escape(k) for k in en2cn), key=len, reverse=True)) or r"ZZZNOMATCHZZZ"

    def kf_parts(block):
        """关键帧拆三段：style（Horizontal…质感锁）/ content（首帧正文）/ tech（Shot on…）"""
        m = re.search(r"### 冻结关键帧提示词\s*\n((?:>.*\n?)+)", block)
        out = {"style": "", "content": "", "tech": ""}
        for ln in (m.group(1).split("\n") if m else []):
            s = ln.lstrip("> ").strip()
            if not s: continue
            if s.startswith("Horizontal"): out["style"] = s
            elif s.startswith("Shot on"): out["tech"] = s
            elif not out["content"]: out["content"] = s
        return out

    def people_of(block, kf_content=""):
        """本镜画内人物 = 视觉依据登记 ∪ 英文首帧里点名的人（后者兜底源头漏登记）"""
        ppl = list(assets_of(block)["人物"])
        for en in dict.fromkeys(re.findall(EN_PAT, kf_content)):
            cn = en2cn[en]
            if cn not in ppl: ppl.append(cn)
        return ppl

    def pos_sentence(en):
        """英文首帧 → 中文位置句：同名与下一人名之间的方向词都归该人"""
        marks = [(m.start(), m.end(), m.group(0)) for m in re.finditer(EN_PAT, en)]
        pairs = []
        for i, (s0, s1, nm) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else len(en)
            who = en2cn[nm]
            for d in re.findall(r"on screen-(left|right)|facing screen-(left|right)|entering from screen-(left|right)",
                                en[s1:end]):
                if d[0]: pairs.append(f"{who} 画面{'左' if d[0]=='left' else '右'}")
                elif d[1]: pairs.append(f"{who} 面朝画面{'左' if d[1]=='left' else '右'}")
                else: pairs.append(f"{who} 从画面{'左' if d[2]=='left' else '右'}进入")
        return "；".join(dict.fromkeys(pairs))

    def keyframe_of(block):
        m = re.search(r"### 冻结关键帧提示词\s*\n((?:>.*\n?)+)", block)
        if not m: return ""
        lines = []
        for ln in m.group(1).split("\n"):
            s = ln.lstrip("> ").strip()
            if not s: continue
            if s.startswith("Horizontal 16:9"): continue
            if s.startswith("Shot on"): continue
            lines.append(s)
        return " ".join(lines)

    def speakers_of(block):
        vo = field(block, "配音指令") or ""
        return [l.split("｜")[0].strip() for l in vo.split("\n") if "｜" in l and l.strip()]

    def color_of(sid):
        for s in shots:
            if s["sid"] == sid: return seg_colors.get(s["seg"], "按 SEG 段头")
        return ""

    def loc_of(a_):
        return "、".join(a_["地点"]) if a_["地点"] else "（见分镜视觉依据）"

    lines = []
    lines.append(f"# {a.ep} 多镜容器提示词 · 15 秒包（平台 @ 引用版）")
    lines.append("")
    _src = pathlib.Path(a.src).name if a.src else "分镜.md"
    lines.append(f"> 由 `项目开发/gen_containers.py` 生成；源：`剧集/{a.ep}/{_src}` + `视觉设定.md`。")
    lines.append(f"> 切包规则：模型单次上限 15s；一包不跨 SEG（场景与色调不混）；尾包不低于 4s。")
    lines.append(f"> 共 {len(pkg_table)} 包 / {len(shots)} 镜 / {shots[-1]['t2']:.1f}s。")
    lines.append("> 出场人物／场景／道具取自每镜「视觉依据」，与素材库资产名逐字一致才能挂上芯片。")
    lines.append("")
    lines.append("## 分包总表")
    lines.append("")
    lines.append("| 包 | 镜头 | 时长 | 场景 | 出场 | 道具 |")
    lines.append("|---|---|---|---|---|---|")
    shot_by_tail = {}
    for s in shots: shot_by_tail[str(int(s["sid"].split("-")[-1]))] = s
    for num, rng, dur, _, lo, hi in pkg_table:
        members = [shot_by_tail[str(i)] for i in range(int(lo), int(hi) + 1) if str(i) in shot_by_tail]
        ch, pr, lc, dp = [], [], [], []
        for s in members:
            a_ = assets_of(s["block"])
            ch += [x for x in a_["人物"] + a_["造型"] if x not in ch]
            lc += [x for x in a_["地点"] if x not in lc]
            dp += [x for x in a_["道具"] if x not in dp]
        members_s = f"SHOT-{lo}~{hi}（{len(members)} 镜）"
        lines.append(f"| {num:02d} | {members_s} | {dur:.1f}s | {'、'.join(lc) or '—'} | {'、'.join(ch) or '—'} | {'、'.join(dp) or '—'} |")
    lines.append("")

    # ===== 音色总表（本集真正开口的常驻角色）=====
    VD = voice_cast.load()
    EX = voice_cast.load_exceptions()
    VER = "搞" if "搞笑" in str(a.src or "") else "原"
    ep_voices = voice_cast.episode_voices(fan, VD)
    if ep_voices:
        lines.append("## 配音音色总表（本集常驻角色 %d 人）" % len(ep_voices))
        lines.append("")
        lines.append(voice_cast.header_table(ep_voices, VD))
        lines.append("")
        lines.append("> 这张表是**核对标尺**，不是中文 TTS 的控制参数。中文 TTS（火山、MiniMax）不认文字描述，"
                     "必须先用末尾「英文音色 prompt」在 Voice Design 里生成音色、导出参考音，再拿参考音克隆。")
        lines.append("> 每镜【台词】里的括号＝该镜的音色锚点（编号｜音区·质感·气息｜语气｜音量档）；语气四值：真诚／装的／压着／随口，逐句例外见 `设定集/语气例外.md`；禁令只在这张表里，不逐镜重复。只出现一次的角色（白大褂、花衬衫等）不设音色卡，按台词里的标签演。")
        lines.append("")

    for num, rng, dur, _, lo, hi in pkg_table:
        members = [shot_by_tail[str(i)] for i in range(int(lo), int(hi) + 1) if str(i) in shot_by_tail]
        seg_id = members[0]["seg"]
        seg_title = segs.get(seg_id, ("",))[0]
        t1, t2 = members[0]["t1"], members[-1]["t2"]
        ch, pr, lc, dp = [], [], [], []
        for s in members:
            a_ = assets_of(s["block"])
            ch += [x for x in a_["人物"] + a_["造型"] if x not in ch]
            lc += [x for x in a_["地点"] if x not in lc]
            dp += [x for x in a_["道具"] if x not in dp]
        color = color_of(members[0]["sid"])
        lines.append(f"## 生成包 {num:02d} · {seg_id} {seg_title}（SHOT-{lo}~{hi}）")
        lines.append("")
        prev = "本包为全片第一包，无上一节" if num == 1 else f"上一包尾帧＝SHOT-{int(lo)-1:03d} 终点，首镜＝{members[0]['title']}"
        nxt = f"末镜＝{members[-1]['title']}，移交下一节" if num < len(pkg_table) else "末镜＝本集最后一格，交给下一集开场"
        durs = [s_["t2"] - s_["t1"] for s_ in members]
        lines.append("| 包级信息 | 内容 |")
        lines.append("|---|---|")
        lines.append(f"| 硬切镜数 | {len(members)} 个硬切镜，总 {t2-t1:.1f}s，逐镜 {'/'.join(f'{d:.1f}' for d in durs)}s |")
        lines.append(f"| 场景 | {'、'.join('@' + x for x in lc) or '无'} |")
        lines.append(f"| 出场人物（仅挂芯片，画内以逐镜为准） | {'、'.join('@' + x for x in ch) or '无'} |")
        lines.append(f"| 道具 | {'、'.join('@' + x for x in dp) or '无'} |")
        lines.append(f"| 全集绝对时间 | {t1:.1f}–{t2:.1f}s |")
        lines.append(f"| 跨节接镜 | {prev}；{nxt} |")
        lines.append("")
        lines.append(f"> 本段色彩意图：{color}")
        lines.append("")
        lines.append("**本节风格提示词**（含禁止项，可直接复制）")
        lines.append("")
        lines.append("```text")
        style_src = kf_parts(members[0]["block"])["style"] or style_lock
        lines.append(f"{style_src.rstrip(' .')}；{BAN}")
        lines.append("```")
        lines.append("")
        for i, s_ in enumerate(members, 1):
            b = s_["block"]
            k = kf_parts(b)
            shot_loc = loc_of(assets_of(b))
            if shot_loc.startswith("（见分镜"): shot_loc = "、".join(lc) or shot_loc
            lines.append(f"### 镜头 {i} · {s_['sid']} · 本镜 {s_['t2']-s_['t1']:.1f}s（本包 {t2-t1:.1f}s 中的 {s_['t1']-t1:.1f}–{s_['t2']-t1:.1f}s）")
            lines.append("")
            lines.append(f"> 场景：{shot_loc}　｜　段：{seg_title}")
            lines.append("")
            reg = set(assets_of(b)["人物"])
            ppl = people_of(b, k["content"])
            extra = [x for x in ppl if x not in reg]
            tag = ("　⚠️源头漏登记：" + "、".join(extra)) if extra else ""
            lines.append(f"- **本镜画内人物**：{'、'.join('@' + x for x in ppl) or '无（空镜）'}{tag}")
            if k["content"]:
                lines.append(f"- **首帧锁定**：{k['content']}")
            if k["tech"]:
                lines.append(f"- **镜头参数**：{k['tech']}")
            else:
                lines.append("- **镜头参数**：（源分镜缺 Shot on 句）")
                print(f"   ⚠️ {s_['sid']} 源分镜缺 Shot on 句")
            jm = strip_meta(field(b, '景别/机位') or '')
            yj = strip_meta(field(b, '运镜') or '')
            lines.append(f"- **运镜**：{jm}。{yj}" if jm and yj else f"- **运镜**：{(jm or yj).rstrip('。')}")
            _pm = strip_meta(field(b, '起点 → 唯一动作 → 终点') or '')
            warn_meta(s_['sid'] + ' 画面', _pm)
            lines.append(f"- **画面**：{_pm}")
            pos = pos_sentence(k["content"])
            lines.append(f"- **位置承接**：{pos or '无人物'}")
            snd = field(b, "声音") or ""
            os_n = len(re.findall(r"\[OS\]", snd))
            if os_n:
                lines.append(f"- **OS**：×{os_n}（内容见【台词】）")
            lines.append(f"- **音效**：{snd or '无'}")
            vo = field(b, "配音指令") or ""
            if vo:
                def _one(utt, b=b, s_=s_):
                    segs2 = utt.split("｜")
                    out2, skip2 = [], False
                    for sg in segs2:
                        if skip2:
                            skip2 = False
                            note = re.search(r"（([^）]*)）", sg)
                            if note and "通讯" in note.group(1) and out2:
                                out2[-1] = out2[-1][:-1] + "·" + note.group(1) + "）"
                            continue
                        if sg.strip() in VD:
                            out2.append(voice_cast.voice_line(sg.strip(), VD, a.ep, s_["sid"], EX, VER))
                            skip2 = True
                        else:
                            out2.append(sg)
                    return "｜".join(out2)
                vo = "；".join(_one(u) for u in vo.split("；"))
            lines.append(f"- **台词**：{vo or '无'}")
            lines.append("")
        lines.append("")

    if ep_voices:
        lines.append("---")
        lines.append("")
        lines.append(voice_cast.english_section(ep_voices, VD))
        lines.append("")

    out = "\n".join(lines) + "\n"
    out_p = ep_dir / (a.out or "多镜容器提示词-15秒包.md")
    if a.write:
        out_p.write_text(out, encoding="utf-8")
        print(f"已写入 {out_p}（{len(pkg_table)} 包 / {len(shots)} 镜 / {shots[-1]['t2']:.1f}s）")
    else:
        print(out[:3000])
        print(f"...（干跑：{len(pkg_table)} 包 / {len(shots)} 镜 / {shots[-1]['t2']:.1f}s；--write 落盘）")

if __name__ == "__main__":
    main()
