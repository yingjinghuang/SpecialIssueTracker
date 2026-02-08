# 📚 Academic Journal Special Issues Tracker

自动追踪学术期刊开放征稿的特刊信息，并提供双语展示。

A web application that automatically tracks open special issues from academic journals with bilingual display support.

## ✨ Features

- 🤖 **完全自动化** - 使用 Playwright 真实浏览器自动爬取，无需手动维护
- 🔄 **每日更新** - 通过 GitHub Actions 每天自动运行
- 🌍 **双语显示** - 支持英文+多种第二语言（中文、西班牙语、法语等）
- 📱 **响应式设计** - 在各种设备上都有良好的显示效果
- 🎯 **可扩展** - 轻松添加新期刊到追踪列表

## 🚀 Quick Start

### 1. 部署到 GitHub Pages

1. Fork 这个仓库
2. 进入仓库设置（Settings）
3. 找到 "Pages" 选项
4. 在 "Source" 下选择 `main` 分支和 `/` (root) 目录
5. 点击 "Save"
6. 等待几分钟后访问 `https://[你的用户名].github.io/[仓库名]/`

### 2. 启用 GitHub Actions

1. 进入仓库的 "Actions" 标签
2. 如果看到提示，点击 "I understand my workflows, go ahead and enable them"
3. 爬虫将每天自动运行一次，使用 Playwright 真实浏览器技术

### 3. 手动触发更新

1. 进入 "Actions" 标签
2. 点击左侧的 "Update Special Issues Data"
3. 点击右侧的 "Run workflow"
4. 选择分支并点击 "Run workflow"

## 🛠️ 技术架构

### 为什么使用 Playwright？

传统的爬虫（如 requests + BeautifulSoup）容易被现代网站的反爬虫机制阻止。本项目使用 **Playwright** 来解决这个问题：

- ✅ **真实浏览器** - 模拟真实用户行为，绕过反爬虫检测
- ✅ **JavaScript 渲染** - 完整渲染动态加载的内容
- ✅ **稳定可靠** - 由 Microsoft 维护，专业级浏览器自动化
- ✅ **GitHub Actions 兼容** - 完美支持无头模式运行

### 工作流程

1. GitHub Actions 每天定时触发
2. Playwright 启动无头浏览器
3. 访问期刊的特刊页面
4. 提取特刊信息（标题、截止日期、编辑等）
5. 保存为 JSON 数据
6. 自动提交更新到仓库
7. GitHub Pages 自动部署新版本

## 📝 自定义配置

### 添加新期刊

编辑 `scraper.py` 文件中的 `journals` 列表：

```python
self.journals = [
    {
        'name': 'Remote Sensing of Environment',
        'url': 'https://www.sciencedirect.com/journal/remote-sensing-of-environment/about/call-for-papers',
        'backup_url': 'https://www.journals.elsevier.com/remote-sensing-of-environment/call-for-papers'
    },
    {
        'name': 'Cities',
        'url': 'https://www.sciencedirect.com/journal/cities/about/call-for-papers',
        'backup_url': 'https://www.journals.elsevier.com/cities/call-for-papers'
    },
    # 在这里添加新的期刊
    {
        'name': '新期刊名称',
        'url': '期刊特刊页面URL',
        'backup_url': '备用URL（可选）'
    }
]
```

提交后，GitHub Actions 会自动使用新配置运行爬虫。

### 修改更新频率

编辑 `.github/workflows/update-data.yml` 中的 cron 表达式：

```yaml
schedule:
  # 每天 8:00 AM UTC 运行
  - cron: '0 8 * * *'
  
  # 其他示例：
  # - cron: '0 */6 * * *'  # 每 6 小时
  # - cron: '0 0 * * 0'    # 每周日
  # - cron: '0 0 1 * *'    # 每月 1 号
```

### 添加新的第二语言

编辑 `index.html` 中的语言选择器：

```html
<select id="secondLang">
    <option value="zh-CN">中文 (Chinese)</option>
    <!-- 添加新语言 -->
    <option value="语言代码">语言名称</option>
</select>
```

## 🛠️ 本地开发

### 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 运行爬虫

```bash
python scraper.py
```

### 本地预览网页

```bash
# 使用 Python 内置服务器
python -m http.server 8000

# 或使用 Node.js
npx serve
```

然后访问 `http://localhost:8000`

## 📊 数据结构

特刊数据保存在 `data/special_issues.json`：

```json
{
  "last_updated": "2026-02-08 12:00:00",
  "journals": [
    {
      "name": "期刊名称",
      "url": "期刊URL",
      "special_issues": [
        {
          "title": "特刊标题",
          "deadline": "截止日期",
          "guest_editors": "客座编辑",
          "description": "简介",
          "url": "特刊详情链接"
        }
      ]
    }
  ]
}
```

## ⚠️ 注意事项

1. **Playwright 爬虫**：使用真实浏览器技术，比传统爬虫更可靠
2. **翻译API**：当前使用免费的 Google Translate API，可能有使用限制
3. **数据准确性**：自动爬取的数据已经过优化，但建议定期检查
4. **GitHub Actions 限制**：
   - 每个工作流最长运行 6 小时
   - 免费账户有使用分钟数限制

## 🔧 故障排查

### 爬虫无法获取数据

1. 检查期刊网站结构是否改变
2. 查看 GitHub Actions 运行日志
3. 尝试手动运行爬虫并检查错误信息

### 网页显示异常

1. 检查浏览器控制台是否有错误
2. 确认 `data/special_issues.json` 文件格式正确
3. 清除浏览器缓存

### GitHub Actions 未运行

1. 确认 Actions 已启用
2. 检查 workflow 文件格式
3. 查看仓库的 Actions 权限设置

## 📄 License

MIT License - 可自由使用和修改

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系

如有问题或建议，请创建 Issue。

---

**Built with ❤️ for the academic community**