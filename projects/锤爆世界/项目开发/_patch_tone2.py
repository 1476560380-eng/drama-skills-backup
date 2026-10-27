import pathlib

p = pathlib.Path("项目开发/voice_cast.py")
s = p.read_text(encoding="utf-8")

s = s.replace('''def load_exceptions():
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
    return ex''',
'''def load_exceptions():
    """{('EP002','SHOT-EP002-014','搞','高铁锤'): ('真诚','理由')} 逐句覆盖默认语气。
    表列：集｜镜号｜版本｜角色｜语气｜理由；版本取 原/搞/两版。"""
    ex = {}
    if not EX_PATH.exists():
        return ex
    for line in EX_PATH.read_text(encoding="utf-8").split("\\n"):
        if not line.startswith("|"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 5 or not c[0].startswith("EP"):
            continue
        ep, sid, ver, who, tone = c[:5]
        ex[(ep, sid, ver, who)] = (tone, c[5] if len(c) > 5 else "")
    return ex''')

s = s.replace('''def voice_line(name, data, ep=None, sid=None, ex=None):
    """每镜【配音指令】里的括号锚点：编号｜音区·质感·气息｜语气｜音量。"""
    v = data.get(name)
    if not v:
        return name
    tone = v.get("tone", "真诚")
    if ex and ep and sid and (ep, sid) in ex and ex[(ep, sid)][0] == name:
        tone = ex[(ep, sid)][1]''',
'''def voice_line(name, data, ep=None, sid=None, ex=None, ver="原"):
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
                break''')
p.write_text(s, encoding="utf-8")

q = pathlib.Path("项目开发/gen_containers.py")
t = q.read_text(encoding="utf-8")
t = t.replace('''    EX = voice_cast.load_exceptions()''',
'''    EX = voice_cast.load_exceptions()
    VER = "搞" if "搞笑" in str(a.src or "") else "原"''')
t = t.replace('voice_cast.voice_line(nm, VD, a.ep, s["sid"], EX)',
              'voice_cast.voice_line(nm, VD, a.ep, s["sid"], EX, VER)')
q.write_text(t, encoding="utf-8")
print("例外表支持 版本+角色 双维度 ✅")
