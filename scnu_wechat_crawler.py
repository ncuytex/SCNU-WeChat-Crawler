#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华南师范大学「晚安华师」微信公众号日程自动抓取工具 v5.0
======================================================
功能：
1. 支持手动输入微信公众号文章链接
2. 提取「晚安华师」推文正文
3. 智能识别并抽取日程信息
4. 输出结果到控制台和 markdown 文件

运行步骤：
1. 确保已安装依赖：pip install -r requirements.txt
2. 运行程序：python scnu_wechat_crawler.py
3. 输入微信公众号文章链接（mp.weixin.qq.com）
4. 查看控制台输出和 wechat_schedule_output.md 文件

注意事项：
1. 新发布文章需等待 10-30 分钟才能被抓取
2. fetcher API 仅用于兜底校验，不稳定
3. 程序会自动规避微信安全策略，使用带 UA 的请求
"""

import re
import os
import sys
import json
import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

import requests
from bs4 import BeautifulSoup

# ============================================================
#  可配置参数
# ============================================================

# 提取脚本相关
WECHAT_ARTICLE_EXTRACTOR_PATH = None  # 本地 wechat-article-extractor 脚本路径，如无则置为 None

# 兜底 API 地址
FETCHER_API_URL = "https://down.mptext.top/api/public/v1/download"

# 校验规则阈值
MIN_CONTENT_LENGTH = 500  # 正文最小长度

# 抓取等待时间（秒）
FETCH_DELAY = 1  # 请求间隔，避免触发反爬
API_TIMEOUT = 10  # API 请求超时时间

# 输出配置
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_MARKDOWN_FILE = os.path.join(OUTPUT_DIR, "wechat_schedule_output.md")

# 日志配置
LOG_FILE = os.path.join(OUTPUT_DIR, "scnu_crawler.log")

# ============================================================
#  日志初始化
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
#  数据结构
# ============================================================


@dataclass
class Article:
    """文章数据结构"""
    title: str
    publish_date: str
    source: str
    content: str
    url: str
    schedule_events: List[Dict]


# ============================================================
#  HTTP 请求工具
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 "
        "MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def get_with_redirect(url: str, allow_redirects: bool = True) -> Tuple[Optional[str], Optional[str]]:
    """
    发送 GET 请求，返回 (最终 URL, 响应内容)
    """
    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            timeout=API_TIMEOUT,
            allow_redirects=allow_redirects
        )
        resp.raise_for_status()
        return resp.url, resp.text
    except requests.RequestException as e:
        logger.warning(f"请求失败 {url}: {e}")
        return None, None


# ============================================================
#  文章正文提取
# ============================================================

def extract_article_content(wechat_url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    提取微信文章正文
    返回：(title, publish_date, source, content)
    """
    # 方法 1：直接请求（带微信 UA）
    try:
        logger.info(f"尝试直接抓取：{wechat_url}")
        _, html = get_with_redirect(wechat_url)
        if html:
            soup = BeautifulSoup(html, "lxml")

            # 提取标题
            title_el = soup.find("h1", class_="rich_media_title") or soup.find("h1")
            title = title_el.get_text(strip=True) if title_el else ""

            # 提取发布时间
            pub_time = ""
            time_el = soup.find("em", id="publish_time") or soup.find("span", class_="rich_media_meta_text")
            if time_el:
                pub_time = time_el.get_text(strip=True)

            # 提取来源
            source_el = soup.find("span", class_="rich_media_meta_nickname")
            source = source_el.get_text(strip=True) if source_el else ""

            # 提取正文
            content_div = (
                soup.find("div", id="js_content")
                or soup.find("div", class_="rich_media_content")
            )
            if content_div:
                for tag in content_div.find_all(["script", "style"]):
                    tag.decompose()
                content = content_div.get_text(separator="\n", strip=True)

                if len(content) > MIN_CONTENT_LENGTH:
                    logger.info(f"直接抓取成功：标题={title}, 长度={len(content)}")
                    return title, pub_time, source, content

            logger.warning(f"直接抓取内容不足：长度={len(content) if content else 0}")
    except Exception as e:
        logger.warning(f"直接抓取失败：{e}")

    # 方法 2：使用 wechat-article-extractor（如果可用）
    if WECHAT_ARTICLE_EXTRACTOR_PATH:
        try:
            logger.info(f"使用 wechat-article-extractor: {WECHAT_ARTICLE_EXTRACTOR_PATH}")
            import subprocess
            result = subprocess.run(
                [sys.executable, WECHAT_ARTICLE_EXTRACTOR_PATH, "--no-vision", wechat_url],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # 解析输出
                output = result.stdout
                # 假设输出格式为 JSON
                try:
                    data = json.loads(output)
                    return data.get("title"), data.get("publish_date"), data.get("source"), data.get("content")
                except json.JSONDecodeError:
                    # 非 JSON 输出，尝试解析纯文本
                    lines = output.strip().split("\n")
                    if len(lines) >= 3:
                        return lines[0], lines[1], lines[2] if len(lines) > 2 else "", "\n".join(lines[3:]) if len(lines) > 3 else ""
        except Exception as e:
            logger.warning(f"wechat-article-extractor 失败：{e}")

    # 方法 3：兜底 API
    logger.info(f"使用兜底 API: {wechat_url}")
    try:
        api_url = f"{FETCHER_API_URL}?url={wechat_url}&format=markdown"
        _, markdown_content = get_with_redirect(api_url)
        if markdown_content and len(markdown_content) > MIN_CONTENT_LENGTH:
            # 从 markdown 中提取标题（第一行）
            lines = markdown_content.strip().split("\n")
            title = lines[0].lstrip("#").strip() if lines else ""
            return title, "", "", markdown_content
    except Exception as e:
        logger.warning(f"兜底 API 失败：{e}")

    return None, None, None, None


# ============================================================
#  数据校验
# ============================================================

def validate_article(title: str, source: str, content: str) -> bool:
    """
    校验文章是否符合要求
    """
    if not title:
        logger.warning("校验失败：标题为空")
        return False

    if not content:
        logger.warning("校验失败：内容为空")
        return False

    if len(content) < MIN_CONTENT_LENGTH:
        logger.warning(f"校验失败：内容长度不足 {len(content)} < {MIN_CONTENT_LENGTH}")
        return False

    # 来源校验（可选，某些文章可能没有明确来源）
    if source and "晚安华师" not in source:
        logger.warning(f"校验失败：来源不匹配 '{source}'")
        return False

    return True


# ============================================================
#  时间提取模块
# ============================================================

TIME_PATTERNS = [
    (r"(?P<year>\d{4})\s*年\s*(?P<month>\d{1,2})\s*月\s*(?P<day>\d{1,2})\s*日", "full_date"),
    (r"(?P<month>\d{1,2})\s*月\s*(?P<day>\d{1,2})\s*日(?:左右 | 前后 | 之前 | 之后)?", "month_day"),
    (r"(?P<month>\d{1,2})\s*月\s*(?P<period>上旬 | 中旬 | 下旬)", "month_period"),
    (
        r"(?P<prefix>下\s*周 | 本\s*周 | 这\s*周 | 下个周 | 这个周)?"
        r"(?P<weekday>周 [一二三四五六日天] | 星期 [一二三四五六日天])",
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
    if re.match(r"^\s*(?:\d{4}\s*年\s*)?\d{1,2}\s*月", s):
        return True
    if re.match(r"^\s*(?:下\s*周 | 本\s*周 | 这\s*周)\s*(?:周 | 星期)", s):
        return True
    if re.match(r"^\s*[\d 一二三四五六七八九十]+[.、)．]\s*", s):
        return True
    if re.match(r"^\s*[·●○◆▪▸►▶\-—–]\s*", s):
        return True
    return False


def _is_valid_event(event: str) -> bool:
    """对非日程行中提取的事件进行严格验证。"""
    if len(event) < 4:
        return False
    if re.search(r'[""「」『』《》]', event):
        return False
    if re.search(r"[？？!！]", event):
        return False
    if re.match(r"^\s*(?:也 | 还 | 但 | 却 | 而 | 且 | 虽然 | 不过 | 然而 | 其实 | 但是 | 因此 | 所以 | 因为 | 由于 | 如果 | 假如 | 若)", event):
        return False
    if re.search(r"既.{0,8}也 | 既.{0,8}又 | 不是.{0,8}而是 | 没有.{0,8}也没有 | 虽然.{0,8}但 | 尽管.{0,8}但", event):
        return False
    if re.search(r"(?:开学 | 考试 | 放假 | 安排) 的 (?:惯例 | 时间 | 原因 | 规定 | 消息 | 说法 | 情况 | 结果 | 通知 | 内容 | 详情)", event):
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
            for punct in "。！？":
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
#  输出模块
# ============================================================

def format_markdown(articles: List[Article]) -> str:
    """
    将抓取结果格式化为 markdown
    """
    lines = []
    lines.append("# 晚安华师日程信息抓取结果")
    lines.append(f"抓取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"共抓取 {len(articles)} 篇文章\n")

    for i, art in enumerate(articles, 1):
        lines.append(f"## 文章 {i}")
        lines.append(f"- **标题**: {art.title}")
        lines.append(f"- **发布日期**: {art.publish_date}")
        lines.append(f"- **来源**: {art.source}")
        lines.append(f"- **原文链接**: [{art.url}]({art.url})")
        lines.append("")

        if art.schedule_events:
            lines.append("### 提取的日程信息")
            for evt in art.schedule_events:
                lines.append(f"- [{evt['标准化时间']}] {evt['事件内容']}")
        else:
            lines.append("### 提取的日程信息")
            lines.append("无相关日程")
        lines.append("")

        lines.append("### 原文内容（前 500 字）")
        content_preview = art.content[:500] + "..." if len(art.content) > 500 else art.content
        lines.append("```")
        lines.append(content_preview)
        lines.append("```\n")

    lines.append("---\n## 日程汇总\n")
    all_events = []
    for art in articles:
        all_events.extend(art.schedule_events)

    if all_events:
        # 按时间排序
        all_events.sort(key=lambda x: x.get("标准化时间", ""))
        for evt in all_events:
            lines.append(f"- [{evt['标准化时间']}] {evt['事件内容']}")
    else:
        lines.append("暂无日程信息")

    return "\n".join(lines)


def save_markdown(content: str, filepath: str) -> bool:
    """保存 markdown 到文件"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"已保存到：{filepath}")
        return True
    except Exception as e:
        logger.error(f"保存失败：{e}")
        return False


def print_console_output(articles: List[Article]):
    """
    控制台输出
    """
    print()
    print("=" * 60)
    print("抓取结果")
    print("=" * 60)

    for i, art in enumerate(articles, 1):
        print(f"\n[成功] 抓取到「晚安华师」最新文章{i}：")
        print(f"标题：{art.title}")
        print(f"发布日期：{art.publish_date}")
        print(f"来源：{art.source}")

        if art.schedule_events:
            print("提取日程信息：")
            for evt in art.schedule_events:
                print(f"  - [{evt['标准化时间']}] {evt['事件内容']}")
        else:
            print("提取日程信息：无相关日程")


# ============================================================
#  单篇文章处理
# ============================================================

def process_article(url: str) -> Optional[Article]:
    """
    处理单篇微信公众号文章
    """
    if "mp.weixin.qq.com" not in url:
        print("  [跳过] 非微信公众号文章链接")
        return None

    print("  正在处理...")
    title, pub_date, source, content = extract_article_content(url)

    if not validate_article(title, source, content):
        print("  [失败] 文章校验失败")
        return None

    # 提取日程信息
    article_date = datetime.now()
    if pub_date:
        try:
            article_date = datetime.strptime(pub_date[:10], "%Y-%m-%d")
        except ValueError:
            pass

    events = extract_time_events(content, article_date)

    article = Article(
        title=title,
        publish_date=pub_date,
        source=source or "微信公众号「晚安华师」",
        content=content,
        url=url,
        schedule_events=events
    )
    print(f"  [成功] 提取到 {len(events)} 条日程")
    return article


# ============================================================
#  主流程
# ============================================================

def main():
    """主函数"""
    print()
    print("=" * 60)
    print("华南师范大学「晚安华师」日程自动抓取工具 v5.0")
    print("=" * 60)
    print(f"输出文件：{OUTPUT_MARKDOWN_FILE}")
    print()
    print("运行步骤说明：")
    print("1. 输入微信公众号文章链接（mp.weixin.qq.com）")
    print("2. 程序提取文章正文和日程信息")
    print("3. 输出到控制台和 markdown 文件")
    print()
    print("注意：")
    print("1. 新发布文章需等待 10-30 分钟才能被抓取")
    print("2. 程序会自动使用微信 UA 规避安全策略")
    print("3. fetcher API 仅用于兜底校验")
    print()
    print("输入 'q' 退出")
    print()

    articles = []

    while True:
        try:
            url = input("请输入文章链接：").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            return

        if url.lower() in ("q", "quit", "exit"):
            break

        if not url:
            continue

        article = process_article(url)
        if article:
            articles.append(article)

        print()

    if not articles:
        print("\n[失败] 未能抓取到任何文章")
        return

    # 控制台输出
    print_console_output(articles)

    # 保存到 markdown 文件
    markdown_content = format_markdown(articles)
    save_markdown(markdown_content, OUTPUT_MARKDOWN_FILE)

    print()
    print("=" * 60)
    print("抓取完成")
    print("=" * 60)
    print(f"成功抓取：{len(articles)} 篇文章")
    print(f"结果已保存到：{OUTPUT_MARKDOWN_FILE}")


if __name__ == "__main__":
    main()
