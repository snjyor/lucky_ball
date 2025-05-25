# 🎯 双色球开奖数据分析系统

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ⚠️ 重要免责声明

**本项目仅用于技术学习和数据分析研究目的**

- 🎲 彩票开奖结果完全随机，历史数据无法预测未来结果
- 📊 本分析结果仅供参考，不构成任何投注建议
- 💰 请理性购彩，量力而行，未满18周岁禁止购买彩票
- ⚖️ 开发者不承担因使用本脚本产生的任何损失

## 🎯 今日推荐号码

**⚠️ 以下推荐号码基于历史统计分析，仅供参考，不保证中奖！**

### 双色球推荐 (更新时间: 2025年05月25日 16:13:18)

**推荐 1** (高频主导): `09 11 14 20 22 32` + `01`  
*基于最高频号码的稳定组合 | 2奇4偶 | 和值:108 | 跨度:23*

**推荐 2** (均衡分布): `06 07 22 23 26 33` + `16`  
*高中低频均衡的平衡组合 | 3奇3偶 | 和值:117 | 跨度:27*

**推荐 3** (中频优先): `07 14 20 23 30 32` + `15`  
*中频主导的稳健组合 | 2奇4偶 | 和值:126 | 跨度:25*

**推荐 4** (冷热结合): `14 21 26 27 30 32` + `07`  
*热号与冷号结合的对冲组合 | 2奇4偶 | 和值:150 | 跨度:18*

**推荐 5** (超高频): `01 02 09 10 19 20` + `01`  
*超高频号码的激进组合 | 3奇3偶 | 和值:61 | 跨度:19*
### 大乐透推荐 (更新时间: 2025年05月25日 16:13:18)

**推荐 1** (高频主导): `19 20 26 29 33` + `07 09`  
*基于最高频号码的稳定组合 | 3奇2偶 | 和值:127 | 跨度:14*

**推荐 2** (均衡分布): `10 17 27 33 35` + `04 11`  
*高中低频均衡的平衡组合 | 4奇1偶 | 和值:122 | 跨度:25*

**推荐 3** (中频优先): `03 10 19 25 29` + `01 11`  
*中频主导的稳健组合 | 4奇1偶 | 和值:86 | 跨度:26*

**推荐 4** (冷热结合): `07 16 24 25 29` + `01 09`  
*热号与冷号结合的对冲组合 | 3奇2偶 | 和值:101 | 跨度:22*

**推荐 5** (超高频): `05 30 31 32 34` + `07 12`  
*超高频号码的激进组合 | 2奇3偶 | 和值:132 | 跨度:29*

## 🚀 功能特性

- 📈 **自动数据抓取**: 每日自动抓取最新双色球开奖数据
- 📊 **统计分析**: 号码频率、奇偶分布、和值跨度等多维度分析
- 📉 **趋势分析**: 冷热号码分析和走势识别
- 🎯 **智能推荐**: 基于统计学的号码推荐算法
- 📱 **可视化图表**: 生成直观的频率分析图表
- 📋 **分析报告**: 自动生成详细的Markdown格式分析报告
- 🤖 **自动化部署**: GitHub Actions自动运行和数据更新

## 📁 项目结构

```
lucky_ball/
├── lottery_analyzer.py          # 主分析脚本
├── requirements.txt             # Python依赖包
├── lottery_data.json           # 开奖数据文件 (自动生成)
├── analysis_report.md          # 详细分析报告 (自动生成)
├── lottery_frequency_analysis.png # 分析图表 (自动生成)
├── .github/workflows/
│   └── update-lottery-data.yml  # GitHub Actions工作流
├── README.md                    # 项目说明
├── LICENSE                      # 开源协议
└── .gitignore                   # Git忽略文件
```

## 🛠️ 安装使用

### 本地运行

1. **克隆仓库**

   ```bash
   git clone https://github.com/your-username/lucky_ball.git
   cd lucky_ball
   ```
2. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```
3. **运行分析**

   ```bash
   python lottery_analyzer.py
   ```

### GitHub Actions自动化

本项目配置了GitHub Actions，会在以下情况自动运行：

- 🕐 **定时运行**: 每天晚上23:00(UTC+8)自动抓取最新数据
- 🖱️ **手动触发**: 在Actions页面可以手动触发运行
- 📝 **自动提交**: 有新数据时自动提交到仓库
- 🏷️ **创建发布**: 每日数据更新时自动创建带数据文件的release

## 📊 分析功能

### 1. 号码频率分析

- 红球和蓝球的出现频率统计
- 热号和冷号识别
- 可视化频率分布图

### 2. 号码规律分析

- 奇偶分布规律
- 和值分布统计
- 跨度分布分析

### 3. 走势分析

- 最近期数走势
- 冷热号码变化
- 号码遗漏统计

### 4. 智能推荐

- 基于概率统计的号码推荐
- 多组号码生成
- 权重算法优化

### 5. 分析报告

- 自动生成Markdown格式报告
- 包含完整的统计分析数据
- 提供详细的使用说明和风险提醒
- 每日自动更新

## 🔧 配置说明

### 修改抓取参数

在 `lottery_analyzer.py` 中可以调整以下参数：

```python
# 修改请求头
self.headers = {
    'User-Agent': '...'  # 可根据需要更新
}

# 修改生成推荐组数
recommendations = analyzer.generate_recommendations(num_sets=5)
```

### 修改GitHub Actions运行时间

在 `.github/workflows/update-lottery-data.yml` 中修改cron表达式：

```yaml
schedule:
  # 晚上23:00 (UTC+8)
  - cron: '0 15 * * *'
```

## 📈 数据来源

数据来源于中国福利彩票官方网站API：

- **API地址**: `https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice`
- **数据格式**: JSON
- **更新频率**: 每周二、四、日开奖后更新

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- 感谢中国福利彩票官方提供的开放数据
- 感谢所有开源贡献者的工具和库

## ⚖️ 法律声明

- 本项目严格遵守相关法律法规
- 仅用于技术研究和学习交流
- 不鼓励任何形式的赌博行为
- 如有违法违规使用，后果自负

---

**记住：彩票有风险，投注需谨慎！理性购彩，快乐生活！** 🍀
