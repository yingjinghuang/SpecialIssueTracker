#!/usr/bin/env python3
import json
import os
import asyncio
import re
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright

# 兼容性处理：适配不同版本的 playwright-stealth
try:
    from playwright_stealth import stealth_async
except ImportError:
    async def stealth_async(page):
        import playwright_stealth
        await playwright_stealth.stealth_async(page)

class PlaywrightJournalScraper:
    def __init__(self):
        # 使用你提供源码的 ScienceDirect 目标页面
        self.journals = [
            {
                'name': 'Remote Sensing of Environment',
                'url': 'https://www.sciencedirect.com/journal/remote-sensing-of-environment/about/call-for-papers'
            },
            {
                'name': 'Cities',
                'url': 'https://www.sciencedirect.com/journal/cities/about/call-for-papers'
            }
        ]

    async def scrape_journal(self, context, journal_info: Dict) -> List[Dict]:
        page = await context.new_page()
        await stealth_async(page)
        
        issues = []
        try:
            print(f"📖 Scraping {journal_info['name']}...")
            # 增加随机延时，模拟真人
            await page.goto(journal_info['url'], wait_until='networkidle', timeout=90000)
            
            # 暴力等待：无论如何先等 10 秒，给 React 充分的渲染时间
            await asyncio.sleep(10) 
            
            # 模拟一点滚动
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
            await asyncio.sleep(2)

            # 获取完整的 HTML 源码
            html_content = await page.content()
            print(f"   Source code obtained ({len(html_content)} chars). Scanning...")

            # 执行提取
            issues = await self.extract_logic(page, html_content)
            print(f"   ✓ Success: Found {len(issues)} issues")

        except Exception as e:
            print(f"   ✗ Error: {str(e)[:100]}")
        finally:
            await page.close()
        return issues

    async def extract_logic(self, page, html_content: str) -> List[Dict]:
        """从隐藏的 JSON 变量或原始文本中挖掘数据"""
        issues = []
        
        print("   🔍 Deep scanning source for hidden data patterns...")

        # 方案 A: 寻找链接模式 (不带 HTML 标签，直接搜字符串)
        # 匹配 URL: /special-issue/数字/标题
        links = re.findall(r'/special-issue/(\d+)/([^"\' >]+)', html_content)
        for issue_id, slug in links:
            # 将 slug 转换为可读标题 (例如 geospatial-foundation-models -> Geospatial Foundation Models)
            title = slug.replace('-', ' ').title()
            issues.append({
                'title': title,
                'url': f'https://www.sciencedirect.com/special-issue/{issue_id}/{slug}',
                'deadline': "Check Link",
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            })

        # 方案 B: 寻找 JSON 数组 (ScienceDirect 常见的内部存储格式)
        # 寻找包含 "specialIssueTitle" 或 "submissionDeadline" 的 JSON 块
        json_blobs = re.findall(r'\{"title":"[^"]+","url":"[^"]*special-issue[^"]*"\}', html_content)
        for blob in json_blobs:
            try:
                data = json.loads(blob)
                issues.append({
                    'title': data.get('title', 'Unknown'),
                    'url': 'https://www.sciencedirect.com' + data.get('url', ''),
                    'deadline': data.get('deadline', 'Unknown'),
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                })
            except: continue

        # 方案 C: 针对你提供的源码中出现的具体文案进行正则定位
        # 寻找 <h3><span>...</span></h3> 这种特定结构
        matches = re.findall(r'<span>([^<]{15,100}?)</span>', html_content)
        for match in matches:
            # 过滤掉明显的非标题文案
            if any(x in match.lower() for x in ['cookie', 'elsevier', 'sciencedirect', 'rights reserved']):
                continue
            # 如果看起来像个学术标题，就收录
            issues.append({
                'title': match.strip(),
                'url': "Search on site",
                'deadline': "Unknown",
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            })

        # 去重并过滤掉垃圾信息
        return self.deduplicate(issues)

    def deduplicate(self, issues: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for i in issues:
            key = i['title'].lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(i)
        return unique

    async def run(self):
        print("=" * 60)
        print(f"🚀 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'journals': []
        }
        
        async with async_playwright() as p:
            # 必须使用 chromium 并在 headless 模式下配置真实的上下文
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            for journal in self.journals:
                issues = await self.scrape_journal(context, journal)
                results['journals'].append({
                    'name': journal['name'],
                    'url': journal['url'],
                    'special_issues': issues
                })
                # 礼貌性延迟，防止 IP 触发二次拦截
                await asyncio.sleep(5)

            await browser.close()
            
        # 保存结果
        os.makedirs('data', exist_ok=True)
        with open('data/special_issues.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Scraping completed. Data saved to data/special_issues.json")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(PlaywrightJournalScraper().run())