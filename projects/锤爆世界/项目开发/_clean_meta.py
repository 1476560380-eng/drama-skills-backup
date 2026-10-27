import pathlib
import re

# ============ 1) 把分镜里的「元说明」改成纯描述（只动 职责 一种字段）============
SUBS = [
    ("本版新增的笑点——", "笑点——"),
    ("本版新增笑点——", "笑点——"),
    ("本版的笑点核心——", "笑点核心——"),
    ("本版的破局笑点——", "破局笑点——"),
    ("本版对白核心——", "对白核心——"),
    ("本版最好笑的一镜——", "全段最强笑点——"),
    ("本版加的反差——", "反差笑点——"),
    ("本版新增——", ""),
    ("本版把", "把"),
    ("本版加一个", "附带"),
    ("本版给自己配", "他给自己配"),
    ("本版「", "「"),
    ("（呼应 EP001）", ""),
    ("（呼应上集）", ""),
]

for e in ["EP001", "EP002", "EP003", "EP004", "EP005"]:
    p = pathlib.Path(f"剧集/{e}/分镜-搞笑夸张版.md")
    t = p.read_text(encoding="utf-8")
    out = []
    changed = 0
    for line in t.split("\n"):
        if line.startswith("- **职责**："):
            new = line
            for a, b in SUBS:
                if a in new:
                    new = new.replace(a, b)
                    changed += 1
            # 「把「X」拍成「Y」」开头读起来不顺，改成「这一镜把…」
            new = re.sub(r"^- \*\*职责\*\*：把「", "- **职责**：这一镜把「", new)
            # 兜底：职责里不能再出现「版」这类元词
            new = new.replace("本版", "此镜").replace("原版", "").replace("正式版", "")
            out.append(new)
        else:
            out.append(line)
    p.write_text("\n".join(out), encoding="utf-8")
    print(f"{e}：改写 {changed} 处")

# ============ 2) 生成器加安全网：字段进容器前剥掉元话语，并报告残留 ============
q = pathlib.Path("项目开发/gen_containers.py")
s = q.read_text(encoding="utf-8")
if "def strip_meta" not in s:
    s = s.replace("def main():", '''META_PAT = re.compile(r"(本版|原版|正式版|呼应 ?EP\\d+|相对原版|这一版)")


def strip_meta(v):
    """把元说明从要进容器的字段里剥掉，避免模型把「解释原版」读成指令。"""
    if not v:
        return v
    v = re.sub(r"（[^）]*(?:本版|原版|正式版|呼应 ?EP\\d+)[^）]*）", "", v)
    v = re.sub(r"[；，]?(?:本版新增的笑点|本版的笑点核心|本版)[－—-]?", "", v)
    return v.strip()


def warn_meta(tag, v):
    if v and META_PAT.search(v):
        print(f"   ⚠️ 字段里仍有元话语（{tag}）：{v[:40]}…")


def main():''', 1)
    s = s.replace('''            lines.append(f"- **动作/情绪**：本镜职责：{field(b, '职责') or ''}（动作链见【画面】）")''',
                  '''            _zz = strip_meta(field(b, '职责') or '')
            warn_meta(s['sid'] + ' 职责', _zz)
            lines.append(f"- **动作/情绪**：本镜职责：{_zz}（动作链见【画面】）")''')
    s = s.replace('''            lines.append(f"- **画面**：{field(b, '起点 → 唯一动作 → 终点') or ''}")''',
                  '''            _pm = strip_meta(field(b, '起点 → 唯一动作 → 终点') or '')
            warn_meta(s['sid'] + ' 画面', _pm)
            lines.append(f"- **画面**：{_pm}")''')
    s = s.replace('''            lines.append(f"- **镜头技术**：{field(b, '镜头技术捕捉') or ''}")''',
                  '''            _js = strip_meta(field(b, '镜头技术捕捉') or '')
            warn_meta(s['sid'] + ' 镜头技术', _js)
            lines.append(f"- **镜头技术**：{_js}")''')
    # 表头「源」按真实来源显示
    s = s.replace('''    lines.append(f"> 由 `项目开发/gen_containers.py` 生成；源：`剧集/{a.ep}/分镜.md` + `视觉设定.md`。")''',
                  '''    _src = pathlib.Path(a.src).name if a.src else "分镜.md"
    lines.append(f"> 由 `项目开发/gen_containers.py` 生成；源：`剧集/{a.ep}/{_src}` + `视觉设定.md`。")''')
    q.write_text(s, encoding="utf-8")
    import py_compile
    py_compile.compile(str(q), doraise=True)
    print("生成器：已加 strip_meta 安全网 + 源头文件名修正 ✅")
else:
    print("安全网已存在")
