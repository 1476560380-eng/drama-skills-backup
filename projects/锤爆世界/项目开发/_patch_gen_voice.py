import pathlib
import re

p = pathlib.Path("项目开发/gen_containers.py")
t = p.read_text(encoding="utf-8")

# 1) 导入音色模块
if "import voice_cast" not in t:
    t = t.replace("BAN = ", "import sys\nsys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))\nimport voice_cast\n\nBAN = ", 1)

# 2) 顶部：在分包总表后插入音色总表
old = '''    lines.append("")

    for num, rng, dur, _, lo, hi in pkg_table:
        members = [shot_by_tail[str(i)] for i in range(int(lo), int(hi) + 1) if str(i) in shot_by_tail]
        seg_id = members[0]["seg"]'''
new = '''    lines.append("")

    # ===== 音色总表（本集真正开口的常驻角色）=====
    VD = voice_cast.load()
    ep_voices = voice_cast.episode_voices(fan, VD)
    if ep_voices:
        lines.append("## 配音音色总表（本集出场 %d 人）" % len(ep_voices))
        lines.append("")
        lines.append(voice_cast.header_table(ep_voices, VD))
        lines.append("")
        lines.append("> 这张表是**核对标尺**，不是中文 TTS 的控制参数。中文 TTS（火山、MiniMax）不认文字描述，"
                     "必须先用末尾「英文音色 prompt」在 Voice Design 里生成音色、导出参考音，再拿参考音克隆。")
        lines.append("> 每镜【台词】里的括号＝该镜的音色锚点（编号｜音区·质感·气息｜音量档），禁令只在这张表里，不逐镜重复。")
        lines.append("")

    for num, rng, dur, _, lo, hi in pkg_table:
        members = [shot_by_tail[str(i)] for i in range(int(lo), int(hi) + 1) if str(i) in shot_by_tail]
        seg_id = members[0]["seg"]'''
assert old in t
t = t.replace(old, new, 1)

# 3) 每镜台词：角色名 → 带括号锚点
old2 = '''            vo = field(b, "配音指令")
            lines.append(f"【台词】{vo or '无'}")'''
new2 = '''            vo = field(b, "配音指令") or ""
            for nm in VD:
                if re.search(r"(?:^|[；；\\s])" + re.escape(nm) + r"(?:｜|\\s*（)", vo):
                    vo = re.sub(r"(?<![\\u4e00-\\u9fa5])" + re.escape(nm) + r"(?=（VO-)", nm, vo)
                    vo = re.sub(r"(?:^|(?<=[；；\\s]))" + re.escape(nm) + r"(?:｜|\\s*（VO-\\d+｜[^）]*）)",
                                voice_cast.voice_line(nm, VD) + "｜", vo)
            lines.append(f"【台词】{vo or '无'}")'''
assert old2 in t
t = t.replace(old2, new2, 1)

# 4) 末尾追加英文音色段
old3 = '''    out = "\\n".join(lines) + "\\n"'''
new3 = '''    if ep_voices:
        lines.append("---")
        lines.append("")
        lines.append(voice_cast.english_section(ep_voices, VD))
        lines.append("")

    out = "\\n".join(lines) + "\\n"'''
assert old3 in t
t = t.replace(old3, new3, 1)

p.write_text(t, encoding="utf-8")
print("gen_containers.py 已注入音色支持 ✅")
