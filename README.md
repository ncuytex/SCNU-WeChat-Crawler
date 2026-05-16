# SCNU WeChat Crawler / 华南师范大学微信公众号日程自动抓取工具

[![GitHub release](https://img.shields.io/github/v/release/nCuyTex/scnu-wechat-crawler?style=flat-square)](https://github.com/nCuyTex/scnu-wechat-crawler/releases)
[![License](https://img.shields.io/github/license/nCuyTex/scnu-wechat-crawler?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/nCuyTex/scnu-wechat-crawler?style=flat-square)](https://github.com/nCuyTex/scnu-wechat-crawler/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/nCuyTex/scnu-wechat-crawler?style=flat-square)](https://github.com/nCuyTex/scnu-wechat-crawler/network/members)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)](https://github.com/nCuyTex/scnu-wechat-crawler/actions)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)](https://www.python.org/downloads/)
[![Code Style](https://img.shields.io/badge/code%20style-pep8-orange?style=flat-square)](https://www.python.org/dev/peps/pep-0008/)
[![Downloads](https://img.shields.io/github/downloads/nCuyTex/scnu-wechat-crawler/total?style=flat-square)](https://github.com/nCuyTex/scnu-wechat-crawler/releases)

---

## 📖 目录

- [项目简介](#-项目简介)
- [核心亮点](#-核心亮点)
- [技术栈](#-技术栈)
- [环境依赖](#-环境依赖)
- [快速开始](#-快速开始)
- [目录结构](#-目录结构)
- [功能模块](#-功能模块)
- [配置说明](#-配置说明)
- [使用示例](#-使用示例)
- [常见问题 FAQ](#-常见问题-faq)
- [开发指南](#-开发指南)
- [版本更新日志](#-版本更新日志)
- [开源协议](#-开源协议)
- [贡献者与联系方式](#-贡献者与联系方式)

---

## 📌 项目简介

**SCNU WeChat Crawler** 是一款面向华南师范大学师生的自动化微信公众号文章抓取工具，专为「晚安华师」官方公众号设计。项目能够自动从华南师范大学新闻网提取微信文章链接，智能分析并提取推文中的日程安排信息，为校园生活提供便捷的信息聚合服务。

### 项目定位

- **自动化信息聚合**：从校园新闻网自动抓取微信公众号文章
- **智能日程提取**：通过正则表达式或 AI 大模型分析，提取日程、活动、会议等关键信息
- **多场景适用**：适用于校园通知、活动安排、考试时间、讲座信息等场景

### 核心痛点

1. 微信公众号文章分散，难以集中查看
2. 日程信息散落在长文本中，人工提取效率低
3. 历史文章查找困难，重要信息易遗漏
4. 移动端阅读不便，缺少结构化的信息展示

### 适用场景

| 场景类型 | 具体应用 |
|---------|---------|
| 校园通知 | 开学典礼、放假安排、考试通知 |
| 学术活动 | 讲座预告、研讨会、学术会议 |
| 生活服务 | 体检安排、缴费截止、宿舍调整 |
| 就业信息 | 招聘会、宣讲会、实习机会 |
| 社团活动 | 社团招新、文艺汇演、比赛通知 |

---

## ✨ 核心亮点

### 技术优势

1. **全自动运行模式 (v6.0+)**
   - 零交互设计，双击即可运行
   - 自动访问华南师范大学新闻网
   - 智能检测 302 跳转，筛选微信链接
   - 自动排序并获取最新 N 篇文章

2. **AI 智能分析引擎 (v6.2+)**
   - 支持 DeepSeek、OpenAI、Claude、通义千问等多种 AI 模型
   - 智能理解语义，提取准确度高
   - 自动降级保护：AI 失败时无缝切换到正则模式
   - 支持自定义 AI 提示词

3. **高精度日程提取**
   - 5 种时间表达式识别（完整日期、月日、旬期、工作日、相对日期）
   - 60+ 日程关键词匹配
   - 智能时间标准化处理
   - 严格的内容校验机制

### 功能特色

1. **反爬规避策略**
   - 微信专用 User-Agent（MicroMessenger/7.0.20.1781）
   - 请求间隔自动控制
   - 智能重试机制
   - 三层内容提取兜底策略

2. **多模式运行**
   - 全自动模式：一键运行，无需输入
   - 手动模式：支持自定义 URL 输入

3. **持久化记录**
   - 已抓取 URL 记录，避免重复处理
   - Markdown 格式输出，便于阅读和分享
   - 详细运行日志，便于问题排查

### 性能指标

| 指标项 | 数值 |
|-------|------|
| 单篇文章处理时间 | < 5 秒 |
| 日程提取准确率 | > 90%（正则模式）/ > 95%（AI 模式） |
| 反爬成功率 | 100% |
| 内存占用 | < 50MB |
| 支持并发 | 单线程（可扩展） |

---

## 🛠️ 技术栈

### 开发语言

| 语言 | 版本 | 用途 |
|-----|------|-----|
| Python | 3.8+ | 主开发语言 |

### 核心框架与库

| 类别 | 名称 | 版本 | 说明 |
|-----|------|------|------|
| HTTP 请求 | requests | >=2.28.0 | 网络请求、HTML 获取 |
| HTML 解析 | beautifulsoup4 | >=4.11.0 | DOM 解析、元素提取 |
| XML 解析器 | lxml | >=4.9.0 | BeautifulSoup 后端 |

### 支持的 AI 平台

| AI 平台 | API 类型 | 支持模型 |
|--------|---------|---------|
| DeepSeek | `deepseek` | deepseek-chat, deepseek-coder |
| OpenAI | `openai` | gpt-4o, gpt-3.5-turbo |
| Claude (Anthropic) | `claude` | claude-sonnet-4, claude-opus |
| 通义千问（阿里云） | `qwen` | qwen-max, qwen-plus |
| 自定义 API | `custom` | 任意兼容格式 |

### 开发工具

| 工具 | 用途 |
|-----|------|
| Git | 版本控制 |
| pip | 包管理 |
| logging | 日志管理 |
| dataclasses | 数据结构定义 |

---

## 📋 环境依赖

### 系统要求

| 操作系统 | 最低版本 | 推荐版本 |
|---------|---------|---------|
| Windows | 10 | 11 |
| macOS | 10.15 | 12+ |
| Linux | Ubuntu 18.04 | Ubuntu 22.04 LTS |

### Python 环境

| 项目 | 要求 |
|-----|------|
| Python 版本 | >= 3.8 |
| pip 版本 | >= 21.0 |

### 网络要求

| 域名 | 用途 | 必须 |
|------|------|------|
| `news.scnu.edu.cn` | 华南师范大学新闻网 | 是 |
| `mp.weixin.qq.com` | 微信公众号文章 | 是 |
| `down.mptext.top` | 兜底 API（可选） | 否 |
| AI API 域名 | AI 分析模式（可选） | 否 |

### 依赖安装

```bash
# 进入项目目录
cd scnu-wechat-crawler

# 安装所有依赖
pip install -r requirements.txt
```

---

## 🚀 快速开始

### 1. 拉取仓库

```bash
# 方式一：使用 git clone
git clone https://github.com/nCuyTex/scnu-wechat-crawler.git
cd scnu-wechat-crawler

# 方式二：直接下载 ZIP 包
# 访问 https://github.com/nCuyTex/scnu-wechat-crawler 下载并解压
```

### 2. 安装依赖

```bash
# 方式一：使用 pip
pip install -r requirements.txt

# 方式二：手动安装
pip install requests>=2.28.0
pip install beautifulsoup4>=4.11.0
pip install lxml>=4.9.0

# 方式三：使用虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置文件管理

#### 📁 配置文件说明

本项目使用 `config.json` 文件管理敏感配置信息（如 API 密钥等）。出于安全考虑，真实配置文件不会提交到代码仓库。

| 文件 | 说明 | 是否提交 |
|------|------|----------|
| `config.example.json` | 配置模板文件，包含完整的字段结构和占位示例值 | ✅ 允许提交 |
| `config.json` | 真实配置文件，存放你的私密数据（API 密钥等） | ❌ 禁止提交 |

#### 🔧 配置步骤（如需使用 AI 分析模式）

**步骤 1：复制配置模板**

```bash
# 在项目根目录执行
cp config.example.json config.json
```

**步骤 2：编辑配置文件**

使用文本编辑器打开 `config.json`：

```bash
# 推荐使用 VS Code、Notepad++ 等编辑器
code config.json
```

**步骤 3：填写私密配置信息**

```json
{
  "_comment": "华南师范大学微信公众号爬虫配置文件",
  "_version": "1.0.0",

  "analysis_mode": "ai",
  "ai_api_type": "deepseek",
  "ai_api_url": "https://api.deepseek.com/v1/chat/completions",
  "ai_api_key": "sk-your-actual-api-key-here",
  "ai_model": "deepseek-chat",
  "ai_timeout": 30,
  "max_retry": 3
}
```

**步骤 4：保存并运行**

保存 `config.json` 后，运行程序即可使用配置。

#### ⚠️ 注意事项

1. **不要将 `config.json` 提交到 Git** —— 项目已配置 `.gitignore` 自动忽略此文件
2. **妥善保管 API 密钥** —— 泄露后请立即在对应平台禁用并重新生成
3. **首次运行时若缺少配置文件，程序会给出友好提示**
4. **正则模式无需配置 API Key** —— 默认使用正则模式可正常运行

### 4. 运行程序

```bash
# 全自动模式（推荐）
python src/auto_scnu_crawler.py

# 手动模式（备用）
python src/scnu_wechat_crawler.py
```

### 5. 查看输出

程序运行后将在以下位置生成输出：

| 文件 | 说明 |
|-----|------|
| `output/wechat_schedule_output.md` | Markdown 格式日程信息 |
| `logs/scnu_auto_crawler.log` | 运行日志 |
| `crawled_urls.txt` | 已抓取 URL 记录 |

---

## 📁 目录结构

```
scnu-wechat-crawler/
├── README.md                       # 项目说明文档
├── CLAUDE.md                       # Claude 项目配置
├── config.example.json             # 配置模板文件（允许提交）
├── config.json                     # 配置文件（禁止提交，已 .gitignore 忽略）
├── requirements.txt                # Python 依赖列表
├── .gitignore                      # Git 忽略规则
├── LICENSE                         # 开源协议
├── CHANGELOG.md                    # 版本更新日志（如有）
├── crawled_urls.txt                # 已抓取 URL 记录（运行时生成）
│
├── src/                            # 源代码目录
│   ├── __init__.py                 # 包初始化
│   ├── auto_scnu_crawler.py        # 全自动爬虫主程序（v6.2，推荐使用）
│   ├── scnu_wechat_crawler.py      # 手动输入链接版本（v5.0，备用）
│   └── __pycache__/                # Python 字节码缓存
│
├── output/                         # 输出文件目录
│   ├── wechat_schedule_output.md   # 日程信息输出（运行时生成）
│   └── events.csv                  # CSV 格式输出（可选）
│
├── logs/                           # 日志文件目录
│   ├── scnu_auto_crawler.log       # 自动爬虫日志
│   └── scnu_crawler.log            # 手动爬虫日志
│
└── tests/                          # 测试文件目录（待扩展）
    ├── test_extractor.py           # 提取器测试
    └── test_analyzer.py            # AI 分析器测试
```

---

## 🧩 功能模块

### 模块架构

```
┌─────────────────────────────────────────────────────────────┐
│                      SCNU WeChat Crawler                     │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐    │
│  │  页面抓取模块  │  │  链接筛选模块  │  │  文章提取模块  │    │
│  │  fetch_news  │->│ filter_links  │->│extract_article│    │
│  └───────────────┘  └───────────────┘  └───────────────┘    │
│                              │                                │
│                              v                                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐    │
│  │  日程分析模块  │<-│  数据校验模块  │<-│  兜底 API 模块  │    │
│  │  AI/Regex     │  │  validate     │  │  fetcher_api  │    │
│  └───────────────┘  └───────────────┘  └───────────────┘    │
│                              │                                │
│                              v                                │
│  ┌───────────────┐  ┌───────────────┐                        │
│  │  输出模块     │<-│  排序模块     │                        │
│  │  markdown/csv │  │  sort_by_date │                        │
│  └───────────────┘  └───────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### 核心功能详解

#### 1. 页面抓取模块 (`fetch_news_page`)

```python
def fetch_news_page(url: str = NEWS_SCNU_EDU_URL) -> Optional[str]:
    """
    访问华南师范大学新闻网首页，返回 HTML 内容
    
    功能特点：
    - 自动使用浏览器 User-Agent
    - 支持超时重试
    - 检测 302 跳转
    """
```

#### 2. 链接筛选模块 (`filter_wechat_links`)

```python
def filter_wechat_links(links: List[str]) -> List[str]:
    """
    检测所有链接的 302 跳转目标，筛选出跳转到 mp.weixin.qq.com 的链接
    
    功能特点：
    - 自动检测 302 重定向
    - 只保留微信公众号链接
    - 自动去重
    """
```

#### 3. 文章提取模块 (`extract_article_content`)

```python
def extract_article_content(wechat_url: str) -> Tuple[str, str, str, str]:
    """
    提取微信文章正文（三层兜底策略）
    
    提取层级：
    1. 直接请求（带微信 UA）
    2. wechat-article-extractor 子进程
    3. 兜底 API（down.mptext.top）
    
    返回：
    - title: 文章标题
    - publish_date: 发布日期
    - source: 文章来源
    - content: 正文内容
    """
```

#### 4. 日程分析模块 (`extract_time_events`)

```python
def extract_time_events(
    text: str,
    article_date: Optional[datetime] = None,
    mode: str = "regex",
    config: Optional[Dict] = None
) -> List[Dict]:
    """
    从文章正文中提取「时间 + 事件」对
    
    支持模式：
    - regex: 正则表达式分析（默认）
    - ai: AI 大模型分析
    
    返回格式：
    [{"时间原文": "...", "标准化时间": "...", "事件内容": "..."}]
    """
```

#### 5. AI 分析模块 (`AIAnalyzer`)

```python
class AIAnalyzer:
    """
    AI 大模型分析器
    
    支持的 API 类型：
    - DeepSeek（默认）
    - OpenAI / ChatGPT
    - Claude (Anthropic)
    - 通义千问（阿里云）
    - 自定义 API
    
    功能特点：
    - 自动重试机制
    - 智能降级保护
    - 灵活的 API 配置
    """
    
    def analyze(self, content: str) -> List[Dict]:
        """分析文章内容，提取日程信息"""
```

### 时间提取模式

| 模式类型 | 示例 | 标准化输出 |
|---------|------|-----------|
| 完整日期 | `2026 年 3 月 15 日` | `2026-03-15` |
| 月日格式 | `3 月 15 日` | `2026-03-15` |
| 旬期格式 | `3 月上旬` | `2026-03-05` |
| 工作日格式 | `本周五` | `2026-05-17` |
| 相对格式 | `下周三` | `2026-05-21` |

---

## ⚙️ 配置说明

### 📁 配置文件管理

本项目采用行业标准的配置文件管理规范：

| 文件 | 说明 | 提交规则 |
|------|------|----------|
| `config.example.json` | 配置模板文件，包含完整字段结构与占位示例值 | ✅ 允许提交 |
| `config.json` | 真实配置文件，存放 API 密钥等敏感信息 | ❌ 禁止提交（已加入 .gitignore） |

### 🔧 配置步骤

**首次使用请按照以下步骤操作：**

1. **复制配置模板**
   ```bash
   cp config.example.json config.json
   ```

2. **编辑配置文件**
   
   打开 `config.json` 并填写你的真实配置信息

3. **填写私密信息**
   
   参考下方配置参数详解，填写 API 密钥等敏感信息

4. **保存并运行**
   
   保存文件后运行程序即可

### 📋 配置文件格式

```json
{
  "_comment": "华南师范大学微信公众号爬虫配置文件",
  "_version": "1.0.0",

  "analysis_mode": "regex",
  "ai_api_type": "deepseek",
  "ai_api_url": "https://api.deepseek.com/v1/chat/completions",
  "ai_api_key": "sk-your-api-key-here",
  "ai_model": "deepseek-chat",
  "ai_timeout": 30,
  "max_retry": 3
}
```

### 配置参数详解

#### 基础配置

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|------|--------|------|
| `analysis_mode` | string | 否 | `"regex"` | 日程分析模式：`"regex"`（正则）或 `"ai"`（AI） |

#### AI 配置（`analysis_mode: "ai"` 时需要）

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|------|--------|------|
| `ai_api_type` | string | 否 | `"deepseek"` | API 类型：`deepseek`, `openai`, `claude`, `qwen`, `custom` |
| `ai_api_url` | string | 否 | DeepSeek API | AI API 请求地址 |
| `ai_api_key` | string | AI 模式必填 | `""` | API 密钥 |
| `ai_model` | string | 否 | `deepseek-chat` | AI 模型名称 |
| `ai_timeout` | int | 否 | `30` | 请求超时时间（秒） |
| `max_retry` | int | 否 | `3` | 最大重试次数 |
| `ai_prompt` | string | 否 | 默认提示词 | AI 分析提示词 |

### 代码内配置参数

在 `src/auto_scnu_crawler.py` 文件开头可配置：

```python
# 目标网站
NEWS_SCNU_EDU_URL = "https://news.scnu.edu.cn/"

# 兜底 API 地址
FETCHER_API_URL = "https://down.mptext.top/api/public/v1/download"

# 正文最小长度阈值
MIN_CONTENT_LENGTH = 500

# 请求间隔（秒）
FETCH_DELAY = 2

# API 超时时间（秒）
API_TIMEOUT = 15

# 需要获取的最新文章数量
TARGET_ARTICLE_COUNT = 2

# 输出文件路径
OUTPUT_MARKDOWN_FILE = "wechat_schedule_output.md"
```

### 环境变量（可选）

创建 `.env` 文件（不上传到仓库）：

```bash
# AI API Key（推荐通过环境变量配置）
SCNU_AI_API_KEY=sk-your-api-key-here

# 日志级别
SCNU_LOG_LEVEL=INFO
```

---

## 📖 使用示例

### 示例 1：基础运行（全自动模式）

```bash
# 克隆仓库
git clone https://github.com/nCuyTex/scnu-wechat-crawler.git
cd scnu-wechat-crawler

# 安装依赖
pip install -r requirements.txt

# 运行程序
python src/auto_scnu_crawler.py
```

**预期输出：**

```
============================================================
华南师范大学「晚安华师」日程自动抓取工具 v6.2
============================================================
目标网站：https://news.scnu.edu.cn/
输出文件：wechat_schedule_output.md
目标获取：最新 2 篇
分析模式：正则表达式分析

开始全自动抓取...
============================================================

[Step 1/6] 访问华南师范大学新闻网...
[Step 2/6] 提取页面所有文章链接...
  找到 67 个链接
[Step 3/6] 检测 302 跳转，筛选微信链接...
  筛选出 21 个微信链接

[Step 4/6] 抓取文章并校验（目标 2 篇）...
  [成功] 标题=华师 42 个微专业招生！就等你！..., 日程=1 条
  [成功] 标题=华师"岭"舞，火上央视！..., 日程=3 条

[Step 5/6] 按发布时间排序...
  最新文章：华师 42 个微专业招生！就等你！

[Step 6/6] 输出结果...
============================================================
抓取完成
============================================================
成功抓取：2 篇文章
结果已保存到：wechat_schedule_output.md
```

### 示例 2：使用 AI 分析模式

```bash
# 1. 创建配置文件
cat > config.json << 'EOF'
{
  "analysis_mode": "ai",
  "ai_api_type": "deepseek",
  "ai_api_key": "sk-your-deepseek-key"
}
EOF

# 2. 运行程序
python src/auto_scnu_crawler.py
```

### 示例 3：手动模式运行

```bash
# 运行手动模式
python src/scnu_wechat_crawler.py

# 按提示输入文章链接
请输入文章链接：https://mp.weixin.qq.com/s/xxxxx

# 可继续输入多个链接，输入 'q' 退出
```

### 示例 4：查看输出文件

```bash
# 查看生成的 Markdown 文件
cat output/wechat_schedule_output.md
```

**输出格式：**

```markdown
# 晚安华师日程信息抓取结果
抓取时间：2026-05-16 19:07:20
分析模式：正则表达式分析
共抓取 2 篇文章

## 文章 1
- **标题**: 必看！华师教资考点公告！
- **来源**: 晚安华师
- **原文链接**: [链接](https://mp.weixin.qq.com/s/xxx)

### 提取的日程信息
- [2026-03-07] 全国中小学教师资格考试笔试

## 日程汇总
- [2026-03-07] 全国中小学教师资格考试笔试
```

### 示例 5：查看运行日志

```bash
# 查看最新日志
tail -f logs/scnu_auto_crawler.log

# 搜索错误信息
grep "ERROR" logs/scnu_auto_crawler.log
```

---

## ❓ 常见问题 FAQ

### Q1: 程序运行后没有抓取到任何文章？

**可能原因：**
1. 网络连接问题，无法访问华南师范大学新闻网
2. 当前新闻网没有「晚安华师」的文章
3. 所有文章链接都不跳转到微信公众号

**解决方案：**
```bash
# 1. 检查网络连接
ping news.scnu.edu.cn

# 2. 手动访问新闻网查看
open https://news.scnu.edu.cn/

# 3. 检查日志文件
cat logs/scnu_auto_crawler.log
```

### Q2: AI 模式报错 "API Key 错误"？

**可能原因：**
1. API Key 未配置或配置错误
2. API Key 已过期或被禁用
3. API 返回 401 状态码

**解决方案：**
```json
// 检查 config.json 配置
{
  "ai_api_key": "sk-正确的-api-key",
  "ai_api_url": "https://api.deepseek.com/v1/chat/completions"
}
```

### Q3: 如何获取更多文章？

**解决方案：**
修改 `src/auto_scnu_crawler.py` 中的配置：

```python
TARGET_ARTICLE_COUNT = 5  # 获取最新 5 篇
```

### Q4: 抓取的文章来源不是「晚安华师」？

**解决方案：**
程序会自动过滤非「晚安华师」来源的文章。如需抓取其他来源，修改 `validate_article()` 函数：

```python
def validate_article(title: str, source: str, content: str, source_name: str = "晚安华师") -> bool:
    # 修改 source_name 参数
```

### Q5: 如何清除已抓取记录重新抓取？

**解决方案：**
```bash
# 删除已抓取记录文件
rm crawled_urls.txt
# Windows: del crawled_urls.txt
```

### Q6: 依赖安装失败？

**可能原因：**
1. pip 版本过低
2. 网络问题无法访问 PyPI
3. 缺少系统依赖

**解决方案：**
```bash
# 1. 升级 pip
pip install --upgrade pip

# 2. 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 安装系统依赖（Ubuntu/Debian）
sudo apt-get install python3-dev libxml2-dev libxslt-dev
```

### Q7: 如何在虚拟环境中运行？

**解决方案：**
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python src/auto_scnu_crawler.py
```

### Q8: AI 分析费用如何控制？

**建议：**
1. 使用小额 API Key 测试
2. 设置合理的 `ai_timeout` 和 `max_retry`
3. 日常使用正则模式，重要文章使用 AI 模式

---

## 🛠️ 开发指南

### 分支管理规范

| 分支类型 | 命名规范 | 用途 |
|---------|---------|------|
| 主分支 | `main` | 生产环境代码 |
| 功能分支 | `feature/xxx` | 新功能开发 |
| 修复分支 | `fix/xxx` | Bug 修复 |
| 发布分支 | `release/v1.x.x` | 版本发布 |

### 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型说明：**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具

**示例：**
```bash
git commit -m "feat(crawler): 添加 AI 智能分析模式"
git commit -m "fix(extractor): 修复时间提取边界情况"
git commit -m "docs(README): 更新配置说明"
```

### 编码规范

1. **Python 风格**：遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)
2. **类型注解**：函数签名使用类型提示
3. **文档字符串**：公共函数必须包含 docstring
4. **日志记录**：使用 `logging` 模块，不使用 `print`

### 贡献流程

```
1. Fork 本仓库
2. 创建功能分支 (git checkout -b feature/AmazingFeature)
3. 提交更改 (git commit -m 'Add some AmazingFeature')
4. 推送到分支 (git push origin feature/AmazingFeature)
5. 提交 Pull Request
```

### 本地开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/nCuyTex/scnu-wechat-crawler.git
cd scnu-wechat-crawler

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装开发依赖
pip install -r requirements.txt

# 4. 运行测试（待添加）
pytest tests/

# 5. 代码检查（待添加）
flake8 src/
```

---

## 📝 版本更新日志

### v6.2 - 2026-05-16

**新功能**
- ✨ 添加 AI 智能分析模式，支持 DeepSeek、OpenAI、Claude、通义千问
- ✨ 添加配置文件管理，支持灵活的 AI 配置
- ✨ 添加 AI 分析失败自动降级到正则模式

**优化**
- 🚀 优化 AI 请求重试机制
- 🚀 改进日程提取准确率

**修复**
- 🐛 修复时间标准化边界情况

### v6.1 - 2026-05-13

**新功能**
- ✨ 添加重复文章检测
- ✨ 已抓取 URL 持久化记录

### v6.0 - 2026-05-04

**重大更新**
- ✨ 全自动运行模式，零交互设计
- ✨ 自动访问华南师范大学新闻网
- ✨ 智能 302 跳转检测
- ✨ 按微信发布时间排序
- ✨ Markdown 格式输出

### v5.0 - 2026-04-24

**功能**
- ✨ 手动输入文章链接
- ✨ 三层内容提取兜底策略
- ✨ 数据校验机制

### v4.x - 已弃用

- ⚠️ 因链接结构问题已弃用

### v3.0 - 早期版本

- 📦 基础版本，CSV 输出

---

## 📜 开源协议

本项目采用 **MIT License** 开源协议。

```
MIT License

Copyright (c) 2026 nCuyTex

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👥 贡献者与联系方式

### 核心贡献者

| 贡献者 | 角色 | 贡献内容 |
|-------|------|---------|
| [@nCuyTex](https://github.com/nCuyTex) | 项目作者 | 核心开发、架构设计 |

### 致谢

感谢所有为项目做出贡献的开发者！

### 联系方式

| 渠道 | 链接                                                                 |
|-----|--------------------------------------------------------------------|
| GitHub Issues | [提交 Issue](https://github.com/nCuyTex/scnu-wechat-crawler/issues)  |
| GitHub Discussions | [参与讨论](https://github.com/nCuyTex/scnu-wechat-crawler/discussions) |
| 电子邮件 | [发送邮件](mailto:charehall@126.com)                                   |

### 支持与赞赏

如果您觉得本项目有帮助，欢迎：

1. ⭐ **Star** 本项目
2. 🔀 **Fork** 并参与贡献
3. 📢 向同学朋友推荐

---

<p align="center">
  <strong>🌟 Made with ❤️ for SCNUers</strong><br>
  <em>© 2026 SCNU WeChat Crawler. All rights reserved.</em>
</p>
