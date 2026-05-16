#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华南师范大学「晚安华师」微信公众号日程自动抓取工具 v6.2
======================================================
功能特性：
1. 全自动运行 - 无需任何用户输入，双击即可运行
2. 自动访问华南师范大学新闻网 (https://news.scnu.edu.cn/)
3. 自动提取页面所有文章链接
4. 自动检测 302 跳转，智能筛选微信公众号链接
5. 自动抓取文章内容，校验来源「晚安华师」
6. 按微信官方发布时间排序，取最新 2 篇
7. 智能提取日程信息（支持正则/AI 双模式）
8. 自动输出到控制台和 markdown 文件
9. 已抓取文章标记 - 自动记录已抓取文章，避免重复处理
10. AI 智能分析日程 - 支持调用 AI 大模型智能分析日程（可选）

运行方式：
    python auto_scnu_crawler.py

输出：
    - 控制台打印抓取结果
    - wechat_schedule_output.md (含文章详情和日程汇总)
    - scnu_auto_crawler.log (运行日志)
    - crawled_urls.txt (已抓取文章 URL 记录)

配置方式：
    - 修改 config.json 配置文件
    - analysis_mode: "regex" (正则模式) 或 "ai" (AI 模式)
    - AI 模式需配置 ai_api_key

注意事项：
    1. 新发布文章需等待 10-30 分钟才能被抓取
    2. 程序自动使用微信 UA 绕过安全策略
    3. 仅处理跳转到 mp.weixin.qq.com 的链接
    4. 已抓取文章会自动记录，下次运行时跳过
    5. AI 模式需要配置有效的 API Key
    6. AI 分析失败时自动降级到正则模式
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

from src.scnu_wechat_crawler import LOG_DIR

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
MIN_TITLE_LENGTH = 5  # 标题最小长度

# 抓取等待时间（秒）
FETCH_DELAY = 2  # 请求间隔，避免触发反爬
API_TIMEOUT = 15  # API 请求超时时间
PAGE_TIMEOUT = 20  # 新闻网页面超时

# 输出配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_MARKDOWN_FILE = os.path.join(OUTPUT_DIR, "wechat_schedule_output.md")

# 日志配置
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "scnu_auto_crawler.log")

# 已抓取记录配置
CRAWLED_RECORD_FILE = os.path.join(LOG_DIR, "crawled_urls.txt")

# 需要获取的最新文章数量
TARGET_ARTICLE_COUNT = 2

# ============================================================
#  配置文件管理
# ============================================================

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "analysis_mode": "regex",
    "ai_api_type": "deepseek",
    "ai_api_url": "https://api.deepseek.com/v1/chat/completions",
    "ai_api_key": "",
    "ai_model": "deepseek-chat",
    "ai_timeout": 90,
    "max_retry": 3,
    "ai_prompt": "请你从文章中提取所有日程、活动、会议、通知信息，包括时间、地点、事件、参与对象。请按照以下 JSON 格式返回：{\"events\": [{\"time\": \"时间\", \"location\": \"地点\", \"event\": \"事件\", \"participants\": \"参与对象\"}]}。如果没有日程，返回 {\"events\": []}。只返回 JSON，不要多余解释。",
}


def check_config_file() -> bool:
    """
    检查配置文件是否存在
    如果不存在，提示用户复制 config.example.json

    返回：配置文件是否存在
    """
    if not os.path.exists(CONFIG_FILE):
        example_file = os.path.join(BASE_DIR, "config.example.json")
        print("\n" + "=" * 60)
        print("配置文件缺失提示")
        print("=" * 60)
        print(f"未找到配置文件：{CONFIG_FILE}")
        print()
        if os.path.exists(example_file):
            print("请按以下步骤初始化配置：")
            print()
            print("  1. 复制配置模板文件：")
            print(f"     cp config.example.json config.json")
            print()
            print("  2. 编辑 config.json，填写你的配置信息：")
            print(f"     {CONFIG_FILE}")
            print()
            print("  3. 如需使用 AI 分析模式，请配置 ai_api_key")
            print()
            print("提示：当前将使用默认配置继续运行")
            print("=" * 60)
        else:
            print("错误：配置模板文件也不存在")
            print(f"请检查项目文件是否完整：{example_file}")
            print("=" * 60)
        return False
    return True


