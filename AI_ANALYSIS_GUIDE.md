# AI 智能分析日程功能使用说明

## 快速开始

### 1. 配置文件

项目根目录下的 `config.json` 配置文件控制分析模式：

```json
{
  "analysis_mode": "regex",
  "ai_api_key": "你的 AI API Key"
}
```

### 2. 选择分析模式

#### 模式 1：正则表达式分析（默认）

```json
{
  "analysis_mode": "regex"
}
```

- 优点：无需配置，快速，离线可用
- 缺点：只能匹配固定格式的日程

#### 模式 2：AI 大模型分析

```json
{
  "analysis_mode": "ai",
  "ai_api_key": "sk-your-api-key-here"
}
```

- 优点：智能理解，提取更准确
- 缺点：需要 API Key，有网络延迟

### 3. 配置 AI API（可选）

支持多种 AI API，通过 `ai_api_type` 切换：

#### DeepSeek（默认）

```json
{
  "analysis_mode": "ai",
  "ai_api_type": "deepseek",
  "ai_api_url": "https://api.deepseek.com/v1/chat/completions",
  "ai_api_key": "sk-your-deepseek-key",
  "ai_model": "deepseek-chat",
  "ai_timeout": 30,
  "max_retry": 3
}
```

#### OpenAI / ChatGPT

```json
{
  "ai_api_type": "openai",
  "ai_api_url": "https://api.openai.com/v1/chat/completions",
  "ai_api_key": "sk-your-openai-key",
  "ai_model": "gpt-4o"
}
```

#### Claude (Anthropic)

```json
{
  "ai_api_type": "claude",
  "ai_api_url": "https://api.anthropic.com/v1/messages",
  "ai_api_key": "sk-your-claude-key",
  "ai_model": "claude-sonnet-4-20250514"
}
```

#### 通义千问（阿里云）

```json
{
  "ai_api_type": "qwen",
  "ai_api_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
  "ai_api_key": "sk-your-qwen-key",
  "ai_model": "qwen-max"
}
```

## 运行程序

```bash
python src/auto_scnu_crawler.py
```

程序会自动读取配置文件，使用指定的分析模式。

## 输出说明

### 控制台输出

```
============================================================
华南师范大学「晚安华师」日程自动抓取工具 v6.2
============================================================
分析模式：AI 大模型分析
...
[Step 6/6] 输出结果...

============================================================
抓取结果
============================================================
分析模式：AI 大模型分析

[文章 1]
标题：...
提取日程信息：
  - [3 月 15 日] 开学
```

### Markdown 文件输出

```markdown
# 晚安华师日程信息抓取结果
抓取时间：2026-05-16 19:00:00
分析模式：AI 大模型分析
共抓取 2 篇文章

## 文章 1
...

### 提取的日程信息
- [3 月 15 日] 开学
```

## 异常处理

程序会自动处理以下异常情况：

| 异常类型 | 处理方式 |
|---------|---------|
| API Key 未配置 | 自动降级到正则模式 |
| 网络超时 | 重试（最多 3 次）→ 降级到正则模式 |
| API 返回错误（401） | 报错提示 "API Key 错误" → 降级到正则模式 |
| JSON 解析失败 | 降级到正则模式 |
| 无返回/空返回 | 视为无日程 |

## 注意事项

1. **API Key 安全**：`config.json` 包含敏感信息，请勿上传到公开仓库
2. **费用控制**：AI 分析会产生 API 调用费用，建议先用小额测试
3. **网络环境**：确保能访问所选 AI API 的服务器
4. **降级保护**：AI 分析失败时自动降级到正则模式，不会中断程序

## 文件结构

```
d:\drag\
├── config.json                     # 配置文件
├── src/
│   └── auto_scnu_crawler.py       # 主程序（v6.2）
├── output/
│   └── wechat_schedule_output.md  # 输出文件
└── logs/
    └── scnu_auto_crawler.log      # 运行日志
```
