import pathlib
import re

# ===== 1) voice_cast.py：读第 10 列「语气默认值」，并支持逐句例外 =====
p = pathlib.Path("项目开发/voice_cast.py")
s = p.read_text(encoding="utf-8")

s = s.replace('''        if len(parts) < 9:
            continue
        vo, name, rng, tex, breath, rate, mood, ban, vol = parts[:9]
        data[name] = dict(vo=vo, name=name, range=rng, texture=tex, breath=breath,
                          rate=rate, mood=mood, ban=ban, volume=vol, en="")''',
'''        if len(parts) < 9:
            continue
        vo, name, rng, tex, breath, rate, mood, ban, vol = parts[:9]
        tone = parts[9] if len(parts) > 9 else "真诚"
        data[name] = dict(vo=vo, name=name, range=rng, texture=tex, breath=breath,
                          rate=rate, mood=mood, ban=ban, volume=vol, tone=tone, en="")''')

s = s.replace('''def voice_line(name, data):
    """每镜【配音指令】里的括号锚点。"""
    v = data.get(name)
    if not v:
        return name
    return f"{name}（{v['vo']}｜{v['range']}·{v['texture']}·气息{v['breath']}｜音量{v['volume']}）"''',
'''EX_PATH = ROOT / "设定集" / "语气例外.md"


def load_exceptions():
    """{('EP002','SHOT-EP002-014'): ('高铁锤','真诚','理由')} 逐句覆盖默认语气。"""
    ex = {}
    if not EX_PATH.exists():
        return ex
    for line in EX_PATH.read_text(encoding="utf-8").split("\\n"):
        if not line.startswith("|"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 4 or not c[0].startswith("EP"):
            continue
        ex[(c[0], c[1])] = (c[2], c[3], c[4] if len(c) > 4 else "")
    return ex


def voice_line(name, data, ep=None, sid=None, ex=None):
    """每镜【配音指令】里的括号锚点：编号｜音区·质感·气息｜语气｜音量。"""
    v = data.get(name)
    if not v:
        return name
    tone = v.get("tone", "真诚")
    if ex and ep and sid and (ep, sid) in ex and ex[(ep, sid)][0] == name:
        tone = ex[(ep, sid)][1]
    return f"{name}（{v['vo']}｜{v['range']}·{v['texture']}·气息{v['breath']}｜{tone}｜音量{v['volume']}）"''')

s = s.replace('''    rows = ["| 编号 | 角色 | 音区 | 音色质感 | 气息 | 语速 | 情绪底色 | 音量档 | 禁令（不能出现什么） |",
            "|---|---|---|---|---|---|---|---|---|"]''',
'''    rows = ["| 编号 | 角色 | 音区 | 音色质感 | 气息 | 语速 | 情绪底色 | 语气默认 | 音量档 | 禁令（不能出现什么） |",
            "|---|---|---|---|---|---|---|---|---|---|"]''')
s = s.replace('''        rows.append(f"| {v['vo']} | {n} | {v['range']} | {v['texture']} | {v['breath']} | "
                    f"{v['rate']} 字/秒 | {v['mood']} | {v['volume']} | {v['ban']} |")''',
'''        rows.append(f"| {v['vo']} | {n} | {v['range']} | {v['texture']} | {v['breath']} | "
                    f"{v['rate']} 字/秒 | {v['mood']} | {v.get('tone','真诚')} | {v['volume']} | {v['ban']} |")''')
p.write_text(s, encoding="utf-8")
print("voice_cast.py 已支持语气 ✅")

# ===== 2) gen_containers.py：把 ep/sid 和例外表传进 voice_line =====
q = pathlib.Path("项目开发/gen_containers.py")
t = q.read_text(encoding="utf-8")
t = t.replace('''                    if nm in VD:
                        out.append(voice_cast.voice_line(nm, VD))''',
'''                    if nm in VD:
                        out.append(voice_cast.voice_line(nm, VD, a.ep, s["sid"], EX))''')
t = t.replace('''    VD = voice_cast.load()
    ep_voices = voice_cast.episode_voices(fan, VD)''',
'''    VD = voice_cast.load()
    EX = voice_cast.load_exceptions()
    ep_voices = voice_cast.episode_voices(fan, VD)''')
t = t.replace('''        lines.append("> 每镜【台词】里的括号＝该镜的音色锚点（编号｜音区·质感·气息｜音量档）；禁令只在这张表里，不逐镜重复。''',
'''        lines.append("> 每镜【台词】里的括号＝该镜的音色锚点（编号｜音区·质感·气息｜语气｜音量档）；语气四值：真诚／装的／压着／随口，逐句例外见 `设定集/语气例外.md`；禁令只在这张表里，不逐镜重复。''')
q.write_text(t, encoding="utf-8")
print("gen_containers.py 已接入语气 + 例外 ✅")