def load_config() -> Dict:
    """
    加载配置文件
    如果配置文件不存在，使用默认配置并提示用户
    """
    config = DEFAULT_CONFIG.copy()

    # 检查配置文件是否存在
    config_exists = check_config_file()

    try:
        if config_exists:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                config.update(file_config)
            logger.info(f"已加载配置文件：{CONFIG_FILE}")
        else:
            logger.warning(f"配置文件不存在：{CONFIG_FILE}，使用默认配置")
    except json.JSONDecodeError as e:
        logger.error(f"配置文件 JSON 格式错误：{e}")
        print(f"\n[错误] 配置文件 JSON 格式错误：{e}")
        print("请检查 config.json 文件语法是否正确")
    except Exception as e:
        logger.error(f"加载配置文件失败：{e}，使用默认配置")
        print(f"\n[警告] 加载配置文件失败：{e}")

    return config

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
#  已抓取记录管理
# ============================================================

def load_crawled_urls() -> Set[str]:
    """
    从本地文件加载已抓取的 URL 记录
    返回：已抓取 URL 的集合
    """
    crawled = set()
    try:
        if os.path.exists(CRAWLED_RECORD_FILE):
            with open(CRAWLED_RECORD_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    url = line.strip()
                    if url:
                        crawled.add(url)
            logger.info(f"已加载 {len(crawled)} 条已抓取记录")
    except Exception as e:
        logger.warning(f"读取已抓取记录失败：{e}")
    return crawled


def save_crawled_urls(crawled: Set[str]) -> bool:
    """
    将已抓取的 URL 记录保存到本地文件
    返回：是否保存成功
    """
    try:
        with open(CRAWLED_RECORD_FILE, "w", encoding="utf-8") as f:
            for url in sorted(crawled):
                f.write(url + "\n")
        logger.info(f"已保存 {len(crawled)} 条已抓取记录到 {CRAWLED_RECORD_FILE}")
        return True
    except Exception as e:
        logger.error(f"保存已抓取记录失败：{e}")
        return False


def add_crawled_url(crawled: Set[str], url: str) -> bool:
    """
    添加单个 URL 到已抓取记录
    返回：是否添加成功（URL 已存在时返回 False）
    """
    if url in crawled:
        return False
    crawled.add(url)
    return save_crawled_urls(crawled)

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
                timeout=60
            )
            if result.returncode == 0:
                output = result.stdout
                try:
                    data = json.loads(output)
                    return data.get("title"), data.get("publish_date"), data.get("source"), data.get("content")
                except json.JSONDecodeError:
                    lines = output.strip().split("\n")
                    if len(lines) >= 3:
                        return lines[0], lines[1], lines[2] if len(lines) > 2 else "", "\n".join(lines[3:]) if len(
                            lines) > 3 else ""
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
#  AI 分析模块
# ============================================================

