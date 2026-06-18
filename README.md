# GitHub 热榜自动抓取

每天自动抓取 GitHub Trending Top 10，生成 Markdown 文件并提交到仓库。

## 工作流程

```
定时触发 (GitHub Actions) → Python 爬虫抓取 → 解析 HTML → 生成 Markdown → 自动提交
```

## 文件说明

- `scripts/github_trending.py` - 抓取脚本
- `.github/workflows/daily-github-trending.yml` - GitHub Actions 工作流
- `github_trending/` - 生成的 Markdown 文件目录

## 触发方式

1. **定时触发**: 每天北京时间 09:00 (UTC 01:00) 自动执行
2. **手动触发**: 在 Actions 页面点击 "Run workflow"

## 数据格式

每个 Markdown 文件包含：
- 项目排名
- 项目名称和链接
- 项目简介
- 主要编程语言
- 今日新增 Stars
- 总 Stars 数
- Forks 数

## 后续：IMA 知识库同步

获取 IMA API Key 后，可以扩展脚本将内容自动写入 IMA 知识库。
