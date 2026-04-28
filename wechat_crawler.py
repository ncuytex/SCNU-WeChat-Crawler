#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章日程提取工具 v3.0
================================
输入文章链接 → 提取时间+事件 → 输出到文件
"""

import re
import os
import csv
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

# ============================================================
#  路径 & 常量
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "events.csv")
LOG_FILE = os.path.join(BASE_DIR, "crawler.log")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 "
        "MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI"
    ),
    "Referer": "https://mp.weixin.qq.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# ============================================================
#  日志
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ============================================================
#  时间提取模块
# ============================================================

TIME_PATTERNS = [
    (r"(?P<year>\d{4})\s*年\s*(?P<month>\d{1,2})\s*月\s*(?P<day>\d{1,2})\s*日", "full_date"),
    (r"(?P<month>\d{1,2})\s*月\s*(?P<day>\d{1,2})\s*日(?:左右|前后|之前|之后)?", "month_day"),
    (r"(?P<month>\d{1,2})\s*月\s*(?P<period>上旬|中旬|下旬)", "month_period"),
    (
        r"(?P<prefix>下\s*周|本\s*周|这\s*周|下个周|这个周)?"
        r"(?P<weekday>周[一二三四五六日天]|星期[一二三四五六日天])",
        "weekday",
    ),
]

WEEKDAY_NUM = {
    "一": 0, "二": 1, "三": 2, "四": 3,
    "五": 4, "六": 5, "日": 6, "天": 6,
}

SCHEDULE_KEYWORDS = (
    "开学", "放假", "考试", "报名", "截止", "上课", "返校", "报到",
    "注册", "缴费", "军训", "测验", "测试", "月考", "期中", "期末",
    "模拟", "家长会", "班会", "运动会", "实践", "研学", "体检",
    "面试", "提交", "上交", "领取", "办理", "完成", "开始", "结束",
    "出发", "抵达", "离校", "放学", "集合", "公布", "发布", "选课",
    "退课", "补考", "重修", "实习", "答辩", "毕业", "入学", "分班",
    "集训", "培训", "讲座", "会议", "活动", "开放", "关闭", "启动",
    "暂停", "恢复", "安排", "通知", "日程", "开课", "结课",
    "招聘", "入职", "考核", "评比", "评选", "表彰", "竞赛", "比赛",
    "演出", "展览", "汇报", "报告", "座谈", "研讨", "交流", "参观",
    "接待", "庆典", "仪式", "典礼", "纪念", "庆祝", "联欢", "晚会",
    "考查", "测评", "评估", "审查", "审核", "验收", "检查",
)


def _standardize(match: dict, article_date: datetime) -> str:
    mtype = match["type"]
    g = match["groups"]
    year = article_date.year

    try:
        if mtype == "full_date":
            y, m, d = int(g["year"]), int(g["month"]), int(g["day"])
            return f"{y:04d}-{m:02d}-{d:02d}"

        if mtype == "month_day":
            m, d = int(g["month"]), int(g["day"])
            try:
                dt = datetime(year, m, d)
                if dt > article_date + timedelta(days=90):
                    dt = datetime(year - 1, m, d)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                return f"{year}-{m:02d}-{d:02d}"

        if mtype == "month_period":
            m = int(g["month"])
            period = g["period"]
            d = {"上旬": 5, "中旬": 15, "下旬": 25}[period]
            try:
                dt = datetime(year, m, d)
                if dt > article_date + timedelta(days=90):
                    dt = datetime(year - 1, m, d)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                return match["text"]

        if mtype == "weekday":
            prefix = (g.get("prefix") or "").replace(" ", "")
            wd_char = g["weekday"][-1]
            if wd_char not in WEEKDAY_NUM:
                return match["text"]
            target_wd = WEEKDAY_NUM[wd_char]
            current_wd = article_date.weekday()
            if "下" in prefix:
                delta = (target_wd - current_wd + 7) % 7 or 7
            else:
                delta = (target_wd - current_wd) % 7
            return (article_date + timedelta(days=delta)).strftime("%Y-%m-%d")

    except (ValueError, KeyError):
        pass

    return match["text"]


def _is_schedule_line(line: str) -> bool:
    """判断一行文本是否具有日程条目的结构特征。"""
    s = line.strip()
    if len(s) > 100:
        return False
    if re.match(r'^\s*(?:\d{4}\s*年\s*)?\d{1,2}\s*月', s):
        return True
    if re.match(r'^\s*(?:下\s*周|本\s*周|这\s*周)\s*(?:周|星期)', s):
        return True
    if re.match(r'^\s*[\d一二三四五六七八九十]+[.、)．]\s*', s):
        return True
    if re.match(r'^\s*[·●○◆▪▸►▶\-—–]\s*', s):
        return True
    return False


def _is_valid_event(event: str) -> bool:
    """对非日程行中提取的事件进行严格验证。"""
    if len(event) < 4:
        return False
    if re.search(r'[""「」『』《》]', event):
        return False
    if re.search(r'[？?！!]', event):
        return False
    if re.match(r'^(也|还|但|却|而|且|虽然|不过|然而|其实|但是|因此|所以|因为|由于|如果|假如|若)', event):
        return False
    if re.search(r'既.{0,8}也|既.{0,8}又|不是.{0,8}而是|没有.{0,8}也没有|虽然.{0,8}但|尽管.{0,8}但', event):
        return False
    if re.search(r'(?:开学|考试|放假|安排)的(?:惯例|时间|原因|规定|消息|说法|情况|结果|通知|内容|详情)', event):
        return False
    if not any(kw in event for kw in SCHEDULE_KEYWORDS):
        return False
    return True


def extract_time_events(text: str, article_date: Optional[datetime] = None) -> List[Dict]:
    """从文章正文中提取「时间 + 事件」对。"""
    if not text:
        return []

    if article_date is None:
        article_date = datetime.now()

    results = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        hits = []
        for pattern, ptype in TIME_PATTERNS:
            for m in re.finditer(pattern, line):
                hits.append({
                    "start": m.start(),
                    "end": m.end(),
                    "text": m.group(),
                    "type": ptype,
                    "groups": m.groupdict(),
                })
        hits.sort(key=lambda h: h["start"])

        filtered = []
        for h in hits:
            contained = False
            for f in filtered:
                if f["start"] <= h["start"] and h["end"] <= f["end"] and f is not h:
                    contained = True
                    break
            if not contained:
                filtered.append(h)
        hits = filtered

        schedule_line = _is_schedule_line(line)

        for i, hit in enumerate(hits):
            evt_start = hit["end"]
            while evt_start < len(line) and line[evt_start] in "，,、：:；; \t":
                evt_start += 1

            evt_end = hits[i + 1]["start"] if i + 1 < len(hits) else len(line)
            raw_event = line[evt_start:evt_end].strip()
            for punct in '。！？':
                pos = raw_event.find(punct)
                if 2 <= pos < len(raw_event):
                    raw_event = raw_event[:pos]
                    break
            event = raw_event.rstrip("。；;，,、：: \t")

            if not event:
                continue

            if schedule_line:
                if len(event) < 2:
                    continue
            else:
                if not _is_valid_event(event):
                    continue

            std = _standardize(hit, article_date)
            results.append({
                "时间原文": hit["text"],
                "标准化时间": std,
                "事件内容": event,
            })

    return results


# ============================================================
#  文章抓取
# ============================================================

def fetch_article(url: str):
    """
    抓取单篇文章，返回 (正文文本, 发布时间字符串, 文章标题)。
    失败返回 (None, None, None)。
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"请求失败: {e}")
        return None, None, None

    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "lxml")

    title_el = soup.find("h1", class_="rich_media_title") or soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    content_div = (
        soup.find("div", id="js_content")
        or soup.find("div", class_="rich_media_content")
    )
    if not content_div:
        logger.warning("未找到文章正文区域")
        return None, None, None

    for tag in content_div.find_all(["script", "style"]):
        tag.decompose()

    text = content_div.get_text(separator="\n", strip=True)

    pub_time = ""
    time_el = (
        soup.find("em", id="publish_time")
        or soup.find("span", class_="rich_media_meta_text")
    )
    if time_el:
        pub_time = time_el.get_text(strip=True)

    return text, pub_time, title