class AIAnalyzer:
    """AI 大模型分析器"""

    def __init__(self, config: Dict):
        self.api_url = config.get("ai_api_url", DEFAULT_CONFIG["ai_api_url"])
        self.api_key = config.get("ai_api_key", "")
        self.model = config.get("ai_model", DEFAULT_CONFIG["ai_model"])
        self.api_type = config.get("ai_api_type", DEFAULT_CONFIG["ai_api_type"])
        self.timeout = config.get("ai_timeout", DEFAULT_CONFIG["ai_timeout"])
        self.max_retry = config.get("max_retry", DEFAULT_CONFIG["max_retry"])
        self.prompt = config.get("ai_prompt", DEFAULT_CONFIG["ai_prompt"])

    def analyze(self, content: str) -> List[Dict]:
        """
        使用 AI 分析文章内容，提取日程信息
        返回统一的日程格式：[{"时间原文": "...", "标准化时间": "...", "事件内容": "..."}]
        """
        if not self.api_key:
            logger.warning("AI API Key 未配置，降级到正则模式")
            return []

        if not content or len(content) < MIN_CONTENT_LENGTH:
            logger.debug("文章内容不足，跳过 AI 分析")
            return []

        for attempt in range(1, self.max_retry + 1):
            try:
                logger.info(f"[AI 分析] 第 {attempt}/{self.max_retry} 次尝试...")
                result = self._call_api(content)
                if result:
                    logger.info(f"[AI 分析] 成功提取 {len(result)} 条日程")
                    return result
                logger.warning(f"[AI 分析] 第 {attempt} 次返回为空")
            except Exception as e:
                logger.warning(f"[AI 分析] 第 {attempt} 次失败：{e}")
            if attempt < self.max_retry:
                time.sleep(1)

        logger.warning("[AI 分析] 所有尝试均失败，降级到正则模式")
        return []

    def _call_api(self, content: str) -> List[Dict]:
        """调用 AI API 分析内容"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # DeepSeek / OpenAI / 阿里云百炼兼容格式
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": f"{self.prompt}\n\n文章内容：\n{content[:8000]}"}
            ],
            "temperature": 0.1,
        }

        # 阿里云百炼需要完整的 URL
        api_url = self.api_url
        if self.api_type == "qwen" and not api_url.endswith("/chat/completions"):
            # 自动补全阿里云百炼的 endpoint
            if api_url.endswith("/compatible-mode/v1"):
                api_url = f"{api_url}/chat/completions"
            elif "dashscope" in api_url and not api_url.endswith("/v1/chat/completions"):
                api_url = f"{api_url}/chat/completions"

        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )

        if response.status_code != 200:
            try:
                resp_body = response.json()
                error_detail = resp_body.get("error", {}).get("message", str(resp_body))
            except:
                error_detail = response.text[:500] if response.text else "无响应内容"
            error_msg = f"API 返回错误：{response.status_code} - {error_detail}"
            raise Exception(error_msg)

        data = response.json()

        # 提取返回内容
        if "choices" not in data or not data["choices"]:
            raise Exception("API 返回格式错误：无 choices")

        content_text = data["choices"][0]["message"]["content"]
        logger.debug(f"[AI 分析] 返回内容：{content_text[:200]}...")

        # 解析 JSON
        return self._parse_ai_response(content_text)

    def _parse_ai_response(self, content_text: str) -> List[Dict]:
        """解析 AI 返回的 JSON 内容，转换为统一的日程格式"""
        try:
            # 尝试提取 JSON（处理可能的 markdown 包裹）
            json_str = content_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()

            data = json.loads(json_str)

            # 提取 events 数组
            events = data.get("events", [])
            if not isinstance(events, list):
                logger.warning(f"[AI 分析] events 不是数组：{type(events)}")
                return []

            # 转换为统一格式
            results = []
            for evt in events:
                if not isinstance(evt, dict):
                    continue
                time_str = evt.get("time", "")
                event_str = evt.get("event", "")
                if time_str and event_str:
                    results.append({
                        "时间原文": time_str,
                        "标准化时间": time_str,  # AI 返回的时间已经是自然语言
                        "事件内容": event_str,
                    })
                elif event_str:  # 只有事件内容，没有时间
                    results.append({
                        "时间原文": "未注明",
                        "标准化时间": "未注明",
                        "事件内容": event_str,
                    })

            return results if results else []

        except json.JSONDecodeError as e:
            logger.warning(f"[AI 分析] JSON 解析失败：{e}, 原始返回：{content_text[:200]}")
            return []
        except Exception as e:
            logger.warning(f"[AI 分析] 解析失败：{e}")
            return []


# ============================================================
#  第五步：时间提取模块（正则表达式模式）
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
    if re.match(
            r"^\s*(?:也 | 还 | 但 | 却 | 而 | 且 | 虽然 | 不过 | 然而 | 其实 | 但是 | 因此 | 所以 | 因为 | 由于 | 如果 | 假如 | 若)",
            event):
        return False
    if re.search(r"既.{0,8}也 | 既.{0,8}又 | 不是.{0,8}而是 | 没有.{0,8}也没有 | 虽然.{0,8}但 | 尽管.{0,8}但", event):
        return False
    if re.search(
            r"(?:开学 | 考试 | 放假 | 安排) 的 (?:惯例 | 时间 | 原因 | 规定 | 消息 | 说法 | 情况 | 结果 | 通知 | 内容 | 详情)",
            event):
        return False
    if not any(kw in event for kw in SCHEDULE_KEYWORDS):
        return False
    return True


def extract_time_events(text: str, article_date: Optional[datetime] = None,
                        mode: str = "regex", config: Optional[Dict] = None) -> List[Dict]:
    """
    从文章正文中提取「时间 + 事件」对（统一入口函数）

    Args:
        text: 文章正文
        article_date: 文章发布日期
        mode: 分析模式 ("regex" 或 "ai")
        config: 配置文件（AI 模式时需要）

    Returns:
        日程列表：[{"时间原文": "...", "标准化时间": "...", "事件内容": "..."}]
    """
    if mode == "ai" and config:
        # AI 模式
        analyzer = AIAnalyzer(config)
        return analyzer.analyze(text)
    else:
        # 正则模式（原有逻辑）
        if not text:
            return []
        if article_date is None:
            article_date = datetime.now()
        return _extract_time_events_regex(text, article_date)


def _extract_time_events_regex(text: str, article_date: datetime) -> List[Dict]:
    """从文章正文中提取「时间 + 事件」对（正则表达式模式）。"""
    if not text:
        return []

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

def format_markdown(articles: List[Article], analysis_mode: str = "regex") -> str:
    """
    将抓取结果格式化为 markdown

    Args:
        articles: 文章列表
        analysis_mode: 分析模式 ("regex" 或 "ai")
    """
    mode_name = "AI 大模型分析" if analysis_mode == "ai" else "正则表达式分析"
    lines = []
    lines.append("# 晚安华师日程信息抓取结果")
    lines.append(f"抓取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"分析模式：{mode_name}")
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


def print_console_output(articles: List[Article], analysis_mode: str = "regex"):
    """
    控制台输出

    Args:
        articles: 文章列表
        analysis_mode: 分析模式
    """
    mode_name = "AI 大模型分析" if analysis_mode == "ai" else "正则表达式分析"
    print()
    print("=" * 60)
    print("抓取结果")
    print("=" * 60)
    print(f"分析模式：{mode_name}")

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
    4. 读取已抓取记录，跳过已处理文章
    5. 抓取文章并校验
    6. 排序取最新 N 篇
    7. 提取日程
    8. 输出结果
    """
    # 加载配置文件
    print("\n[初始化] 读取配置文件...")
    config = load_config()
    analysis_mode = config.get("analysis_mode", "regex")
    print(f"  分析模式：{'AI 大模型分析' if analysis_mode == 'ai' else '正则表达式分析'}")
    if analysis_mode == "ai":
        if not config.get("ai_api_key"):
            print("  [警告] AI API Key 未配置，将降级到正则模式")
            analysis_mode = "regex"
        else:
            print(f"  AI 模型：{config.get('ai_model', 'unknown')}")

    print()
    print("=" * 60)
    print("华南师范大学「晚安华师」日程自动抓取工具 v6.2")
    print("=" * 60)
    print(f"目标网站：{NEWS_SCNU_EDU_URL}")
    print(f"输出文件：{OUTPUT_MARKDOWN_FILE}")
    print(f"目标获取：最新 {TARGET_ARTICLE_COUNT} 篇")
    print(f"分析模式：{'AI 大模型分析' if analysis_mode == 'ai' else '正则表达式分析'}")
    print()
    print("开始全自动抓取...")
    print("=" * 60)

    articles = []

    # 加载已抓取记录
    print("\n[初始化] 读取已抓取文章记录...")
    crawled_urls = load_crawled_urls()
    if crawled_urls:
        print(f"  已加载 {len(crawled_urls)} 条历史记录")
    else:
        print("  无历史记录（首次运行）")

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

    # Step 4: 抓取文章并校验（跳过已抓取）
    print(f"\n[Step 4/6] 抓取文章并校验（目标 {TARGET_ARTICLE_COUNT} 篇）...")
    for i, url in enumerate(wechat_links, 1):
        url_display = url[:60] + "..." if len(url) > 60 else url

        # 检查是否已抓取
        if url in crawled_urls:
            print(f"  [{i}/{len(wechat_links)}] [已抓取] 跳过文章：{url}")
            continue

        print(f"  [{i}/{len(wechat_links)}] [新文章] 开始处理：{url}")

        title, pub_date, source, content = extract_article_content(url)

        if not validate_article(title, source, content):
            print("    [跳过] 文章校验失败，不记录到已抓取列表")
            continue

        # 提取日程（使用配置的分析模式）
        article_date = datetime.now()
        if pub_date:
            try:
                article_date = datetime.strptime(pub_date[:10], "%Y-%m-%d")
            except ValueError:
                pass

        events = extract_time_events(content, article_date, mode=analysis_mode, config=config)

        article = Article(
            title=title,
            publish_date=pub_date,
            source=source or "微信公众号「晚安华师」",
            content=content,
            url=url,
            schedule_events=events
        )
        articles.append(article)

        # 记录到已抓取列表
        add_crawled_url(crawled_urls, url)
        print(f"    [成功] 标题={title[:30]}..., 日程={len(events)} 条，已记录到已抓取列表")

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
    print_console_output(articles, analysis_mode=analysis_mode)

    # 保存 markdown 文件
    markdown_content = format_markdown(articles, analysis_mode=analysis_mode)
    save_markdown(markdown_content, OUTPUT_MARKDOWN_FILE)

    print()
    print("=" * 60)
    print("抓取完成")
    print("=" * 60)
    print(f"成功抓取：{len(articles)} 篇文章")
    print(f"结果已保存到：{OUTPUT_MARKDOWN_FILE}")
    print(f"日志文件：{LOG_FILE}")
    print(f"已抓取记录：{CRAWLED_RECORD_FILE} (共 {len(crawled_urls)} 条)")

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
