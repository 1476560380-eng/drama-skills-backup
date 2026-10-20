#!/usr/bin/env python3
"""短剧题材热度探针：抓公开热榜，统计题材赛道命中数。

用法：
    python3 heat_probe.py                     # 打印 JSON 到 stdout
    python3 heat_probe.py --out heat.json     # 同时落盘

数据源（全部免费、无需登录、2026-10 实测可用）：
    - 百度热搜 realtime
    - 今日头条热榜
    - B站热搜
    - 豆瓣热门剧集（在播剧，短剧常在此露头）

注意：这些是「话题热度」证据，不是平台播放量。热度结论只能来自
本脚本输出 + 创作者提供的平台数据；缺失就写「未提供热度数据」，不得编造。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

H = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

# 短剧常见赛道 → 关键词。命中数越高，说明该赛道在公开热榜里越活跃。
GENRES = {
    "逆袭": ["逆袭", "翻身", "小人物", "草根"],
    "复仇": ["复仇", "报仇", "清算", "打脸"],
    "甜宠": ["甜宠", "甜妻", "撩", "宠溺", "闪婚"],
    "赘婿": ["赘婿", "上门女婿", "女婿"],
    "重生": ["重生", "回到", "再来一次", "重活"],
    "穿越": ["穿越", "古今", "异世"],
    "豪门": ["豪门", "总裁", "首富", "继承", "千金"],
    "宫斗": ["宫斗", "嫡女", "侧妃", "皇后", "后宫"],
    "悬疑": ["悬疑", "推理", "谜案", "真相", "凶手"],
    "末世": ["末世", "丧尸", "废土", "灾难", "末日"],
    "玄幻": ["玄幻", "修仙", "神尊", "灵根", "仙门"],
    "战神": ["战神", "龙王", "兵王", "神级", "至尊"],
    "神医": ["神医", "医圣", "医术", "药王"],
    "校园": ["校园", "校花", "高考", "青春"],
    "职场": ["职场", "打工人", "老板", "创业"],
    "婆媳家庭": ["婆媳", "婚姻", "离婚", "家庭", "带娃"],
}


def _get(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def baidu() -> list[str]:
    raw = _get("https://top.baidu.com/api/board?platform=wise&tab=realtime")
    data = json.loads(raw)
    out: list[str] = []
    for card in data.get("data", {}).get("cards", []):
        # 结构为 cards[].content[].content[] 嵌套两层，内层才是词条
        for group in card.get("content", []) or []:
            items = group.get("content", []) if isinstance(group, dict) else None
            if isinstance(items, list):
                out += [str(i["word"]) for i in items if isinstance(i, dict) and i.get("word")]
            elif isinstance(group, dict) and group.get("word"):
                out.append(str(group["word"]))
    return out


def toutiao() -> list[str]:
    raw = _get("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc")
    data = json.loads(raw)
    return [str(x.get("Title", "")) for x in data.get("data", []) if x.get("Title")]


def bilibili() -> list[str]:
    raw = _get("https://api.bilibili.com/x/web-interface/search/square?limit=50")
    data = json.loads(raw)
    items = data.get("data", {}).get("trending", {}).get("list", []) or []
    return [str(x.get("keyword", "")) for x in items if x.get("keyword")]


def douban_tv() -> list[dict]:
    raw = _get("https://movie.douban.com/j/search_subjects?type=tv&tag=%E7%83%AD%E9%97%A8&page_limit=30")
    data = json.loads(raw)
    return [
        {"title": s.get("title"), "rate": s.get("rate"), "episodes": s.get("episodes_info")}
        for s in data.get("subjects", [])
    ]


def fanqie() -> list[dict]:
    """番茄小说榜单（网页端公开接口，单次 7 本，含简介——题材信号最准）。"""
    raw = _get("https://fanqienovel.com/api/rank/list?category_id=0&rank_type=1")
    data = json.loads(raw)
    return [
        {"书名": b.get("bookName"), "作者": b.get("author"), "简介": (b.get("abstract") or "")[:80]}
        for b in data.get("data", {}).get("list", []) or []
    ]


def genre_scores(titles: list[str]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for genre, kws in GENRES.items():
        n = 0
        for t in titles:
            if any(k in t for k in kws):
                n += 1
        if n:
            scores[genre] = n
    return dict(sorted(scores.items(), key=lambda kv: -kv[1]))


def main() -> int:
    ap = argparse.ArgumentParser(description="短剧题材热度探针（公开热榜）")
    ap.add_argument("--out", help="结果写入 JSON 文件")
    ap.add_argument("--quiet", action="store_true", help="只输出汇总，不输出原始条目")
    args = ap.parse_args()

    sources: dict[str, object] = {}
    titles: list[str] = []
    status: dict[str, str] = {}

    for name, fn in (("baidu", baidu), ("toutiao", toutiao), ("bilibili", bilibili)):
        try:
            got = fn()
            status[name] = f"ok ({len(got)})"
            titles += got
            if not args.quiet:
                sources[name] = got
        except Exception as exc:  # 网络/接口变动都记成不可用，不阻断
            status[name] = f"failed: {type(exc).__name__}: {exc}"

    tv: list[dict] = []
    try:
        tv = douban_tv()
        status["douban_tv"] = f"ok ({len(tv)})"
        titles += [str(x["title"]) for x in tv if x.get("title")]
    except Exception as exc:
        status["douban_tv"] = f"failed: {type(exc).__name__}: {exc}"

    # 番茄小说榜单：书名+简介一起参与赛道匹配，小说侧信号最准
    books: list[dict] = []
    try:
        books = fanqie()
        status["fanqie_rank"] = f"ok ({len(books)})"
        for b in books:
            titles.append(f"{b.get('书名') or ''} {b.get('简介') or ''}")
    except Exception as exc:
        status["fanqie_rank"] = f"failed: {type(exc).__name__}: {exc}"

    now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    result = {
        "fetched_at": now,
        "sources_status": status,
        "topic_count": len(titles),
        "genre_scores": genre_scores(titles),
        "douban_hot_tv": tv if not args.quiet else len(tv),
        "fanqie_rank": books if not args.quiet else len(books),
        "raw": sources if not args.quiet else "hidden (--quiet)",
        "usage_note": (
            "这是公开热榜的话题热度证据，不是平台播放量或分账数据。"
            "引用时必须写明来源与抓取时间；平台级数据（云合/DataEye/红果）"
            "需要创作者提供，缺失就写「未提供热度数据」，不得编造。"
        ),
    }

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
