# 📘 使用指南 | User Guide

## 🤖 完全自动化方案

本项目使用 **Playwright** 实现完全自动化的期刊特刊追踪，无需手动维护！

## 🎯 工作原理

### 技术栈
- **Playwright** - Microsoft 开发的浏览器自动化工具
- **GitHub Actions** - 自动化运行爬虫
- **GitHub Pages** - 托管网站

### 自动化流程

```
每天 8:00 UTC (16:00 北京时间)
    ↓
GitHub Actions 触发
    ↓
启动 Playwright 无头浏览器
    ↓
访问期刊特刊页面
    ↓
提取特刊信息
    ↓
保存为 JSON
    ↓
自动提交到仓库
    ↓
GitHub Pages 自动更新
```

## 📝 添加新期刊

### 1. 编辑 scraper.py

找到 `self.journals` 列表并添加新期刊：

```python
self.journals = [
    # ... 现有期刊 ...
    
    # 添加你的新期刊
    {
        'name': '期刊完整名称',  # 例如：'Nature Communications'
        'url': '特刊页面URL',     # 主URL
        'backup_url': '备用URL'   # 备用URL（可选）
    }
]
```

### 2. 提交更改

```bash
git add scraper.py
git commit -m "Add new journal: [期刊名称]"
git push
```

### 3. 自动运行

GitHub Actions 会自动：
- 检测到文件变更
- 运行爬虫测试新期刊
- 更新数据

## 🔧 调整爬虫行为

### 修改爬取频率

编辑 `.github/workflows/update-data.yml`:

```yaml
schedule:
  # 默认：每天一次
  - cron: '0 8 * * *'
  
  # 每12小时一次
  # - cron: '0 */12 * * *'
  
  # 每周一次（周一8点）
  # - cron: '0 8 * * 1'
```

### 增加等待时间

如果爬虫太快导致问题，可以增加延迟：

在 `scraper.py` 中找到：
```python
await page.wait_for_timeout(2000)  # 2秒
```

改为：
```python
await page.wait_for_timeout(5000)  # 5秒
```

## 🐛 故障排查

### 问题1：GitHub Actions 失败

**检查步骤：**
1. 进入 Actions 标签
2. 点击失败的运行记录
3. 查看错误日志

**常见原因：**
- 网站结构变化
- 网络超时
- Playwright 浏览器问题

**解决方法：**
```bash
# 本地测试爬虫
pip install -r requirements.txt
playwright install chromium
python scraper.py
```

### 问题2：爬不到数据

**可能原因：**
- 网站改版
- 选择器失效
- 反爬虫检测

**调试方法：**

1. 在 `scraper.py` 中启用 headful 模式：
```python
browser = await p.chromium.launch(headless=False)  # 改为 False
```

2. 添加调试日志：
```python
print(f"Page title: {await page.title()}")
print(f"URL: {page.url}")
```

3. 截图调试：
```python
await page.screenshot(path='debug.png')
```

### 问题3：数据格式错误

检查 `data/special_issues.json` 格式：

```json
{
  "last_updated": "2026-02-08 12:00:00",
  "journals": [
    {
      "name": "期刊名称",
      "url": "URL",
      "special_issues": [...]
    }
  ]
}
```

## 🎨 自定义界面

### 修改网站样式

编辑 `index.html` 中的 CSS：

```css
/* 修改主题色 */
header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 修改卡片样式 */
.issue-card {
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

### 添加新语言

在 `index.html` 中：

```html
<select id="secondLang">
    <!-- 添加新语言 -->
    <option value="it">Italiano (Italian)</option>
    <option value="nl">Nederlands (Dutch)</option>
</select>
```

## 📊 性能优化

### 1. 减少爬取时间

```python
# 在 scraper.py 中
# 减少等待时间
await page.goto(url, wait_until='domcontentloaded')  # 而不是 'networkidle'

# 跳过图片和CSS
await context.new_page()
await context.route("**/*.{png,jpg,jpeg,css}", lambda route: route.abort())
```

### 2. 并发爬取多个期刊

```python
async def scrape_all_concurrent(self):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        tasks = []
        for journal in self.journals:
            page = await browser.new_page()
            tasks.append(self.scrape_journal(page, journal))
        
        results = await asyncio.gather(*tasks)
        await browser.close()
```

## 🌍 多语言翻译

当前使用 Google Translate API（浏览器端）。

如需更高质量翻译，可以集成：
- DeepL API
- Microsoft Translator
- Google Cloud Translation API

## 💡 最佳实践

1. **定期检查**：每月查看一次 Actions 日志
2. **备份数据**：定期下载 `special_issues.json`
3. **测试期刊**：添加新期刊后手动触发一次 Actions
4. **尊重网站**：不要设置过于频繁的爬取
5. **版本控制**：对爬虫逻辑的重要修改做好注释

## 📞 获取帮助

- **Bug 报告**：创建 GitHub Issue
- **功能请求**：创建 GitHub Discussion
- **代码贡献**：提交 Pull Request

---

**Enjoy automated tracking!** 🎉