import pathlib

q = pathlib.Path("项目开发/gen_containers.py")
s = q.read_text(encoding="utf-8")

start = s.index('        lines.append(f"## 生成包 {num:02d}')
end = s.index('        lines.append("```")', start)
end2 = s.index("\n", end) + 1

new = '''        lines.append(f"## 生成包 {num:02d} · {seg_id} {seg_title}（SHOT-{lo}~{hi}）")
        lines.append("")
        prev = "本包为全片第一包，无上一节" if num == 1 else f"上一包尾帧＝SHOT-{int(lo)-1:03d} 终点，首镜＝{members[0]['title']}"
        nxt = f"末镜＝{members[-1]['title']}，移交下一节" if num < len(pkg_table) else "末镜＝本集最后一格，交给下一集开场"
        lines.append("| 包级信息 | 内容 |")
        lines.append("|---|---|")
        lines.append(f"| 出场人物 | {'、'.join('@' + x for x in ch) or '无'} |")
        lines.append(f"| 场景 | {'、'.join('@' + x for x in lc) or '无'} |")
        lines.append(f"| 道具 | {'、'.join('@' + x for x in dp) or '无'} |")
        lines.append(f"| 包时长 | {t2 - t1:.1f}s（{len(members)} 镜，切点由剪辑落刀） |")
        lines.append(f"| 全集绝对时间 | {t1:.1f}–{t2:.1f}s |")
        lines.append(f"| 跨节接镜 | {prev}；{nxt} |")
        lines.append("")
        lines.append("**本节风格提示词**（含禁止项，可直接复制）")
        lines.append("")
        lines.append("```text")
        lines.append(f"{STYLE_HEAD}；{color}；{BAN}")
        lines.append("```")
        lines.append("")
        for i, s_ in enumerate(members, 1):
            b = s_["block"]
            shot_loc = loc_of(assets_of(b))
            if shot_loc.startswith("（见分镜"): shot_loc = "、".join(lc) or shot_loc
            lines.append(f"### 镜头 {i} · {s_['sid']} · {s_['t1']:.1f}–{s_['t2']:.1f} 秒")
            lines.append("")
            lines.append(f"> 场景：{shot_loc}　｜　段：{seg_title}　｜　色调：{color}")
            lines.append("")
            lines.append("- **时间标识**：无")
            kf = keyframe_of(b)
            if kf:
                lines.append(f"- **首帧锁定**：{kf}")
            jm = (field(b, '景别/机位') or '').rstrip('。')
            lines.append(f"- **运镜**：{jm}。{field(b, '运镜') or ''}")
            lines.append(f"- **画面**：{field(b, '起点 → 唯一动作 → 终点') or ''}")
            lines.append(f"- **镜头技术**：{field(b, '镜头技术捕捉') or ''}")
            lines.append(f"- **动作/情绪**：本镜职责：{field(b, '职责') or ''}（动作链见【画面】）")
            pos = re.findall(r"(on screen-\\w+|facing screen-\\w+|axis resets|not part of the dialogue axis)",
                             "\\n".join(re.findall(r"^> (.+)$", b, re.M)))
            lines.append(f"- **位置承接**：{'；'.join(dict.fromkeys(pos)) or '本镜无人物位置句（空镜/纯物件）'}")
            snd = field(b, "声音") or ""
            os_n = len(re.findall(r"\\[OS\\]", snd))
            lines.append(f"- **OS**：{'×' + str(os_n) + '（内容见【台词】）' if os_n else '无'}")
            lines.append("- **画外音**：无")
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
'''

s = s[:start] + new + s[end2:]
q.write_text(s, encoding="utf-8")
import py_compile
py_compile.compile(str(q), doraise=True)
print("排版改完 ✅")
