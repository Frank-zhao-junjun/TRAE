#!/usr/bin/env python3
"""
GitHub Trending Top 10 自动抓取脚本
生成 Markdown 格式文件
"""

import os
import re
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError


def fetch_github_trending():
    """抓取 GitHub Trending 页面，提取 Top 10 项目信息"""
    url = "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8")
    except URLError as e:
        print(f"抓取 GitHub Trending 失败: {e}")
        return []

    # 提取所有 article 块
    article_pattern = re.compile(r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>', re.DOTALL)
    articles = article_pattern.findall(html)

    projects = []
    for i, article in enumerate(articles[:10]):
        project = parse_project(article)
        if project:
            project["rank"] = i + 1
            projects.append(project)

    return projects


def parse_project(article_html):
    """解析单个项目信息"""
    try:
        # 提取仓库链接 - 从 h2 > a 的 href 属性
        link_match = re.search(r'<h2[^>]*>.*?<a[^>]*href="(/[^"]+)"[^>]*>', article_html, re.DOTALL)
        if not link_match:
            return None

        repo_path = link_match.group(1).strip('/')

        # 提取仓库名称 - 从 h2 > a 标签内的文本
        # 先找到 h2 块，再提取其中的 a 标签文本
        h2_match = re.search(r'<h2[^>]*>(.*?)</h2>', article_html, re.DOTALL)
        repo_name = repo_path
        if h2_match:
            h2_content = h2_match.group(1)
            # 在 h2 内容中找到仓库链接的 a 标签
            name_match = re.search(r'<a[^>]*href="/' + re.escape(repo_path) + r'"[^>]*>(.*?)</a>', h2_content, re.DOTALL)
            if name_match:
                # 移除所有 HTML 标签，保留文本
                name_text = re.sub(r'<[^>]+>', '', name_match.group(1))
                # 清理空白字符
                name_text = ' '.join(name_text.split())
                # 格式通常是 "Owner / RepoName"
                repo_name = name_text.replace(' / ', '/')

        # 提取描述
        desc_match = re.search(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', article_html, re.DOTALL)
        description = ""
        if desc_match:
            description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
            description = ' '.join(description.split())

        # 提取编程语言
        lang_match = re.search(r'<span[^>]*itemprop="programmingLanguage"[^>]*>([^<]*)</span>', article_html)
        language = lang_match.group(1).strip() if lang_match else "Unknown"

        # 提取今日新增 Stars
        stars_today_match = re.search(r'([\d,]+)\s*stars?\s*today', article_html)
        stars_today = stars_today_match.group(1).strip() if stars_today_match else "0"

        # 提取总 Stars
        total_stars_match = re.search(r'href="[^"]*stargazers[^"]*"[^>]*>.*?([\d,]+)</a>', article_html, re.DOTALL)
        total_stars = total_stars_match.group(1).strip() if total_stars_match else "0"

        # 提取 Forks
        forks_match = re.search(r'href="[^"]*forks[^"]*"[^>]*>.*?([\d,]+)</a>', article_html, re.DOTALL)
        forks = forks_match.group(1).strip() if forks_match else "0"

        return {
            "rank": 0,
            "name": repo_name,
            "url": f"https://github.com/{repo_path}",
            "description": description,
            "language": language,
            "stars_today": stars_today,
            "total_stars": total_stars,
            "forks": forks,
        }
    except Exception as e:
        print(f"解析项目失败: {e}")
        return None


def generate_markdown(projects):
    """生成 Markdown 格式的热榜文档"""
    today = datetime.now().strftime("%Y-%m-%d")
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]

    md = f"""# GitHub 热榜 Top 10 - {today}

> 自动生成于 {today} ({weekday_cn})
> 数据来源: [GitHub Trending](https://github.com/trending)

---

"""

    for project in projects:
        md += f"""## {project['rank']}. [{project['name']}]({project['url']})

**项目链接**: {project['url']}

**简介**: {project['description'] or '暂无描述'}

**主要语言**: {project['language']}

**今日新增 Stars**: {project['stars_today']}

**总 Stars**: {project['total_stars']}

**Forks**: {project['forks']}

---

"""

    md += f"""
## 统计信息

- **抓取时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **项目总数**: {len(projects)}

---

*本文件由自动化脚本生成，每日更新*
"""

    return md


def main():
    """主函数"""
    print("=" * 60)
    print("GitHub Trending 自动抓取脚本")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 抓取 GitHub Trending
    print("\n[1/2] 正在抓取 GitHub Trending...")
    projects = fetch_github_trending()

    if not projects:
        print("抓取失败，未获取到项目数据")
        sys.exit(1)

    print(f"成功抓取 {len(projects)} 个项目")
    for p in projects:
        print(f"  {p['rank']}. {p['name']} ({p['language']}) +{p['stars_today']} stars today")

    # 2. 生成 Markdown
    print("\n[2/2] 正在生成 Markdown 文档...")
    markdown_content = generate_markdown(projects)
    today = datetime.now().strftime("%Y-%m-%d")
    file_name = f"GitHub热榜_{today}.md"

    # 保存到仓库目录（支持本地和 GitHub Actions）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "..", "github_trending")
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"✅ 文件已保存: {file_path}")
    print(f"   文件名: {file_name}")
    print(f"   大小: {len(markdown_content)} 字符")

    # 同时打印内容预览
    print("\n" + "=" * 60)
    print("文件内容预览:")
    print("=" * 60)
    print(markdown_content[:500] + "...")

    print("\n" + "=" * 60)
    print("执行完成!")
    print("=" * 60)

    return file_path


if __name__ == "__main__":
    main()
