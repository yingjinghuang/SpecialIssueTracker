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
        """组合拳：DOM 选择器 + 正则全文扫描"""
        issues = []
        
        # 1. 首先尝试最正规的 DOM 提取
        items = await page.query_selector_all('li.list-item')
        for item in items:
            try:
                title_link = await item.query_selector('a[href*="/special-issue/"]')
                if title_link:
                    title = await title_link.inner_text()
                    href = await title_link.get_attribute('href')
                    issues.append({
                        'title': title.strip(),
                        'url': 'https://www.sciencedirect.com' + href if href.startswith('/') else href,
                        'deadline': "Parsing...",
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    })
            except: continue

        # 2. 如果 DOM 提取失败，启动正则扫描 (暴力提取所有 SI 链接)
        if not issues:
            # 匹配模式：寻找 /special-issue/ 开头的链接及其前后的文本
            # 这个正则会抓取 href 及其标签内的文本
            pattern = r'href="(/special-issue/[^"]+)"[^>]*>.*?<span>(.*?)</span>'
            matches = re.findall(pattern, html_content, re.DOTALL)
            
            for href, title in matches:
                # 过滤掉 HTML 标签
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                if len(clean_title) > 10:
                    issues.append({
                        'title': clean_title,
                        'url': 'https://www.sciencedirect.com' + href,
                        'deadline': "Check website",
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    })

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