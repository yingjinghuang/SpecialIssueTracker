import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 从环境变量获取密钥
API_KEY = os.environ.get('SCRAPER_API_KEY')

# 定义目标期刊
JOURNALS = [
    {
        'name': 'Remote Sensing of Environment',
        'url': 'https://www.sciencedirect.com/journal/remote-sensing-of-environment/about/call-for-papers'
    },
    {
        'name': 'Cities',
        'url': 'https://www.sciencedirect.com/journal/cities/about/call-for-papers'
    }
]

def get_soup(target_url):
    """
    通过 ScraperAPI 获取渲染后的 HTML
    """
    if not API_KEY:
        raise ValueError("❌ 缺少 API Key！请在 GitHub Secrets 中配置 SCRAPER_API_KEY")

    payload = {
        'api_key': API_KEY,
        'url': target_url,
        'render': 'true',  # 关键：告诉 API 帮我们渲染 JS
        # 'country_code': 'us', # 可选：指定美国 IP
    }
    
    print(f"   ☁️ Calling ScraperAPI for: {target_url} ...")
    try:
        r = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
        if r.status_code == 200:
            print("   ✅ Success! Content received.")
            return BeautifulSoup(r.text, 'html.parser')
        else:
            print(f"   ❌ Failed: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def parse_journal(journal):
    print(f"📖 Scraping {journal['name']}...")
    soup = get_soup(journal['url'])
    issues = []
    
    if not soup:
        return []

    # BeautifulSoup 查找逻辑
    # 寻找所有 href 包含 special-issue 的 a 标签
    links = soup.select('a[href*="/special-issue/"]')
    print(f"   🔍 Found {len(links)} raw links.")

    seen_urls = set()
    
    for link in links:
        title = link.get_text(strip=True)
        url = link.get('href')
        
        if not title or not url:
            continue
            
        # 补全 URL
        if not url.startswith('http'):
            url = 'https://www.sciencedirect.com' + url
            
        if url not in seen_urls:
            seen_urls.add(url)
            issues.append({
                'title': title,
                'url': url,
                'deadline': 'Check Link', # 如果想进一步抓详情，需要再调一次 API
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            })
            
    print(f"   ✅ Extracted {len(issues)} unique issues.")
    return issues

def main():
    print("=" * 60)
    print(f"🚀 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'journals': []
    }
    
    for journal in JOURNALS:
        issues = parse_journal(journal)
        results['journals'].append({
            'name': journal['name'],
            'url': journal['url'],
            'special_issues': issues
        })
    
    # 保存结果
    os.makedirs('data', exist_ok=True)
    with open('data/issues.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"💾 Data saved to data/issues.json")
    print("=" * 60)

if __name__ == "__main__":
    main()