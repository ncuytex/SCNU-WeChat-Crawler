#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华南师范大学「晚安华师」微信公众号日程自动抓取工具 v6.0
======================================================
功能特性：
1. 全自动运行 - 无需任何用户输入，双击即可运行
2. 自动访问华南师范大学新闻网 (https://news.scnu.edu.cn/)
3. 自动提取页面所有文章链接
4. 自动检测 302 跳转，智能筛选微信公众号链接
5. 自动抓取文章内容，校验来源「晚安华师」
6. 按微信官方发布时间排序，取最新 2 篇
7. 智能提取日程信息
8. 自动输出到控制台和 markdown 文件

运行方式：
    python auto_scnu_crawler.py

输出：
    - 控制台打印抓取结果
    - wechat_schedule_output.md (含文章详情和日程汇总)
    - scnu_auto_crawler.log (运行日志)

注意事项：
    1. 新发布文章需等待 10-30 分钟才能被抓取
    2. 程序自动使用微信 UA 绕过安全策略
    3. 仅处理跳转到 mp.weixin.qq.com 的链接
"""

import re
import os
import sys
import json
import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ============================================================
#  可配置参数
# ============================================================

# 目标网站
NEWS_SCNU_EDU_URL = "https://news.scnu.edu.cn/"

# 提取脚本相关
WECHAT_ARTICLE_EXTRACTOR_PATH = None  # 本地 wechat-article-extractor 脚本路径

# 兜底 API 地址
FETCHER_API_URL = "https://down.mptext.top/api/public/v1/download"

# 校验规则阈值
MIN_CONTENT_LENGTH = 500  # 正文最小长度
MIN_TITLE_LENGTH = 5      # 标题最小长度

# 抓取等待时间（秒）
FETCH_DELAY = 2           # 请求间隔，避免触发反爬
API_TIMEOUT = 15          # API 请求超时时间
PAGE_TIMEOUT = 20         # 新闻网页面超时

# 输出配置
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_MARKDOWN_FILE = os.path.join(OUTPUT_DIR, "wechat_schedule_output.md")

# 日志配置
LOG_FILE = os.path.join(OUTPUT_DIR, "scnu_auto_crawler.log")

# 需要获取的最新文章数量
TARGET_ARTICLE_COUNT = 2

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

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def get_with_redirect(url: str, allow_redirects: bool = True,
                      headers: Optional[Dict] = None,
                      timeout: int = API_TIMEOUT) -> Tuple[Optional[str], Optional[str]]:
    """
    发送 GET 请求，返回 (最终 URL, 响应内容)
    allow_redirects=False 时可检测 302 跳转目标
    """
    try:
        resp = requests.get(
            url,
            headers=headers or HEADERS,
            timeout=timeout,
            allow_redirects=allow_redirects
        )
        resp.raise_for_status()
        return resp.url, resp.text
    except requests.RequestException as e:
        logger.warning(f"请求失败 {url}: {e}")
        return None, None


def get_redirect_url(url: str, timeout: int = 10) -> Optional[str]:
    """
    获取 URL 的 302 跳转目标地址
    不跟随跳转，直接返回 Location 头中的 URL
    """
    try:
        resp = requests.get(
            url,
            headers=BROWSER_HEADERS,
            timeout=timeout,
            allow_redirects=False
        )
        if resp.status_code in [301, 302, 303, 307, 308]:
            location = resp.headers.get('Location')
            if location:
                return location
        return resp.url
    except requests.RequestException as e:
        logger.debug(f"获取跳转失败 {url}: {e}")
        return None


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
#  第一步：自动访问华南师范大学新闻网，提取所有文章链接
# ============================================================

def fetch_news_page(url: str = NEWS_SCNU_EDU_URL) -> Optional[str]:
    """
    访问华南师范大学新闻网首页，返回 HTML 内容
    """
    logger.info(f"访问新闻网：{url}")
    _, html = get_with_redirect(url, headers=BROWSER_HEADERS, timeout=PAGE_TIMEOUT)
    if html:
        logger.info(f"成功获取新闻网页面，大小：{len(html)} 字节")
    else:
        logger.error(f"无法访问新闻网：{url}")
    return html


def extract_article_links(html: str, base_url: str = NEWS_SCNU_EDU_URL) -> List[str]:
    """
    从 HTML 页面提取所有可能的文章链接
    返回去重后的链接列表
    """
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    links = set()

    # 查找所有 <a> 标签，提取 href
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if href:
            # 处理相对路径
            full_url = urljoin(base_url, href)
            links.add(full_url)

    logger.info(f"从页面提取到 {len(links)} 个唯一链接")
    return list(links)


# ============================================================
#  第二步：自动检测 302 跳转，筛选微信公众号链接
# ============================================================

def is_wechat_url(url: str) -> bool:
    """
    判断 URL 是否为微信公众号文章链接
    """
    return "mp.weixin.qq.com" in url


def filter_wechat_links(links: List[str]) -> List[str]:
    """
    检测所有链接的 302 跳转目标，筛选出跳转到 mp.weixin.qq.com 的链接
    返回有效微信链接列表
    """
    logger.info(f"开始检测 {len(links)} 个链接的跳转目标...")
    wechat_links = []

    for i, link in enumerate(links, 1):
        logger.debug(f"[{i}/{len(links)}] 检测：{link}")

        # 先直接判断是否已经是微信链接
        if is_wechat_url(link):
            logger.info(f"直接匹配微信链接：{link}")
            wechat_links.append(link)
            time.sleep(FETCH_DELAY)
            continue

        # 检测 302 跳转
        redirect_url = get_redirect_url(link)
        if redirect_url and is_wechat_url(redirect_url):
            logger.info(f"跳转至微信：{link} -> {redirect_url}")
            wechat_links.append(redirect_url)
        else:
            logger.debug(f"跳过非微信链接：{link}")

        # 请求间隔，避免触发反爬
        time.sleep(FETCH_DELAY)

    logger.info(f"筛选出 {len(wechat_links)} 个有效微信链接")
    return list(set(wechat_links))  # 去重


# ============================================================
#  第三步：提取文章正文
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
                output = result.stdout
                try:
                    data = json.loads(output)
                    return data.get("title"), data.get("publish_date"), data.get("source"), data.get("content")
                except json.JSONDecodeError:
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
            lines = markdown_content.strip().split("\n")
            title = lines[0].lstrip("#").strip() if lines else ""
            return title, "", "", markdown_content
    except Exception as e:
        logger.warning(f"兜底 API 失败：{e}")

    return None, None, None, None


# ============================================================
#  第四步：数据校验
# ============================================================

def validate_article(title: str, source: str, content: str, source_name: str = "晚安华师") -> bool:
    """
    校验文章是否符合要求
    """
    if not title or len(title) < MIN_TITLE_LENGTH:
        logger.warning(f"校验失败：标题无效 '{title}'")
        return False

    if not content:
        logger.warning("校验失败：内容为空")
        return False

    if len(content) < MIN_CONTENT_LENGTH:
        logger.warning(f"校验失败：内容长度不足 {len(content)} < {MIN_CONTENT_LENGTH}")
        return False

    # 来源校验
    if source and source_name not in source:
        logger.warning(f"校验失败：来源不匹配 '{source}'")
        return False

    return True


# ============================================================
#  第五步：时间提取模块
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
    if re.search(r"[??!！]", event):
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
#  第六步：输出模块
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
    """控制台输出"""
    print()
    print("=" * 60)
    print("抓取结果")
    print("=" * 60)

    for i, art in enumerate(articles, 1):
        print(f"\n[文章 {i}]")
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
#  第七步：排序模块 - 按微信官方发布时间排序
# ============================================================

def parse_publish_date(date_str: str) -> datetime:
    """解析发布日期字符串为 datetime 对象"""
    if not date_str:
        return datetime.min

    # 尝试多种格式
    formats = [
        "%Y-%m-%d",
        "%Y年%m月%d日",
        "%Y-%m-%d %H:%M:%S",
        "%Y年%m月%d日 %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str[:len(date_str)].strip(), fmt)
        except ValueError:
            continue

    return datetime.min


def sort_articles_by_date(articles: List[Article]) -> List[Article]:
    """按发布日期降序排序（最新的在前）"""
    return sorted(articles, key=lambda a: parse_publish_date(a.publish_date), reverse=True)


# ============================================================
#  主流程 - 全自动执行
# ============================================================

def run_auto_crawler() -> List[Article]:
    """
    全自动爬虫主流程
    1. 访问新闻网
    2. 提取所有链接
    3. 检测 302 跳转，筛选微信链接
    4. 抓取文章并校验
    5. 排序取最新 N 篇
    6. 提取日程
    7. 输出结果
    """
    print()
    print("=" * 60)
    print("华南师范大学「晚安华师」日程自动抓取工具 v6.0")
    print("=" * 60)
    print(f"目标网站：{NEWS_SCNU_EDU_URL}")
    print(f"输出文件：{OUTPUT_MARKDOWN_FILE}")
    print(f"目标获取：最新 {TARGET_ARTICLE_COUNT} 篇")
    print()
    print("开始全自动抓取...")
    print("=" * 60)

    articles = []

    # Step 1: 访问新闻网
    print("\n[Step 1/6] 访问华南师范大学新闻网...")
    html = fetch_news_page()
    if not html:
        logger.error("无法访问新闻网，程序终止")
        print("[失败] 无法访问新闻网")
        return []
    time.sleep(FETCH_DELAY)

    # Step 2: 提取所有链接
    print("[Step 2/6] 提取页面所有文章链接...")
    all_links = extract_article_links(html)
    print(f"  找到 {len(all_links)} 个链接")
    time.sleep(FETCH_DELAY)

    # Step 3: 筛选微信公众号链接
    print("[Step 3/6] 检测 302 跳转，筛选微信链接...")
    wechat_links = filter_wechat_links(all_links)
    print(f"  筛选出 {len(wechat_links)} 个微信链接")

    if not wechat_links:
        logger.warning("未找到任何微信公众号链接")
        print("\n[警告] 未找到任何微信公众号链接")
        print("可能原因：")
        print("  1. 新闻网当前没有「晚安华师」的文章")
        print("  2. 网络请求失败")
        print("稍后可重新运行程序重试。")
        return []

    # Step 4: 抓取文章并校验
    print(f"\n[Step 4/6] 抓取文章并校验（目标 {TARGET_ARTICLE_COUNT} 篇）...")
    for i, url in enumerate(wechat_links, 1):
        print(f"\n  [{i}/{len(wechat_links)}] 处理：{url[:60]}...")

        title, pub_date, source, content = extract_article_content(url)

        if not validate_article(title, source, content):
            print("    [跳过] 文章校验失败")
            continue

        # 提取日程
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
        articles.append(article)
        print(f"    [成功] 标题={title[:30]}..., 日程={len(events)} 条")

        # 已达到目标数量，停止抓取
        if len(articles) >= TARGET_ARTICLE_COUNT:
            print(f"\n  已达到目标数量 ({TARGET_ARTICLE_COUNT} 篇)，停止抓取")
            break

        time.sleep(FETCH_DELAY)

    if not articles:
        print("\n[失败] 未能抓取到任何符合要求的文章")
        return []

    # Step 5: 按发布时间排序
    print(f"\n[Step 5/6] 按发布时间排序...")
    articles = sort_articles_by_date(articles)
    print(f"  最新文章：{articles[0].title if articles else '无'}")

    # Step 6: 输出结果
    print(f"\n[Step 6/6] 输出结果...")

    # 控制台输出
    print_console_output(articles)

    # 保存 markdown 文件
    markdown_content = format_markdown(articles)
    save_markdown(markdown_content, OUTPUT_MARKDOWN_FILE)

    print()
    print("=" * 60)
    print("抓取完成")
    print("=" * 60)
    print(f"成功抓取：{len(articles)} 篇文章")
    print(f"结果已保存到：{OUTPUT_MARKDOWN_FILE}")
    print(f"日志文件：{LOG_FILE}")

    return articles


def main():
    """主函数 - 全自动入口"""
    try:
        articles = run_auto_crawler()
        if not articles:
            print("\n程序执行完成，但未获取到任何文章。")
            print("请检查：")
            print("  1. 网络连接是否正常")
            print("  2. 华南师范大学新闻网是否可访问")
            print("  3. 当前是否有「晚安华师」的文章发布")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"程序异常退出：{e}")
        print(f"\n程序异常退出：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