# ============================================================
#  存储模块
# ============================================================

FIELDS = ["时间原文", "标准化时间", "事件内容", "文章标题", "文章发布时间", "文章链接", "提取时间"]


def _row_hash(row: Dict) -> str:
    raw = f"{row['时间原文']}|{row['事件内容']}|{row['文章链接']}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _load_existing_hashes() -> set:
    hashes = set()
    if not os.path.exists(OUTPUT_FILE):
        return hashes
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                hashes.add(_row_hash(row))
    except Exception as e:
        logger.warning(f"读取已有记录时出错: {e}")
    return hashes


def save_events(events: List[Dict], meta: Dict) -> int:
    """追加事件记录到 CSV，自动去重。返回实际新增条数。"""
    existing = _load_existing_hashes()
    new_rows = []

    for evt in events:
        row = {
            "时间原文": evt["时间原文"],
            "标准化时间": evt["标准化时间"],
            "事件内容": evt["事件内容"],
            "文章标题": meta["title"],
            "文章发布时间": meta["pub_time"],
            "文章链接": meta["url"],
            "提取时间": meta["crawl_time"],
        }
        h = _row_hash(row)
        if h not in existing:
            new_rows.append(row)
            existing.add(h)

    if not new_rows:
        return 0

    file_exists = os.path.exists(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)

    return len(new_rows)


# ============================================================
#  主流程
# ============================================================

def process_url(url: str):
    """处理单篇文章链接：抓取 → 提取 → 保存"""
    url = url.strip()
    if not url:
        return

    if "mp.weixin.qq.com" not in url:
        print("  [跳过] 非微信公众号文章链接")
        return

    print(f"  正在抓取...")
    text, pub_time, title = fetch_article(url)

    if not text:
        print("  [失败] 无法获取文章内容")
        return

    print(f"  标题: {title or '(未知)'}")
    print(f"  发布时间: {pub_time or '(未知)'}")

    article_date = datetime.now()
    if pub_time:
        try:
            article_date = datetime.strptime(pub_time[:10], "%Y-%m-%d")
        except ValueError:
            pass

    events = extract_time_events(text, article_date)

    if not events:
        print("  [结果] 未匹配到日程信息")
        return

    meta = {
        "title": title,
        "pub_time": pub_time,
        "url": url,
        "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    n = save_events(events, meta)
    print(f"  [结果] 提取到 {len(events)} 条日程，新增 {n} 条")
    for evt in events:
        print(f"    - [{evt['标准化时间']}] {evt['事件内容']}")


def main():
    print()
    print("微信公众号文章日程提取工具 v3.0")
    print("=" * 40)
    print(f"  输出文件: {OUTPUT_FILE}")
    print("  输入文章链接后回车即可提取日程")
    print("  输入 q 退出")
    print()

    while True:
        try:
            url = input("文章链接> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            break

        if url.lower() in ("q", "quit", "exit"):
            print("再见！")
            break

        if not url:
            continue

        process_url(url)
        print()


if __name__ == "__main__":
    main()
