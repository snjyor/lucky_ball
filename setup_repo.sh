#!/bin/bash

# 双色球数据分析项目仓库初始化脚本

echo "🎯 初始化双色球数据分析项目仓库..."

# 检查是否已经是git仓库
if [ ! -d ".git" ]; then
    echo "📦 初始化Git仓库..."
    git init
else
    echo "✅ Git仓库已存在"
fi

# 添加所有文件
echo "📁 添加项目文件..."
git add .

# 创建初始提交
echo "💾 创建初始提交..."
git commit -m "🎯 初始化双色球数据分析项目

✨ 功能特性:
- 自动抓取双色球开奖数据
- 多维度统计分析
- 智能号码推荐
- 自动生成分析报告
- GitHub Actions自动化

📊 项目文件:
- lottery_analyzer.py: 主分析脚本
- requirements.txt: Python依赖
- .github/workflows/: GitHub Actions配置
- README.md: 项目文档
- test_analyzer.py: 测试脚本

⚠️ 免责声明: 仅供学习研究，理性购彩"

echo "🚀 仓库初始化完成！"
echo ""
echo "📋 接下来的步骤:"
echo "1. 在GitHub上创建新仓库 'lucky_ball'"
echo "2. 执行以下命令推送到远程仓库:"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/lucky_ball.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. 在GitHub仓库设置中启用Actions"
echo "4. GitHub Actions将在每天晚上23:00自动运行"
echo ""
echo "🎉 祝你好运！记住理性购彩！" 