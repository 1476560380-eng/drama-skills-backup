#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 设定集/音色设计提示词.md 读音色数据，供 gen_containers.py 注入容器。

对外两个函数：
  load()          -> {角色名: dict(vo, name, range, texture, breath, rate, mood, ban, volume, en)}
  episode_voices(fan_text, data) -> 本集出场角色名列表（按台词首次出现顺序）
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "设定集" / "音色设计提示词.md"


def load():
    t = SRC.read_text(encoding="utf-8")
    # 1) 机读表
    m = re.search(r"## 六、机读表.*?```text\n(.*?)```", t, re.S)
    data = {}
    if not m:
        return data
    for line in m.group(1).strip().split("\n"):
        parts = [x.strip() for x in line.strip().split("|")]
        if len(parts) < 9:
            continue
        vo, name, rng, tex, breath, rate, mood, ban, vol = parts[:9]
        tone = parts[9] if len(parts) > 9 else "真诚"
        data[name] = dict(vo=vo, name=name, range=rng, texture=tex, breath=breath,
                          rate=rate, mood=mood, ban=ban, volume=vol, tone=tone, en="")
    # 2) 英文 prompt：从各角色小节里抓
    for sec in re.split(r"\n### ", t)[1:]:
        nm = re.match(r"\d+\.\s*([^（(]+)", sec)
        if not nm:
            continue
        name = nm.group(1).strip()
        em = re.search(r"\*\*English prompt\*\*\s*\n>\s*(.+?)(?:\n\n|\n\*\*)", sec, re.S)
        if name in data and em:
            data[name]["en"] = " ".join(x.strip("> ").strip() for x in em.group(1).split("\n")).strip()
    return data


def episode_voices(fan_text, data):
    """按台词首次出现顺序，返回本集真正开口的常驻角色。"""
    seen = []
    for mm in re.finditer(r"\*\*配音指令\*\*：(.+)", fan_text):
        line = mm.group(1)
        for name in data:
            if name not in seen and re.search(r"(?:^|[；；\s])" + re.escape(name) + r"(?:｜|\s*（)", line):
                seen.append(name)
    return seen


EX_PATH = ROOT / "设定集" / "语气例外.md"


def load_exceptions():
    """{('EP002','SHOT-EP002-014','搞','高铁锤'): ('真诚','理由')} 逐句覆盖默认语气。
    表列：集｜镜号｜版本｜角色｜语气｜理由；版本取 原/搞/两版。"""
    ex = {}
    if not EX_PATH.exists():
        return ex
    for line in EX_PATH.read_text(encoding="utf-8").split("\n"):
        if not line.startswith("|"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 5 or not c[0].startswith("EP"):
            continue
        ep, sid, ver, who, tone = c[:5]
        ex[(ep, sid, ver, who)] = (tone, c[5] if len(c) > 5 else "")
    return ex


def voice_line(name, data, ep=None, sid=None, ex=None, ver="原"):
    """每镜【配音指令】里的括号锚点：编号｜音区·质感·气息｜语气｜音量。"""
    v = data.get(name)
    if not v:
        return name
    tone = v.get("tone", "真诚")
    if ex and ep and sid:
        for vk in (ver, "两版"):
            hit = ex.get((ep, sid, vk, name))
            if hit:
                tone = hit[0]
                break
    return f"{name}（{v['vo']}｜{v['range']}·{v['texture']}·气息{v['breath']}｜{tone}｜音量{v['volume']}）"


def header_table(names, data):
    rows = ["| 编号 | 角色 | 音区 | 音色质感 | 气息 | 语速 | 情绪底色 | 语气默认 | 音量档 | 禁令（不能出现什么） |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for n in names:
        v = data[n]
        rows.append(f"| {v['vo']} | {n} | {v['range']} | {v['texture']} | {v['breath']} | "
                    f"{v['rate']} 字/秒 | {v['mood']} | {v.get('tone','真诚')} | {v['volume']} | {v['ban']} |")
    return "\n".join(rows)


def english_section(names, data):
    out = ["## 附：英文音色 prompt（只给配音工具用，不是画面输入）", ""]
    out.append("> 用法：整段贴进 ElevenLabs Voice Design 这类只吃英文的工具，生成后导出参考音；"
               "中文 TTS（火山、MiniMax）不认文字描述，必须用参考音克隆。")
    out.append("")
    for n in names:
        v = data[n]
        out.append(f"### {v['vo']} {n}（{v['range']}｜{v['rate']} 字/秒｜音量{v['volume']}）")
        out.append("")
        out.append("> " + (v["en"] or "（英文 prompt 缺失，去 设定集/音色设计提示词.md 补）"))
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    d = load()
    print(f"读出 {len(d)} 个音色：")
    for k, v in d.items():
        print(f"  {v['vo']} {k}｜{v['range']}｜{v['rate']}｜音量{v['volume']}｜英文 {len(v['en'])} 字符")
