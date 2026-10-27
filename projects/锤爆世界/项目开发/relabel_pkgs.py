import re
import sys
import pathlib

ep = sys.argv[1]
root = pathlib.Path(__file__).resolve().parent.parent
p = root / "剧集" / ep / "分镜-搞笑夸张版.md"
t = p.read_text(encoding="utf-8")

title = {m.group(1): m.group(2).strip() for m in re.finditer(r"## (SHOT-%s-\d{3}) · ([^（\n]+)" % ep, t)}
rows = re.findall(r"^\| (\d+) \| SHOT-(\d{3})~(\d{3}) \| ([\d.]+)s \|", t, re.M)
new = "| 包 | 成员镜 | 时长 | 包内内容 |\n|---|---|---|---|\n"
for n, lo, hi, dur in rows:
    names = [title.get(f"SHOT-{ep}-{i:03d}", "") for i in range(int(lo), int(hi) + 1)]
    new += f"| {n} | SHOT-{lo}~{hi} | {dur}s | {'、'.join(names)} |\n"
t = re.sub(r"\| 包 \| 成员镜 \| 时长 \| 包内内容 \|\n\|---\|---\|---\|---\|\n(?:\|[^\n]*\|\n)+", new, t)
p.write_text(t, encoding="utf-8")
print(new)
