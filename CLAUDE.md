# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

华南师范大学「晚安华师」微信公众号日程自动抓取工具。Automatically crawls WeChat articles from SCNU news portal and extracts schedule events.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run auto crawler (recommended)
python src/auto_scnu_crawler.py

# Run manual crawler (fallback)
python src/scnu_wechat_crawler.py
```

## Architecture

### Crawler Pipeline (auto_scnu_crawler.py v6.4)

```
fetch_news_page() → extract_article_links() → filter_wechat_links() 
    → extract_article_content() → validate_article() → extract_time_events() → Output
```

| Step | Function | Description |
|------|----------|-------------|
| 1 | `fetch_news_page()` | Fetches SCNU news homepage with browser headers |
| 2 | `extract_article_links()` | Extracts all `<a>` hrefs from HTML |
| 3 | `filter_wechat_links()` | Detects 302 redirects, keeps only `mp.weixin.qq.com` |
| 4 | `extract_article_content()` | Three-layer fallback: direct request → extractor subprocess → API |
| 5 | `validate_article()` | Checks title/content length, source contains "晚安华师" |
| 6 | `extract_time_events()` | Regex or AI mode for schedule extraction |
| 7 | Output | `format_markdown()` + `save_markdown()` + `print_console_output()` |

### AI Analysis Module (v6.2+)

```python
class AIAnalyzer:
    """Supports DeepSeek, OpenAI, Claude, Qwen APIs"""
    def analyze(self, content: str) -> List[Dict]:
        # Returns: [{"时间原文": "...", "标准化时间": "...", "事件内容": "..."}]
```

- Config file: `config.json` (not committed, see `config.example.json`)
- Auto-fallback: AI failure → regex mode
- Error output: Full API error messages including response body

### Time Extraction Patterns

- Full dates: `2026 年 3 月 15 日` → `2026-03-15`
- Month-day: `3 月 15 日` → `2026-03-15`
- Month-period: `3 月上旬/中旬/下旬` → `2026-03-05/15/25`
- Weekdays: `本周五`/`下周三` → calculated from article date

## Key Files

| File | Purpose |
|------|---------|
| `src/auto_scnu_crawler.py` | Main auto crawler (v6.4) |
| `src/scnu_wechat_crawler.py` | Manual URL input crawler (v5.0) |
| `config.example.json` | Config template (safe to commit) |
| `config.json` | Real config with API keys (gitignored) |
| `output/wechat_schedule_output.md` | Output markdown |
| `logs/scnu_auto_crawler.log` | Runtime log |
| `logs/crawled_urls.txt` | Deduplication records |

## Important Details

- **WeChat UA**: `MicroMessenger/7.0.20.1781` required for all WeChat requests
- **Redirect Detection**: Does not follow redirects; reads `Location` header
- **Fetch Delay**: 2-second delay between requests
- **Source Validation**: Only accepts articles where source contains "晚安华师"
- **Deduplication**: Crawled URLs persisted to `logs/crawled_urls.txt`

## Development

```bash
# Syntax check
python -m py_compile src/auto_scnu_crawler.py

# Import test
python -c "from src.auto_scnu_crawler import load_config, AIAnalyzer, extract_time_events"

# Run with custom config
python src/auto_scnu_crawler.py
```

## Configurable Parameters

```python
# In auto_scnu_crawler.py
TARGET_ARTICLE_COUNT = 2      # Articles to fetch
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
