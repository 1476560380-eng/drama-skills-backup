#!/usr/bin/env python3
"""零丢字比对：创作者原文 vs 规范化后的 剧本.md。

把「保留原文，只做格式规范化」变成可验证的事，而不是靠肉眼。
比对时剥掉剧本里的集标题、场景头、生产标签前缀、对白行首的 `角色（提示）：`，
剩下的每个实字都必须能在原文里按同样顺序找到。

用法：
    python3 normalize_check.py 输入/original-script.md 剧集/EP001/剧本.md
    python3 normalize_check.py 原文.md 剧本.md --speakers 洛洛 小药
    python3 normalize_check.py 原文.md 剧本.md --drop-first-line   # 原文首行是集名标题

判据：
- 只有「标点换成另一种标点」算可接受差异（冒号断成句号这类）。
- 任何实字增删、换字、顺序变化都算硬差异，退出码 1。
- 对白括号里的表演提示若原文没有，会作为硬差异报出来——这正是
  「同一个动作既写动作段又写进对白括号」的检查方式。

退出码：0 零丢字（仅标点差异）/ 1 有实字差异 / 2 用法错误
"""
from __future__ import annotations

import argparse
import re
import sys
from difflib import SequenceMatcher

PUNCT = set('，。！？、；：…—·「」『』“”‘’（）()《》〈〉【】,.!?;:-–~～')
TAG_RE = re.compile(r'^\[[^\]]{1,10}\]\s*')
SPEAKER_RE = re.compile(r'^([^\s：（）]{1,8})(（[^）]*）)?：')


def read(path: str) -> str:
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def detect_speakers(text: str) -> list[str]:
    """冒出 ≥2 次的冒号前缀才当说话者，避免把「第二格：…」这类动作误剥。"""
    counts: dict[str, int] = {}
    for line in text.splitlines():
        m = SPEAKER_RE.match(line.strip())
        if m:
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return [name for name, n in counts.items() if n >= 2]


def screenplay_body(text: str, speakers: list[str]) -> str:
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        s = TAG_RE.sub('', s)
        m = SPEAKER_RE.match(s)
        if m and m.group(1) in speakers:
            s = s[m.end():]
        out.append(s)
    return '\n'.join(out)


def plain(text: str) -> str:
    return re.sub(r'[\s"“”\'‘’「」『』]', '', text)


def main() -> int:
    ap = argparse.ArgumentParser(description='原文 vs 规范化剧本的零丢字比对')
    ap.add_argument('original', help='创作者原文（规范化的唯一依据）')
    ap.add_argument('screenplay', help='规范化后的 剧本.md')
    ap.add_argument('--speakers', nargs='*', default=None,
                    help='本集说话者；省略时自动取出现≥2次的冒号前缀')
    ap.add_argument('--drop-first-line', action='store_true',
                    help='原文首行是集名标题（剧本里已写成 # 集名）时丢掉它')
    args = ap.parse_args()

    try:
        original = read(args.original)
        screenplay = read(args.screenplay)
    except OSError as exc:
        print(f'读文件失败：{exc}', file=sys.stderr)
        return 2

    if args.drop_first_line and '\n' in original:
        original = original.split('\n', 1)[1]

    speakers = args.speakers if args.speakers is not None else detect_speakers(screenplay)
    n_orig = plain(original)
    n_scr = plain(screenplay_body(screenplay, speakers))

    ops = [op for op in SequenceMatcher(None, n_orig, n_scr).get_opcodes() if op[0] != 'equal']
    hard: list[str] = []
    soft: list[str] = []
    for tag, i1, i2, j1, j2 in ops:
        a, b = n_orig[i1:i2], n_scr[j1:j2]
        item = f'{tag}: 原文「{a}」→ 剧本「{b}」'
        if set(a) <= PUNCT and set(b) <= PUNCT:
            soft.append(item)
        else:
            hard.append(item)

    print(f'原文净字数 {len(n_orig)} / 剧本净字数 {len(n_scr)} / 说话者：{"、".join(speakers) or "未识别"}')
    print(f'标点断句差异 {len(soft)} 处（可接受） / 实字差异 {len(hard)} 处')
    for line in hard:
        print(f'  ✗ {line}')
    for line in soft:
        print(f'  · {line}')

    if hard:
        print('\n有实字增删：先判定是「原文被改写」还是「规范化漏字/重复」，改完重跑。')
        return 1
    print('\n✅ 零丢字：只存在标点断句差异。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
