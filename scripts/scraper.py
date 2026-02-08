#!/usr/bin/env python3
import json
import os
import asyncio
import random
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright

# 尝试导入 stealth
try:
    from playwright_stealth import stealth_async
except ImportError:
    async def stealth_async(page): pass

class PlaywrightJournalScraper:
    def __init__(self):
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
            
            # --- 关键策略 1: 伪装 Referer (假装来自 Google) ---
            await page.set_extra_http_headers({
                "Referer": "https://www.google.com/",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            })

            # --- 关键策略 2: 迂回战术 (先访问首页领 Cookie) ---
            print("   Drafting cookies from homepage...")
            try:
                await page.goto("https://www.sciencedirect.com/", wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4)) # 假装人在看首页
            except Exception as e:
                print(f"   ⚠️ Homepage load warning: {e}")

            # --- 关键策略 3: 跳转到目标页 ---
            print("   Navigating to target page...")
            response = await page.goto(journal_info['url'], wait_until='domcontentloaded', timeout=60000)
            
            # 检查是否被拦截
            page_content = await page.content()
            if "There was a problem providing the content" in page_content or response.status == 403:
                print(f"   🚫 Blocked! Taking screenshot...")
                await page.screenshot(path=f"blocked_{journal_info['name'].replace(' ', '_')}.png")
                return []

            # 正常等待渲染
            await asyncio.sleep(5) 
            
            # 截图留证 (无论成功失败都存一张，方便调试)
            await page.screenshot(path=f"debug_{journal_info['name'].replace(' ', '_')}.png")

            # 查找链接 (针对 ScienceDirect 的结构调整)
            # 寻找 href 中包含 /special-issue/ 的链接
            links = page.locator('a[href*="/special-issue/"]')
            count = await links.count()
            print(f"   Found {count} potential links.")

            for i in range(count):
                element = links.nth(i)
                title = await element.text_content()
                url = await element.get_attribute('href')
                
                if title and url:
                    full_url = url if url.startswith('http') else f"https://www.sciencedirect.com{url}"
                    issues.append({
                        'title': title.strip(),
                        'url': full_url,
                        'deadline': 'Check Link',
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    })

        except Exception as e:
            print(f"   ✗ Error: {e}")
            await page.screenshot(path=f"error_{journal_info['name'].replace(' ', '_')}.png")
        finally:
            await page.close()
        
        return self.deduplicate(issues)

    def deduplicate(self, issues: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for i in issues:
            key = i['url']
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
            # 使用稍微旧一点的 User-Agent，有时候反而更稳
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1366, 'height': 768}, # 普通笔记本分辨率
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            )
            
            # 注入webdriver移除脚本
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            for journal in self.journals:
                issues = await self.scrape_journal(context, journal)
                results['journals'].append({
                    'name': journal['name'],
                    'url': journal['url'],
                    'special_issues': issues
                })
                print(f"   ✅ Collected {len(issues)} issues.")
                # 必须休息，防止请求过快被封 IP
                await asyncio.sleep(random.uniform(5, 10))

            await browser.close()
            
        os.makedirs('data', exist_ok=True)
        with open('data/issues.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Data saved to data/issues.json")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(PlaywrightJournalScraper().run())