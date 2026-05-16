# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WeChat article (微信公众号文章) schedule extractor. Interactive tool that extracts time+event pairs from WeChat MP article URLs and saves them to CSV.

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
python wechat_crawler.py
```

Program starts an interactive prompt. Paste a WeChat article URL and press Enter to extract schedule info. Type `q` to quit.

## Architecture (single-file: `wechat_crawler.py`)

- **`fetch_article(url)`** — Fetches a single article via `requests` with MicroMessenger User-Agent, parses HTML with BeautifulSoup to extract title, content, and publish time.
- **`extract_time_events()`** — Regex-based extraction of Chinese date expressions (年月日，月日，上/中/下旬，周/星期) paired with following text as events. Standardizes dates relative to article publish date.
- **`save_events()`** — Appends events to CSV with MD5-based deduplication.
- **`process_url()`** — Pipeline for a single URL: fetch → extract → save → print results.
- **`main()`** — Interactive input loop. Reads URLs from stdin until user quits.

## Key Files

| File | Purpose |
|------|---------|
| `events.csv` | Output: deduplicated time+event records |
| `crawler.log` | Application log |

## Important Details

- The User-Agent must include `MicroMessenger` — WeChat's article pages block non-WeChat browsers.
- Time extraction handles relative dates (本周三，下周五) resolved against `article_date` from the publish timestamp.

## Dependencies

```
requests>=2.28.0      # HTTP requests to WeChat MP
beautifulsoup4>=4.11.0  # HTML parsing
lxml>=4.9.0           # BeautifulSoup parser backend
```

## URL Validation

Only processes URLs containing `mp.weixin.qq.com` — rejects all others.

## New: SCNU WeChat Crawler (scnu_wechat_crawler.py)

v5.0 - 华南师范大学「晚安华师」微信公众号日程自动抓取工具

### Features

- Manual WeChat article URL input
- Auto-extraction of article content with WeChat UA bypass
- Intelligent schedule event extraction
- Data validation (source, title, content length)
- Fallback API verification (fetcher API)
- Multi-format output (console + markdown)

### Running

```bash
python scnu_wechat_crawler.py
```

### Output

- Console: Article title, date, source, extracted schedule events
- File: `wechat_schedule_output.md` (markdown with full article details + schedule summary)

### Key Differences from wechat_crawler.py

| wechat_crawler.py | scnu_wechat_crawler.py |
|-------------------|------------------------|
| CSV output | Markdown output |
| Simple time+event extraction | Full article content + schedule summary |
| Basic validation | Multi-layer validation + fallback API |
| Direct WeChat URL only | Same, with better error handling |
