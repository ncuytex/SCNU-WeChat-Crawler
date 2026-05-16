# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

华南师范大学「晚安华师」微信公众号日程自动抓取工具。Automatically crawls WeChat articles from SCNU news portal and extracts schedule events.

## Running

### Full Auto Crawler (v6.0, Recommended)

```bash
python src/auto_scnu_crawler.py
```

- Zero-interaction, fully automated
- Visits https://news.scnu.edu.cn/ automatically
- Detects 302 redirects, filters only WeChat links
- Fetches latest 2 articles, extracts schedules
- Output: console + `wechat_schedule_output.md`

### Manual Crawler (v5.0, Fallback)

```bash
python src/scnu_wechat_crawler.py
```

- Manual URL input loop
- Paste `mp.weixin.qq.com` URLs, press Enter
- Type `q` to quit

## Setup

```bash
pip install -r requirements.txt
```

## Architecture (auto_scnu_crawler.py v6.0)

Seven-step pipeline:

1. **`fetch_news_page()`** — Fetches SCNU news homepage with browser headers
2. **`extract_article_links()`** — Extracts all `<a>` hrefs from HTML
3. **`filter_wechat_links()`** — Detects 302 redirects, keeps only `mp.weixin.qq.com` targets
4. **`extract_article_content()`** — Three-layer fallback:
   - Direct request with WeChat UA (MicroMessenger/7.0.20.1781)
   - wechat-article-extractor subprocess (if configured)
   - Fallback API: `down.mptext.top/api/public/v1/download`
5. **`validate_article()`** — Checks title length, content length (≥500), source contains "晚安华师"
6. **`extract_time_events()`** — Regex patterns for Chinese date expressions + schedule keywords
7. **Output** — `format_markdown()` + `save_markdown()` + `print_console_output()`

### Time Extraction Patterns

- Full dates: `2026 年 3 月 15 日`
- Month-day: `3 月 15 日`
- Month-period: `3 月上旬`, `3 月中旬`, `3 月下旬`
- Weekdays: `本周五`, `下周三`, `星期一下午`
- Relative dates resolved against `article_date`

### Schedule Validation

Lines identified by structure (bullets, numbered lists, date prefixes). Events validated against `SCHEDULE_KEYWORDS` tuple (开学，放假，考试，报名，截止，etc.).

## Key Files

| File | Purpose |
|------|---------|
| `src/auto_scnu_crawler.py` | Main auto crawler (v6.0) |
| `src/scnu_wechat_crawler.py` | Manual URL input crawler (v5.0) |
| `requirements.txt` | Dependencies |
| `output/wechat_schedule_output.md` | Output: article details + schedule summary |
| `logs/scnu_auto_crawler.log` | Runtime log |

## Important Details

- **WeChat UA Required**: All requests must include `MicroMessenger` in User-Agent — WeChat blocks non-WeChat browsers
- **Redirect Detection**: Does not follow redirects; reads `Location` header to detect WeChat links
- **Fetch Delay**: 2-second delay between requests to avoid rate limiting
- **Source Validation**: Only accepts articles where source contains "晚安华师"

## Configurable Parameters (top of auto_scnu_crawler.py)

```python
TARGET_ARTICLE_COUNT = 2      # Number of articles to fetch
FETCH_DELAY = 2               # Request interval (seconds)
MIN_CONTENT_LENGTH = 500      # Minimum content length
API_TIMEOUT = 15              # API timeout (seconds)
```

## Dependencies

```
requests>=2.28.0      # HTTP requests
beautifulsoup4>=4.11.0  # HTML parsing
lxml>=4.9.0           # BeautifulSoup parser backend
```
