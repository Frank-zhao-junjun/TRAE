#!/usr/bin/env python3
"""
GitHub Trending Top 10 自动抓取脚本
抓取热榜 → 生成 Markdown → 写入 IMA 知识库
"""

import json
import os
import re
import sys
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request, urlopen

# ============ 配置 ============
IMA_CLIENT_ID = os.environ.get("IMA_CLIENT_ID", "474a298eeb695dfea40b311c23f5984b")
IMA_API_KEY = os.environ.get("IMA_API_KEY", "uXRK7ZzFtfgwWq5Uco2UraGe4AIBMGGzSL9/Pf+DYXv8uAqqM7UG+z+/K2+cIFTAltBhzWkwTw==")
IMA_KNOWLEDGE_BASE_ID = os.environ.get("IMA_KNOWLEDGE_BASE_ID", "Jh3lk3quIekpqBO-FPi_xbpJO4K92ao-SjFMQiveJt0=")
IMA_BASE_URL = "https://ima.qq.com"


# ============ GitHub Trending 抓取 ============

def fetch_github_trending():
    """抓取 GitHub Trending 页面，提取 Top 10 项目信息"""
    url = "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8")
    except URLError as e:
        print(f"抓取 GitHub Trending 失败: {e}")
        return []

    article_pattern = re.compile(
        r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>', re.DOTALL
    )
    articles = article_pattern.findall(html)

    projects = []
    for i, article in enumerate(articles[:10]):
        project = _parse_project(article)
        if project:
            project["rank"] = i + 1
            projects.append(project)
    return projects


def _parse_project(article_html):
    """解析单个项目信息"""
    try:
        link_match = re.search(
            r'<h2[^>]*>.*?<a[^>]*href="(/[^"]+)"[^>]*>', article_html, re.DOTALL
        )
        if not link_match:
            return None
        repo_path = link_match.group(1).strip("/")

        h2_match = re.search(r'<h2[^>]*>(.*?)</h2>', article_html, re.DOTALL)
        repo_name = repo_path
        if h2_match:
            name_match = re.search(
                r'<a[^>]*href="/' + re.escape(repo_path) + r'"[^>]*>(.*?)</a>',
                h2_match.group(1),
                re.DOTALL,
            )
            if name_match:
                name_text = re.sub(r"<[^>]+>", "", name_match.group(1))
                name_text = " ".join(name_text.split())
                repo_name = name_text.replace(" / ", "/")

        desc_match = re.search(
            r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>',
            article_html,
            re.DOTALL,
        )
        description = ""
        if desc_match:
            description = re.sub(r"<[^>]+>", "", desc_match.group(1)).strip()
            description = " ".join(description.split())

        lang_match = re.search(
            r'<span[^>]*itemprop="programmingLanguage"[^>]*>([^<]*)</span>',
            article_html,
        )
        language = lang_match.group(1).strip() if lang_match else "Unknown"

        stars_today_match = re.search(r"([\d,]+)\s*stars?\s*today", article_html)
        stars_today = stars_today_match.group(1).strip() if stars_today_match else "0"

        total_stars_match = re.search(
            r'href="[^"]*stargazers[^"]*"[^>]*>.*?([\d,]+)</a>',
            article_html,
            re.DOTALL,
        )
        total_stars = total_stars_match.group(1).strip() if total_stars_match else "0"

        forks_match = re.search(
            r'href="[^"]*forks[^"]*"[^>]*>.*?([\d,]+)</a>',
            article_html,
            re.DOTALL,
        )
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


# ============ Markdown 生成 ============

def generate_markdown(projects):
    """生成 Markdown 格式的热榜文档"""
    today = datetime.now().strftime("%Y-%m-%d")
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][
        datetime.now().weekday()
    ]

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


# ============ IMA API 操作 ============

def ima_post(path, data):
    """调用 IMA OpenAPI"""
    url = f"{IMA_BASE_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "ima-openapi-clientid": IMA_CLIENT_ID,
        "ima-openapi-apikey": IMA_API_KEY,
    }
    try:
        req = Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"code": -1, "msg": str(e)}


def write_to_ima(title, markdown_content):
    """
    将 Markdown 内容写入 IMA 知识库
    流程: 创建笔记 → 添加到知识库
    """
    # Step 1: 创建笔记
    print("  [IMA] 创建笔记...")
    result = ima_post("/openapi/note/v1/import_doc", {
        "content_format": 1,  # MARKDOWN
        "content": markdown_content,
        "folder_name": "Github热榜",
    })

    if result.get("code") != 0:
        print(f"  [IMA] 创建笔记失败: {result.get('msg')}")
        return False

    note_id = result.get("data", {}).get("note_id")
    if not note_id:
        print("  [IMA] 未获取到 note_id")
        return False

    print(f"  [IMA] 笔记 ID: {note_id}")

    # Step 2: 添加到知识库
    print("  [IMA] 添加到知识库...")
    result2 = ima_post("/openapi/wiki/v1/add_knowledge", {
        "media_type": 11,  # 笔记类型
        "title": title,
        "knowledge_base_id": IMA_KNOWLEDGE_BASE_ID,
        "note_info": {
            "content_id": note_id,
        },
    })

    if result2.get("code") == 0:
        print(f"  [IMA] 写入成功!")
        return True
    else:
        print(f"  [IMA] 添加到知识库失败: {result2.get('msg')}")
        return False


# ============ 主流程 ============

def main():
    print("=" * 60)
    print("GitHub Trending 自动抓取 + IMA 知识库同步")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 调试：检查环境变量
    print(f"\n[调试] IMA_CLIENT_ID: {'已设置' if IMA_CLIENT_ID else '未设置'}")
    print(f"[调试] IMA_API_KEY: {'已设置' if IMA_API_KEY else '未设置'}")
    print(f"[调试] IMA_KNOWLEDGE_BASE_ID: {'已设置' if IMA_KNOWLEDGE_BASE_ID else '未设置'}")

    # 1. 抓取 GitHub Trending
    print("\n[1/3] 正在抓取 GitHub Trending...")
    projects = fetch_github_trending()

    if not projects:
        print("抓取失败，未获取到项目数据")
        sys.exit(1)

    print(f"成功抓取 {len(projects)} 个项目:")
    for p in projects:
        print(f"  {p['rank']}. {p['name']} ({p['language']}) +{p['stars_today']} stars today")

    # 2. 生成 Markdown
    print("\n[2/3] 正在生成 Markdown 文档...")
    markdown_content = generate_markdown(projects)
    today = datetime.now().strftime("%Y-%m-%d")
    file_name = f"GitHub热榜_{today}.md"

    # 保存到本地
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "..", "github_trending")
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"文件已保存: {file_path}")

    # 3. 写入 IMA 知识库
    print(f"\n[3/3] 正在写入 IMA 知识库...")
    success = write_to_ima(file_name, markdown_content)

    if success:
        print(f"\n✅ 全部完成! 热榜已写入 IMA 知识库「Github热榜」")
    else:
        print(f"\n⚠️ Markdown 文件已生成，但写入 IMA 知识库失败")

    print("=" * 60)
    return file_path


if __name__ == "__main__":
    main()
