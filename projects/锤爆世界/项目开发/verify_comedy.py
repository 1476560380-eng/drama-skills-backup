#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验并修正搞笑版分镜：时间码连续性、SEG 小计、生成包总表、头部合计。
用法：python3 项目开发/verify_comedy.py EP003

只改「算错的地方」，不改任何画面/台词文字。
"""
import re
import sys
import pathlib

ep = sys.argv[1]
root = pathlib.Path(__file__).resolve().parent.parent
p = root / "剧集" / ep / "分镜-搞笑夸张版.md"
t = p.read_text(encoding="utf-8")

# 逐镜时长
durs = {}
for m in re.finditer(r"## (SHOT-%s-\d{3}) · [^\n]*\n\n- \*\*职责\*\*.*?- \*\*时长\*\*：([\d.]+)s" % ep, t, re.S):
    durs[m.group(1)] = float(m.group(2))
ids = sorted(durs)
if not ids:
    sys.exit("没解析到镜头")

# 时间码连续重排
acc = 0.0
fixed_time = 0
for sid in ids:
    a, b = round(acc, 1), round(acc + durs[sid], 1)
    pat = re.compile(r"(## " + sid + r" · [^\n]*?)（[\d.]+[–\-][\d.]+s）")
    new, n = pat.subn(lambda m: m.group(1) + f"（{a:.1f}–{b:.1f}s）", t)
    if n and new != t:
        fixed_time += 1
    t = new
    acc = b
total = acc

# SEG 小计（按段头的成员范围，短写 SHOT-001~010 或长写）
def seg_fix(m):
    head, lo, hi = m.group(1), m.group(2), m.group(3)
    keys = [k for k in ids if lo <= k[-3:] <= hi]
    s = sum(durs[k] for k in keys)
    return f"{head}{lo}~{hi} · {s:.1f}s）"

t = re.sub(r"(## SEG-0\d[^\n]*（SHOT-)(\d{3})~(\d{3}) · [\d.]+s）", seg_fix, t)

# 生成包总表：贪心 ≤15s，且不跨 SEG
seg_of = {}
for m in re.finditer(r"## SEG-0\d[^\n]*（SHOT-(\d{3})~(\d{3}) · [\d.]+s）", t):
    for k in ids:
        if m.group(1) <= k[-3:] <= m.group(2):
            seg_of[k] = m.group(0)[3:9]
pkgs, cur, csum, curseg = [], [], 0.0, None
for sid in ids:
    d, s = durs[sid], seg_of.get(sid)
    if cur and (csum + d > 15.0 or s != curseg):
        pkgs.append((cur, round(csum, 1)))
        cur, csum = [sid], d
    else:
        cur.append(sid)
        csum += d
    curseg = s
if cur:
    pkgs.append((cur, round(csum, 1)))

# 尾包不足 4s 时，从上一包借一镜过来（借完前一包仍需 ≥4s）
MIN_PKG = 4.0
if len(pkgs) > 1 and pkgs[-1][1] < MIN_PKG:
    prev_mem, _ = pkgs[-2]
    moved = prev_mem.pop()
    pkgs[-2] = (prev_mem, round(sum(durs[k] for k in prev_mem), 1))
    pkgs[-1] = ([moved] + pkgs[-1][0], round(sum(durs[k] for k in [moved] + pkgs[-1][0]), 1))
    pkgs = [p for p in pkgs if p[0]]

rows = "| 包 | 成员镜 | 时长 | 包内内容 |\n|---|---|---|---|\n"
old_rows = {}
for m in re.finditer(r"^\| (\d+) \| (SHOT-[\d~]+) \| ([\d.]+)s \|(.*)\|$", t, re.M):
    old_rows[int(m.group(1))] = m.group(4).strip()
for i, (mem, s) in enumerate(pkgs, 1):
    rows += f"| {i} | SHOT-{mem[0][-3:]}~{mem[-1][-3:]} | {s:.1f}s | {old_rows.get(i, '')} |\n"
t = re.sub(r"\| 包 \| 成员镜 \| 时长 \| 包内内容 \|\n\|---\|---\|---\|---\|\n(?:\|[^\n]*\|\n)+", rows, t)

# 头部合计与镜数
t = re.sub(r"- 镜长合计 \*\*[\d.]+s\*\*（\d+ 镜", f"- 镜长合计 **{total:.1f}s**（{len(ids)} 镜", t)

p.write_text(t, encoding="utf-8")

# 校验输出
segs = re.findall(r"## (SEG-0\d[^\n]*)", t)
seg_sum = sum(float(re.search(r"· ([\d.]+)s）", s).group(1)) for s in segs)
print(f"{ep}: {len(ids)} 镜 | 逐镜合计 {total:.1f}s | SEG 相加 {seg_sum:.1f}s | 时间码重排 {fixed_time} 处")
for s in segs:
    print("   ", s)
over = [s for _, s in pkgs if s > 15.0]
print(f"生成包 {len(pkgs)} 个，超 15s：{over or '无'}，最小时长 {min(s for _, s in pkgs):.1f}s")
print("✅ 一致" if abs(total - seg_sum) < 0.05 else "❌ SEG 相加与合计不符")
