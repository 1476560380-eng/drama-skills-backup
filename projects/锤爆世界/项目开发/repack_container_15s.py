#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 EP001 多镜容器提示词重新切包到「每包 ≤15s（模型单次上限）」，
并输出成平台可 @ 引用的格式（四槽+道具槽、资产名逐字、色调并入风格行）。

用法：
    python3 repack_container_15s.py            # 干跑，只打印分包表与体检结果
    python3 repack_container_15s.py --write    # 生成 md 文件

数据来源（只读，不改动）：
    剧集/EP001/分镜.md              —— 镜头绝对时间、SEG、逐镜「视觉依据」、音色表
    剧集/EP001/多镜容器提示词.md    —— 逐镜正文（运镜/画面/镜头技术/位置承接/音效/台词）
    剧集/EP001/视觉设定.md          —— 人物/造型/地点/道具资产名（白名单）
"""
import argparse
import re
import pathlib
from collections import OrderedDict

EP_DIR = pathlib.Path(__file__).resolve().parents[1] / "剧集" / "EP001"
FAN = EP_DIR / "分镜.md"
CONTAINER = EP_DIR / "多镜容器提示词.md"
SHEET = EP_DIR / "视觉设定.md"
OUT = EP_DIR / "多镜容器提示词-15秒包-at.md"

MAX_SEC = 15.0   # 模型单次生成上限
MIN_SEC = 4.0    # 太短的包没意义，尾包低于 4s 要回并

STYLE_HEAD = ("3D 国漫半写实高级 CG 风格，轻度风格化，影视动画人物资产级渲染，"
              "整体参考高规格角色资产图与游戏角色设定图的渲染效果")
BAN = "禁止出现字幕，禁止出现背景音乐"

VOICE = {"高铁锤": "低沉砂哑男中音", "冯彩虹": "急促偏软的青年男声",
         "卢不拔": "干硬无起伏的中年男声", "露西": "甜软少女音",
         "花衬衫医生": "油滑中年男声", "白大褂医生": "细窄男声",
         "秃鹫领头大汉": "粗咧男声"}

# 正文里的旧称呼/英文代称 → 视觉设定资产名
RENAME = [("White Coat", "白大褂医生"), ("Floral Shirt", "花衬衫医生"),
          ("Gao Tiechui", "高铁锤"), ("Feng Caihong", "冯彩虹"),
          ("Lu Bubai", "卢不拔"), ("Lead Enforcer", "秃鹫领头大汉"),
          ("Lucy", "露西")]

# 台词里的简称 → 视觉设定资产名（画外音说话人也要归一到资产名，否则会多出一个人物）
SPEAKER_ALIAS = {"领头大汉": "秃鹫领头大汉", "三锤": "高铁锤", "修女": "露西"}

RE_SHOT_TITLE = re.compile(r"^## SHOT-EP001-(\d+) · (.+?)（([\d.]+)[–\-]([\d.]+)s）", re.M)
RE_SEG = re.compile(r"^## SEG-(\d+) (.+?)（", re.M)
RE_BLOCK = re.compile(r"^镜头(\d+) / SHOT-(\d+)（([\d.]+)-([\d.]+)秒）：(.+)$")
RE_SHEET = re.compile(r"^## (人物|造型|地点|道具) · (.+?)\s*$", re.M)
RE_REF = re.compile(r"(人物|造型|地点|道具)「(.+?)」")


def parse_sheet():
    """视觉设定白名单：{类别: [名称…]}"""
    out = {"人物": [], "造型": [], "地点": [], "道具": []}
    for m in RE_SHEET.finditer(SHEET.read_text(encoding="utf-8")):
        out[m.group(1)].append(m.group(2).strip())
    return out


def parse_shots():
    text = FAN.read_text(encoding="utf-8")
    titles = list(RE_SHOT_TITLE.finditer(text))
    segs = [(m.start(), int(m.group(1)), m.group(2).strip()) for m in RE_SEG.finditer(text)]
    shots = []
    for i, m in enumerate(titles):
        body_start = m.end()
        body_end = titles[i + 1].start() if i + 1 < len(titles) else len(text)
        chunk = text[body_start:body_end]
        ref_line = ""
        for ln in chunk.splitlines():
            if ln.startswith("- **视觉依据**"):
                ref_line = ln
                break
        refs = [(c, n.strip()) for c, n in RE_REF.findall(ref_line)]
        seg = None
        for s_pos, s_no, s_name in segs:
            if s_pos < m.start():
                seg = (s_no, s_name)
        shots.append(dict(no=int(m.group(1)), title=m.group(2),
                          start=float(m.group(3)), end=float(m.group(4)),
                          seg=seg, refs=refs))
    return shots


def parse_blocks():
    """从已派生好的多镜容器文件里取逐镜正文（不重写源文档）。"""
    blocks = {}
    lines = CONTAINER.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        m = RE_BLOCK.match(lines[i])
        if not m:
            i += 1
            continue
        head = [x.strip() for x in m.group(5).split("｜")]
        body = []
        i += 1
        while i < len(lines) and lines[i].strip() and not RE_BLOCK.match(lines[i]):
            body.append(lines[i])
            i += 1
        blocks[int(m.group(2))] = dict(loc=head[0],
                                      seg_name=head[1] if len(head) > 1 else "",
                                      tone="｜".join(head[2:]) if len(head) > 2 else "",
                                      body=body)
    return blocks


def field(body, key):
    for ln in body:
        if ln.startswith(f"【{key}】"):
            return ln[len(key) + 2:]
    return ""


def dur(s):
    return round(s["end"] - s["start"], 2)


def dur_list(lst):
    return round(sum(dur(s) for s in lst), 2)


def pack(shots):
    """SEG 内贪心装包，每包 ≤MAX_SEC；尾包 <MIN_SEC 时回并或前借。"""
    out, cur = [], []
    for s in shots:
        if cur and dur_list(cur) + dur(s) > MAX_SEC + 1e-9:
            out.append(cur)
            cur = [s]
        else:
            cur.append(s)
    if cur:
        out.append(cur)
    if len(out) > 1 and dur_list(out[-1]) < MIN_SEC:
        tail, prev = out[-1], out[-2]
        if dur_list(prev) + dur_list(tail) <= MAX_SEC + 1e-9:
            out[-2] = prev + tail
            out.pop()
    return out


def norm_names(text):
    text = re.sub(r"白大褂(?!医生)", "白大褂医生", text)
    text = re.sub(r"花衬衫(?!医生)", "花衬衫医生", text)
    for a, b in RENAME:
        text = text.replace(a, b)
    text = text.replace("（内容见台词栏）（内容见台词栏）", "（内容见台词栏）")
    return text


def speakers_in(body):
    out = []
    for ln in body:
        m = re.match(r"^【台词】([^（(]+)[（(]", ln)
        if m:
            n = norm_names(m.group(1).strip())
            n = SPEAKER_ALIAS.get(n, n)
            if n not in out:
                out.append(n)
    return out


def beat(tech, which):
    if which == "起":
        m = re.search(r"起幅从(.+?)起", tech)
        return m.group(1) if m else ""
    m = re.search(r"落幅停在(.+?)(；|。|$)", tech)
    return m.group(1) if m else ""


def build(shots, blocks, sheet):
    # 地点 carry-forward：某镜视觉依据只写人物/道具时，继承同 SEG 上一镜的地点；
    # SEG 开头就缺的，用容器文件里那镜自己的地点（切包时已按 SEG 落好）。
    last_loc = {}
    for s in shots:
        seg_key = s["seg"][0]
        ref_locs = [n for c, n in s["refs"] if c == "地点"]
        if ref_locs:
            last_loc[seg_key] = ref_locs[0]
            s["loc_cf"] = ref_locs[0]
        else:
            s["loc_cf"] = last_loc.get(seg_key) or blocks[s["no"]]["loc"]

    groups = OrderedDict()
    for s in shots:
        groups.setdefault(s["seg"], []).append(s)

    packs = []
    for seg, lst in groups.items():
        for chunk in pack(lst):
            packs.append([seg, chunk])

    unknown, out = [], []
    for idx, (seg, chunk) in enumerate(packs, 1):
        chars, props, tones = [], [], []
        for s in chunk:
            t = blocks[s["no"]]["tone"].strip()
            if t and t not in tones:
                tones.append(t)
            for cat, name in s["refs"]:
                if cat == "人物":
                    if name not in sheet["人物"]:
                        unknown.append((s["no"], cat, name))
                    if name not in chars:
                        chars.append(name)
                elif cat == "造型":
                    owner = name.split("·")[0].strip()   # 造型 → 它的主人
                    if owner not in chars:
                        chars.append(owner)
                elif cat == "地点":
                    if name not in sheet["地点"]:
                        unknown.append((s["no"], cat, name))
                elif cat == "道具":
                    if name not in sheet["道具"]:
                        unknown.append((s["no"], cat, name))
                    elif name not in props:
                        props.append(name)
        locs = []
        for s in chunk:
            if s["loc_cf"] not in locs:
                locs.append(s["loc_cf"])
        speakers = []
        for s in chunk:
            for sp in speakers_in(blocks[s["no"]]["body"]):
                if sp not in speakers:
                    speakers.append(sp)
        for sp in speakers:                      # 只出声没写进视觉依据的也补上
            if sp not in chars:
                chars.append(sp)

        abs_start, abs_end = chunk[0]["start"], chunk[-1]["end"]
        total = round(abs_end - abs_start, 2)
        out.append(dict(no=idx, seg=seg, shots=chunk, total=total,
                        abs_start=abs_start, abs_end=abs_end,
                        loc=locs[0], locs=locs,
                        tone="；".join(tones),
                        chars=chars, speakers=speakers, props=props,
                        first_beat=norm_names(beat(field(blocks[chunk[0]["no"]]["body"], "镜头技术"), "起")),
                        last_beat=norm_names(beat(field(blocks[chunk[-1]["no"]]["body"], "镜头技术"), "落"))))
    return out, unknown


def blocks_tone(s):
    return BLOCKS[s["no"]]["tone"].strip()


def render(packs):
    L = ["# EP001 多镜容器提示词 · 15 秒包（平台 @ 引用版）\n",
         "> 由 `项目开发/repack_container_15s.py` 生成；源：`剧集/EP001/多镜容器提示词.md` + `分镜.md` + `视觉设定.md`。",
         f"> 切包规则：模型单次上限 {MAX_SEC:.0f}s；一包不跨 SEG（场景与色调不混）；尾包不低于 {MIN_SEC:.0f}s。",
         f"> 共 {len(packs)} 包 / {sum(len(p['shots']) for p in packs)} 镜 / "
         f"{round(sum(p['total'] for p in packs), 2)}s。",
         "> 出场人物／场景／道具取自每镜「视觉依据」，与素材库资产名逐字一致才能挂上芯片。\n",
         "## 分包总表\n",
         "| 包 | 镜头 | 时长 | 场景 | 出场 | 道具 |",
         "|---|---|---|---|---|---|"]
    for p in packs:
        L.append(f"| {p['no']:02d} | SHOT-{p['shots'][0]['no']:03d}~{p['shots'][-1]['no']:03d}"
                 f"（{len(p['shots'])} 镜） | {p['total']:.1f}s | {'、'.join(p['locs'])} "
                 f"| {'、'.join(p['chars'])} | {'、'.join(p['props']) or '—'} |")
    L.append("")
    for p in packs:
        seg_no, seg_name = p["seg"]
        L.append(f"## 生成包 {p['no']:02d} · SEG-{seg_no:02d} {seg_name}"
                 f"（SHOT-{p['shots'][0]['no']:03d}~{p['shots'][-1]['no']:03d}）\n")
        L.append("```text")
        people = [f"@{c} @{c}音色" if c in p["speakers"] else f"@{c}" for c in p["chars"]]
        L.append("【出场人物】" + "、".join(people))
        L.append("【场景】" + "、".join(f"@{x}" for x in p["locs"]))
        L.append("【道具】" + ("、".join(f"@{x}" for x in p["props"]) if p["props"] else "无"))
        L.append(f"【本节风格提示词】{STYLE_HEAD}；{p['tone']}；{BAN}")
        if p["no"] == 1:
            L.append(f"【跨节接镜】开场首帧（本包为全片第一包，无上一节）；"
                     f"首镜＝{p['first_beat'] or '见镜头1'}；末镜＝{p['last_beat'] or '见末镜'}，移交下一节")
        else:
            prev = packs[p["no"] - 2]
            tail = "移交下一节" if p["no"] < len(packs) else "本节为全片最后一包，无下一节"
            L.append(f"【跨节接镜】上一节末镜＝{prev['last_beat'] or '见上一包末镜'}；"
                     f"本节首镜＝{p['first_beat'] or '见镜头1'}；"
                     f"末镜＝{p['last_beat'] or '见末镜'}，{tail}")
        L.append(f"【包时长】{p['total']:.1f}s（{len(p['shots'])} 镜，切点由剪辑落刀）"
                 f"　【全集绝对时间】{p['abs_start']:.1f}–{p['abs_end']:.1f}s")
        L.append("")
        for k, s in enumerate(p["shots"], 1):
            rel_s = round(s["start"] - p["abs_start"], 2)
            rel_e = round(s["end"] - p["abs_start"], 2)
            L.append(f"镜头{k} / SHOT-{s['no']:03d}（{rel_s:.1f}-{rel_e:.1f}秒）："
                     f"{s['loc_cf']}｜{seg_name}｜{blocks_tone(s)}")
            L.extend(norm_names(ln) for ln in BLOCKS[s["no"]]["body"])
        L.append("```\n")
    return "\n".join(L)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    shots = parse_shots()
    BLOCKS = parse_blocks()
    sheet = parse_sheet()
    assert len(shots) == 46, f"分镜镜头数异常：{len(shots)}"
    assert len(BLOCKS) == 46, f"容器镜头块数异常：{len(BLOCKS)}"

    packs, unknown = build(shots, BLOCKS, sheet)

    print(f"{'包':>3} {'镜头':<16} {'时长':>6}  场景 / 出场 / 道具")
    for p in packs:
        rng = f"{p['shots'][0]['no']:03d}-{p['shots'][-1]['no']:03d}"
        print(f"{p['no']:>3} SHOT-{rng:<11} {p['total']:>5.1f}s  {'、'.join(p['locs'])}"
              f" / {'、'.join(p['chars'])} / {'、'.join(p['props']) or '—'}")
    print(f"\n合计 {len(packs)} 包 / {sum(len(p['shots']) for p in packs)} 镜 / "
          f"{round(sum(p['total'] for p in packs), 2)}s　"
          f"最长 {max(p['total'] for p in packs):.1f}s　最短 {min(p['total'] for p in packs):.1f}s")

    # 体检
    assert all(p["total"] <= MAX_SEC + 1e-9 for p in packs), "存在超 15s 的包"
    seq = [s["no"] for p in packs for s in p["shots"]]
    assert seq == list(range(1, 47)), "镜头有丢失或重复"
    print("✓ 全部 ≤15s，46 镜无丢失无重复，时长合计", round(sum(p['total'] for p in packs), 2))
    # @ 名字里带空格会导致 @ 只吃到空格前那一段，挂不上芯片
    bad_at = sorted({n for p in packs for n in p["chars"] + p["props"] + p["locs"] if re.search(r"\s", n)})
    if bad_at:
        print("\n⚠ 资产名里含空格，@ 会被截断（建议在视觉设定里去掉空格）：", bad_at)

    if unknown:
        print("\n⚠ 视觉依据里引用了视觉设定中不存在的资产（无法 @ 引用）：")
        for no, cat, name in sorted(set(unknown)):
            print(f"   SHOT-{no:03d} {cat}「{name}」")

    if args.write:
        OUT.write_text(render(packs), encoding="utf-8")
        print(f"\n已写入 {OUT}")
