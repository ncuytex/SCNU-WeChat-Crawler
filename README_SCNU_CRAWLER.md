# 华南师范大学「晚安华师」微信公众号日程抓取工具

## 项目概述

自动抓取微信公众号「晚安华师」推文，并提取推文中的日程信息的 Python 工具。

## 功能特性

1. **手动输入文章链接** - 支持输入任意微信公众号文章链接
2. **自动提取正文** - 使用微信 UA 绕过安全策略，自动提取文章标题、发布日期、来源和正文
3. **智能日程识别** - 从文章正文中智能识别并抽取日程信息（会议、活动、时间、地点、事项等）
4. **数据校验** - 来源、标题、正文长度自动校验
5. **兜底校验** - 集成 fetcher API 做交叉验证
6. **多格式输出** - 控制台打印 + markdown 文件保存

## 安装依赖

```bash
pip install -r requirements.txt
```

依赖列表：
- `requests>=2.28.0` - HTTP 请求
- `beautifulsoup4>=4.11.0` - HTML 解析
- `lxml>=4.9.0` - BeautifulSoup 解析器后端

## 运行方法

```bash
python scnu_wechat_crawler.py
```

程序启动后：
1. 输入微信公众号文章链接（mp.weixin.qq.com/s/xxx）
2. 按回车开始处理
3. 可继续输入更多链接
4. 输入 `q` 退出

## 输出示例

### 控制台输出

```
[成功] 抓取到「晚安华师」最新文章 1：
标题：393 位获奖！下一个，就是你！
发布日期：2026-04-28
来源：微信公众号「晚安华师」
提取日程信息：无相关日程
```

### 本地文件

`wechat_schedule_output.md` - 包含文章详情和日程汇总的 markdown 文件

## 可配置参数

在 `scnu_wechat_crawler.py` 文件开头可配置以下参数：

```python
# 提取脚本路径（如有本地 wechat-article-extractor 则配置）
WECHAT_ARTICLE_EXTRACTOR_PATH = None

# 兜底 API 地址
FETCHER_API_URL = "https://down.mptext.top/api/public/v1/download"

# 正文最小长度阈值
MIN_CONTENT_LENGTH = 500

# 请求间隔（秒）
FETCH_DELAY = 1

# API 超时时间（秒）
API_TIMEOUT = 10

# 输出文件路径
OUTPUT_MARKDOWN_FILE = "wechat_schedule_output.md"

# 日志文件路径
LOG_FILE = "scnu_crawler.log"
```

## 注意事项

1. **新发布文章同步延迟** - 新发布的文章需等待 10-30 分钟才能被抓取
2. **微信安全策略** - 程序自动使用微信 UA（MicroMessenger）绕过安全检测
3. **fetcher API 稳定性** - 兜底 API 不稳定，仅用于校验，不作为主流程
4. **链接格式** - 必须输入完整的微信公众号文章链接（mp.weixin.qq.com 域名）

## 规避的反爬措施

1. ✅ 使用微信 UA（MicroMessenger/7.0.20.1781）
2. ✅ 不直接裸请求 mp.weixin.qq.com
3. ✅ 请求间隔控制（FETCH_DELAY）
4. ✅ 禁用图片视觉解析（--no-vision）
5. ✅ 不使用搜狗微信搜索（避免反爬、数据陈旧）

## 文件说明

| 文件 | 说明 |
|------|------|
| `scnu_wechat_crawler.py` | 主程序 |
| `requirements.txt` | 依赖列表 |
| `wechat_schedule_output.md` | 输出文件 |
| `scnu_crawler.log` | 日志文件 |

## 版本历史

- **v5.0** - 手动输入链接版本，稳定可靠
- **v4.x** - 尝试从新闻网自动抓取（因链接结构问题已弃用）

## 获取文章链接的方法

1. 在微信中打开「晚安华师」公众号文章
2. 点击右上角「...」
3. 选择「复制链接」
4. 粘贴到程序中

或者从华南师范大学新闻网（https://news.scnu.edu.cn/）中找到相关文章，点击后从跳转后的 URL 获取微信链接。
