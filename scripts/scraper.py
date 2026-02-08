#!/usr/bin/env python3
import json
import os
import asyncio
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright

# 尝试导入 stealth，如果没有也不强求（Github Actions 里可能需要特殊配置）
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
            # 增加 timeout 防止网络慢报错
            await page.goto(journal_info['url'], wait_until='domcontentloaded', timeout=60000)
            
            # 等待 5 秒让 JS 加载
            await asyncio.sleep(5) 
            
            # --- 关键调试步骤 ---
            # 如果抓不到数据，查看当前目录下生成的 debug_截图.png，看看是不是出现了验证码
            screenshot_path = f"debug_{journal_info['name'].replace(' ', '_')}.png"
            await page.screenshot(path=screenshot_path)
            print(f"   📸 Debug screenshot saved to {screenshot_path}")
            # --------------------

            # 使用 Locator 查找所有包含 special-issue 的链接
            # ScienceDirect 的结构通常是列表，我们直接找 href 里带 special-issue 的 a 标签
            links = page.locator('a[href*="/special-issue/"]')
            
            count = await links.count()
            print(f"   Found {count} potential links via Locator.")

            for i in range(count):
                element = links.nth(i)
                title = await element.text_content()
                url = await element.get_attribute('href')
                
                # 简单清洗数据
                if title and url:
                    # 补全 URL
                    full_url = url if url.startswith('http') else f"https://www.sciencedirect.com{url}"
                    
                    issues.append({
                        'title': title.strip(),
                        'url': full_url,
                        'deadline': 'Check Link', # deadline 往往藏在详情页，列表页很难抓准，先略过
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    })

        except Exception as e:
            print(f"   ✗ Error: {e}")
        finally:
            await page.close()
        
        return self.deduplicate(issues)

    def deduplicate(self, issues: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for i in issues:
            # 用 URL 做去重键更准确
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
            # ⚠️ 关键修改：添加防检测参数
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled', # 移除自动化特征
                    '--no-sandbox', 
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                    '--window-position=0,0',
                    '--ignore-certificate-errors',
                    '--window-size=1920,1080',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36' 
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                # 再次覆盖 User Agent 确保万无一失
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            
            # 为每个页面注入 JS，彻底抹除 webdriver 痕迹
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            for journal in self.journals:
                issues = await self.scrape_journal(context, journal)
                results['journals'].append({
                    'name': journal['name'],
                    'url': journal['url'],
                    'special_issues': issues
                })
                # 打印一下结果预览
                print(f"   ✅ Collected {len(issues)} issues.")
                await asyncio.sleep(3) # 休息一下

            await browser.close()
            
        # 保存结果
        os.makedirs('data', exist_ok=True)
        with open('data/issues.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Data saved to data/issues.json")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(PlaywrightJournalScraper().run())