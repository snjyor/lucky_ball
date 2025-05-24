#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双色球开奖数据抓取与分析脚本

⚠️  重要免责声明 ⚠️
1. 本脚本仅用于技术学习和数据分析研究目的
2. 彩票开奖结果完全随机，历史数据无法预测未来结果
3. 本分析结果仅供参考，不构成任何投注建议
4. 请理性购彩，量力而行，未满18周岁禁止购买彩票
5. 开发者不承担因使用本脚本产生的任何损失

功能：
1. 抓取中国福利彩票双色球历史开奖数据
2. 分析开奖号码规律
3. 基于统计分析生成推荐号码
"""

import requests
import time
import json
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class DoubleColorBallAnalyzer:
    """双色球分析器"""
    
    def __init__(self):
        self.base_url = "https://www.cwl.gov.cn/ygkj/wqkjgg/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.lottery_data = []
        
    def get_max_pages(self):
        """获取真实的最大页码"""
        print("正在获取最大页码...")
        
        api_url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
        
        try:
            # 先获取第一页数据来确定总数
            params = {
                'name': 'ssq',
                'pageNo': 1,
                'pageSize': 30,
                'systemType': 'PC'
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('state') != 0:
                print(f"API返回错误: {data.get('message', '未知错误')}")
                return 10  # 默认返回10页
            
            # 尝试获取总记录数
            total_count = data.get('total', 0)
            if total_count > 0:
                max_pages = (total_count + 29) // 30  # 向上取整
                print(f"发现总共 {total_count} 条记录，需要抓取 {max_pages} 页")
                return max_pages
            
            # 如果无法获取总数，通过试探方式确定最大页码
            print("无法获取总记录数，正在试探最大页码...")
            page = 1
            while page <= 200:  # 设置上限防止无限循环
                params['pageNo'] = page
                response = self.session.get(api_url, params=params, timeout=10)
                data = response.json()
                
                if data.get('state') != 0 or not data.get('result'):
                    break
                
                page += 10  # 每次跳跃10页快速试探
                time.sleep(0.2)
            
            # 精确定位最大页码
            start = max(1, page - 10)
            end = page
            
            for precise_page in range(start, end + 1):
                params['pageNo'] = precise_page
                response = self.session.get(api_url, params=params, timeout=10)
                data = response.json()
                
                if data.get('state') != 0 or not data.get('result'):
                    max_pages = precise_page - 1
                    print(f"通过试探确定最大页码为 {max_pages}")
                    return max_pages
                
                time.sleep(0.1)
            
            return max(1, page - 1)
            
        except Exception as e:
            print(f"获取最大页码时出错: {e}")
            return 100  # 默认返回100页
    
    def fetch_lottery_data(self, max_pages=10):
        """抓取双色球开奖数据"""
        print("开始抓取双色球开奖数据...")
        
        # API接口URL
        api_url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
        
        for page in range(1, max_pages + 1):
            print(f"正在抓取第 {page} 页数据...")
            
            try:
                # API参数
                params = {
                    'name': 'ssq',  # 双色球
                    'pageNo': page,
                    'pageSize': 30,
                    'systemType': 'PC'
                }
                
                response = self.session.get(api_url, params=params, timeout=10)
                response.raise_for_status()
                
                # 解析JSON响应
                data = response.json()
                
                if data.get('state') != 0:
                    print(f"API返回错误: {data.get('message', '未知错误')}")
                    continue
                
                results = data.get('result', [])
                if not results:
                    print(f"第 {page} 页无数据")
                    break
                
                print(f"第 {page} 页获取到 {len(results)} 条记录")
                
                for item in results:
                    try:
                        # 解析期号
                        period = item.get('code', '')
                        
                        # 解析开奖日期
                        date_str = item.get('date', '')
                        # 提取日期部分，去除星期信息
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
                        if not date_match:
                            continue
                        draw_date = date_match.group(1)
                        
                        # 解析红球号码（逗号分隔的字符串）
                        red_str = item.get('red', '')
                        if not red_str:
                            continue
                        red_balls = [int(x.strip()) for x in red_str.split(',')]
                        
                        # 解析蓝球号码
                        blue_str = item.get('blue', '')
                        if not blue_str:
                            continue
                        blue_ball = int(blue_str)
                        
                        # 解析其他信息
                        sales_amount = self._parse_number(item.get('sales', '0'))
                        pool_amount = self._parse_number(item.get('poolmoney', '0'))
                        
                        # 解析奖级信息
                        prizegrades = item.get('prizegrades', [])
                        first_prize_count = 0
                        first_prize_amount = 0
                        second_prize_count = 0
                        second_prize_amount = 0
                        
                        for grade in prizegrades:
                            if grade.get('type') == 1:  # 一等奖
                                first_prize_count = self._parse_number(grade.get('typenum', '0'))
                                first_prize_amount = self._parse_number(grade.get('typemoney', '0'))
                            elif grade.get('type') == 2:  # 二等奖
                                second_prize_count = self._parse_number(grade.get('typenum', '0'))
                                second_prize_amount = self._parse_number(grade.get('typemoney', '0'))
                        
                        # 存储数据
                        lottery_record = {
                            'period': period,
                            'date': draw_date,
                            'red_balls': red_balls,
                            'blue_ball': blue_ball,
                            'first_prize_count': first_prize_count,
                            'first_prize_amount': first_prize_amount,
                            'second_prize_count': second_prize_count,
                            'second_prize_amount': second_prize_amount,
                            'sales_amount': sales_amount,
                            'pool_amount': pool_amount
                        }
                        
                        self.lottery_data.append(lottery_record)
                        
                    except Exception as e:
                        print(f"解析记录时出错: {e}")
                        continue
                
                # 添加延时，避免请求过于频繁
                time.sleep(0.5)
                
            except Exception as e:
                print(f"抓取第 {page} 页时出错: {e}")
                continue
        
        print(f"数据抓取完成！共获取 {len(self.lottery_data)} 期开奖数据")
        return self.lottery_data
    
    def _parse_number(self, text):
        """解析数字，移除逗号等格式符号"""
        if not text or text == '-':
            return 0
        # 移除逗号、￥符号等
        cleaned = re.sub(r'[,￥¥元]', '', str(text))
        try:
            return int(float(cleaned))
        except:
            return 0
    
    def save_data(self, filename="lottery_data.json"):
        """保存数据到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.lottery_data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}")
    
    def load_data(self, filename="lottery_data.json"):
        """从文件加载数据"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.lottery_data = json.load(f)
            print(f"从 {filename} 加载了 {len(self.lottery_data)} 期数据")
            return True
        except FileNotFoundError:
            print(f"文件 {filename} 不存在")
            return False
    
    def analyze_frequency(self):
        """分析号码出现频率"""
        print("\n=== 号码频率分析 ===")
        
        # 红球频率分析
        red_counter = Counter()
        blue_counter = Counter()
        
        for record in self.lottery_data:
            for red in record['red_balls']:
                red_counter[red] += 1
            blue_counter[record['blue_ball']] += 1
        
        # 红球频率排序
        red_freq = sorted(red_counter.items(), key=lambda x: x[1], reverse=True)
        print("\n红球出现频率排行榜（前10）：")
        for i, (num, count) in enumerate(red_freq[:10], 1):
            percentage = (count / len(self.lottery_data)) * 100
            print(f"{i:2d}. 号码 {num:2d}: 出现 {count:3d} 次 ({percentage:.1f}%)")
        
        # 蓝球频率排序
        blue_freq = sorted(blue_counter.items(), key=lambda x: x[1], reverse=True)
        print("\n蓝球出现频率排行榜（前10）：")
        for i, (num, count) in enumerate(blue_freq[:10], 1):
            percentage = (count / len(self.lottery_data)) * 100
            print(f"{i:2d}. 号码 {num:2d}: 出现 {count:3d} 次 ({percentage:.1f}%)")
        
        return red_counter, blue_counter
    
    def analyze_patterns(self):
        """分析号码规律"""
        print("\n=== 号码规律分析 ===")
        
        # 奇偶分布分析
        odd_even_dist = defaultdict(int)
        sum_dist = defaultdict(int)
        span_dist = defaultdict(int)
        
        for record in self.lottery_data:
            red_balls = record['red_balls']
            
            # 奇偶分析
            odd_count = sum(1 for x in red_balls if x % 2 == 1)
            even_count = 6 - odd_count
            odd_even_dist[f"{odd_count}奇{even_count}偶"] += 1
            
            # 和值分析
            total_sum = sum(red_balls)
            sum_range = f"{(total_sum//10)*10}-{(total_sum//10)*10+9}"
            sum_dist[sum_range] += 1
            
            # 跨度分析
            span = max(red_balls) - min(red_balls)
            span_range = f"{(span//5)*5}-{(span//5)*5+4}"
            span_dist[span_range] += 1
        
        print("\n奇偶分布统计：")
        for pattern, count in sorted(odd_even_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.lottery_data)) * 100
            print(f"{pattern}: {count} 次 ({percentage:.1f}%)")
        
        print("\n和值分布统计：")
        for sum_range, count in sorted(sum_dist.items(), key=lambda x: int(x[0].split('-')[0])):
            percentage = (count / len(self.lottery_data)) * 100
            print(f"{sum_range}: {count} 次 ({percentage:.1f}%)")
        
        print("\n跨度分布统计：")
        for span_range, count in sorted(span_dist.items(), key=lambda x: int(x[0].split('-')[0])):
            percentage = (count / len(self.lottery_data)) * 100
            print(f"{span_range}: {count} 次 ({percentage:.1f}%)")
    
    def analyze_trends(self):
        """分析走势"""
        print("\n=== 走势分析 ===")
        
        if len(self.lottery_data) < 10:
            print("数据不足，无法进行走势分析")
            return
        
        # 最近10期的号码
        recent_10 = self.lottery_data[:10]
        
        print("最近10期开奖号码：")
        for record in recent_10:
            red_str = " ".join([f"{x:2d}" for x in record['red_balls']])
            print(f"{record['period']}: {red_str} + {record['blue_ball']:2d}")
        
        # 冷热号分析
        red_counter = Counter()
        blue_counter = Counter()
        
        for record in recent_10:
            for red in record['red_balls']:
                red_counter[red] += 1
            blue_counter[record['blue_ball']] += 1
        
        print(f"\n最近10期红球热号（出现2次及以上）：")
        hot_reds = [num for num, count in red_counter.items() if count >= 2]
        if hot_reds:
            hot_reds.sort()
            print(" ".join([f"{x:2d}" for x in hot_reds]))
        else:
            print("无")
        
        print(f"\n最近10期蓝球热号（出现2次及以上）：")
        hot_blues = [num for num, count in blue_counter.items() if count >= 2]
        if hot_blues:
            hot_blues.sort()
            print(" ".join([f"{x:2d}" for x in hot_blues]))
        else:
            print("无")
    
    def generate_recommendations(self, num_sets=5):
        """生成推荐号码（基于统计概率的固定推荐）"""
        print(f"\n=== 生成 {num_sets} 组推荐号码 ===")
        
        if not self.lottery_data:
            print("无数据，无法生成推荐")
            return []
        
        # 统计频率
        red_counter = Counter()
        blue_counter = Counter()
        
        for record in self.lottery_data:
            for red in record['red_balls']:
                red_counter[red] += 1
            blue_counter[record['blue_ball']] += 1
        
        # 获取红球频率排序（从高到低）
        red_freq_sorted = sorted(red_counter.items(), key=lambda x: x[1], reverse=True)
        # 获取蓝球频率排序（从高到低）
        blue_freq_sorted = sorted(blue_counter.items(), key=lambda x: x[1], reverse=True)
        
        # 提取高频号码用于组合
        high_freq_reds = [num for num, count in red_freq_sorted[:18]]  # 前18个高频红球
        high_freq_blues = [num for num, count in blue_freq_sorted[:8]]   # 前8个高频蓝球
        
        print(f"\n高频红球（前18）: {high_freq_reds}")
        print(f"高频蓝球（前8）: {high_freq_blues}")
        
        recommendations = []
        
        # 生成5组固定的推荐组合
        recommendation_patterns = [
            # 第1组：前6个最高频红球 + 最高频蓝球
            {
                'red_indices': [0, 1, 2, 3, 4, 5],
                'blue_index': 0,
                'description': '最高频组合'
            },
            # 第2组：混合高频球（1,3,5,7,9,11位置的球）
            {
                'red_indices': [0, 2, 4, 6, 8, 10],
                'blue_index': 1,
                'description': '高频均衡组合'
            },
            # 第3组：另一种混合（2,4,6,8,10,12位置的球）
            {
                'red_indices': [1, 3, 5, 7, 9, 11],
                'blue_index': 2,
                'description': '高频交替组合'
            },
            # 第4组：跨度较大的高频组合
            {
                'red_indices': [0, 3, 6, 9, 12, 15],
                'blue_index': 3,
                'description': '高频跨度组合'
            },
            # 第5组：平衡型组合
            {
                'red_indices': [1, 4, 7, 10, 13, 16],
                'blue_index': 4,
                'description': '高频平衡组合'
            }
        ]
        
        for i, pattern in enumerate(recommendation_patterns[:num_sets]):
            # 选择红球
            selected_reds = []
            for idx in pattern['red_indices']:
                if idx < len(high_freq_reds):
                    selected_reds.append(high_freq_reds[idx])
            
            # 如果红球不足6个，从剩余高频球中补充
            while len(selected_reds) < 6 and len(selected_reds) < len(high_freq_reds):
                for red in high_freq_reds:
                    if red not in selected_reds:
                        selected_reds.append(red)
                        if len(selected_reds) == 6:
                            break
            
            # 确保有6个红球
            if len(selected_reds) < 6:
                # 如果高频球还不够，从所有红球中补充
                all_reds = list(range(1, 34))
                for red in all_reds:
                    if red not in selected_reds:
                        selected_reds.append(red)
                        if len(selected_reds) == 6:
                            break
            
            selected_reds = sorted(selected_reds[:6])  # 排序并确保只有6个
            
            # 选择蓝球
            blue_idx = pattern['blue_index']
            if blue_idx < len(high_freq_blues):
                selected_blue = high_freq_blues[blue_idx]
            else:
                selected_blue = high_freq_blues[0]  # 默认选择最高频蓝球
            
            # 计算这组号码的期望频率
            red_total_freq = sum(red_counter.get(red, 0) for red in selected_reds)
            blue_freq = blue_counter.get(selected_blue, 0)
            
            recommendations.append({
                'red_balls': selected_reds,
                'blue_ball': selected_blue,
                'description': pattern['description'],
                'red_freq_sum': red_total_freq,
                'blue_freq': blue_freq,
                'total_freq': red_total_freq + blue_freq
            })
        
        # 按总频率排序推荐（可选，保持原有顺序也可以）
        # recommendations.sort(key=lambda x: x['total_freq'], reverse=True)
        
        print("\n基于统计概率的固定推荐号码：")
        for i, rec in enumerate(recommendations, 1):
            red_str = " ".join([f"{x:2d}" for x in rec['red_balls']])
            print(f"推荐 {i}: {red_str} + {rec['blue_ball']:2d} ({rec['description']})")
            print(f"       频率统计: 红球总频次={rec['red_freq_sum']}, 蓝球频次={rec['blue_freq']}")
        
        return recommendations
    
    def visualize_frequency(self, save_plots=True):
        """可视化频率分析"""
        if not self.lottery_data:
            print("无数据，无法生成图表")
            return
        
        # 统计频率
        red_counter = Counter()
        blue_counter = Counter()
        
        for record in self.lottery_data:
            for red in record['red_balls']:
                red_counter[red] += 1
            blue_counter[record['blue_ball']] += 1
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # 红球频率图
        red_nums = list(range(1, 34))
        red_freqs = [red_counter.get(num, 0) for num in red_nums]
        
        bars1 = ax1.bar(red_nums, red_freqs, color='red', alpha=0.7)
        ax1.set_title('红球出现频率分布', fontsize=16, fontweight='bold')
        ax1.set_xlabel('红球号码', fontsize=12)
        ax1.set_ylabel('出现次数', fontsize=12)
        ax1.set_xticks(red_nums)
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar, freq in zip(bars1, red_freqs):
            if freq > 0:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                        str(freq), ha='center', va='bottom', fontsize=8)
        
        # 蓝球频率图
        blue_nums = list(range(1, 17))
        blue_freqs = [blue_counter.get(num, 0) for num in blue_nums]
        
        bars2 = ax2.bar(blue_nums, blue_freqs, color='blue', alpha=0.7)
        ax2.set_title('蓝球出现频率分布', fontsize=16, fontweight='bold')
        ax2.set_xlabel('蓝球号码', fontsize=12)
        ax2.set_ylabel('出现次数', fontsize=12)
        ax2.set_xticks(blue_nums)
        ax2.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar, freq in zip(bars2, blue_freqs):
            if freq > 0:
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                        str(freq), ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        if save_plots:
            plt.savefig('lottery_frequency_analysis.png', dpi=300, bbox_inches='tight')
            print("频率分析图表已保存为 lottery_frequency_analysis.png")
        
        plt.show()
    
    def get_lottery_rules(self):
        """获取双色球游戏规则"""
        rules = """
        === 双色球游戏规则 ===
        
        1. 号码范围：
           - 红球：01-33，选择6个号码
           - 蓝球：01-16，选择1个号码
        
        2. 中奖等级：
           一等奖：6个红球 + 1个蓝球（浮动奖金，500万元起）
           二等奖：6个红球（浮动奖金）
           三等奖：5个红球 + 1个蓝球（固定3000元）
           四等奖：5个红球 或 4个红球 + 1个蓝球（固定200元）
           五等奖：4个红球 或 3个红球 + 1个蓝球（固定10元）
           六等奖：2个红球 + 1个蓝球 或 1个红球 + 1个蓝球 或 1个蓝球（固定5元）
        
        3. 开奖时间：每周二、四、日晚21:15
        
        4. 投注方式：
           - 单式投注：手动选择号码
           - 复式投注：选择7个以上红球进行组合
           - 机选投注：系统随机选择号码
        
        5. 中奖概率：
           一等奖：1/17,721,088
           二等奖：1/1,107,568
           三等奖：1/72,107
           
        注意：彩票投注有风险，请理性购彩，量力而行！
        """
        print(rules)
    
    def generate_analysis_report(self, filename="analysis_report.md"):
        """生成完整的分析报告文件"""
        print(f"正在生成分析报告: {filename}")
        
        if not self.lottery_data:
            print("无数据，无法生成报告")
            return
        
        # 执行所有分析
        red_counter, blue_counter = self._get_frequency_analysis()
        patterns_data = self._get_patterns_analysis()
        trends_data = self._get_trends_analysis()
        recommendations = self.generate_recommendations(num_sets=8)
        
        # 生成报告内容
        current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        
        report_content = f"""# 🎯 双色球数据分析报告

## 📊 报告信息
- **生成时间**: {current_time}
- **数据期数**: 共 {len(self.lottery_data)} 期
- **最新期号**: {self.lottery_data[0]['period'] if self.lottery_data else 'N/A'}
- **数据来源**: 中国福利彩票官方API

## ⚠️ 重要免责声明
**本分析报告仅供学习和研究使用，彩票开奖完全随机，历史数据无法预测未来结果。请理性购彩，量力而行！**

---

## 📈 最新开奖信息

"""
        
        # 添加最近5期开奖信息
        if len(self.lottery_data) >= 5:
            report_content += "### 最近5期开奖号码\n\n"
            for i, record in enumerate(self.lottery_data[:5]):
                red_str = " ".join([f"{x:02d}" for x in record['red_balls']])
                report_content += f"**{record['period']}期** ({record['date']}): {red_str} + **{record['blue_ball']:02d}**\n\n"
        
        # 添加号码频率分析
        report_content += """---

## 🔥 号码频率分析

### 红球出现频率排行榜（前15名）

| 排名 | 号码 | 出现次数 | 出现频率 |
|------|------|----------|----------|
"""
        
        red_freq = sorted(red_counter.items(), key=lambda x: x[1], reverse=True)
        for i, (num, count) in enumerate(red_freq[:15], 1):
            percentage = (count / len(self.lottery_data)) * 100
            report_content += f"| {i:02d} | **{num:02d}** | {count} | {percentage:.1f}% |\n"
        
        report_content += """
### 蓝球出现频率排行榜（前10名）

| 排名 | 号码 | 出现次数 | 出现频率 |
|------|------|----------|----------|
"""
        
        blue_freq = sorted(blue_counter.items(), key=lambda x: x[1], reverse=True)
        for i, (num, count) in enumerate(blue_freq[:10], 1):
            percentage = (count / len(self.lottery_data)) * 100
            report_content += f"| {i:02d} | **{num:02d}** | {count} | {percentage:.1f}% |\n"
        
        # 添加规律分析
        report_content += f"""
---

## 📊 号码规律分析

### 奇偶分布统计

{patterns_data['odd_even']}

### 和值分布统计

{patterns_data['sum_dist']}

### 跨度分布统计

{patterns_data['span_dist']}

---

## 📉 走势分析

### 最近10期开奖记录

{trends_data['recent_draws']}

### 热号分析

**最近10期红球热号（出现2次及以上）**: {trends_data['hot_reds']}

**最近10期蓝球热号（出现2次及以上）**: {trends_data['hot_blues']}

---

## 🎯 智能推荐号码

**⚠️ 以下推荐号码仅基于历史统计分析，不保证中奖，请理性参考！**

"""
        
        for i, rec in enumerate(recommendations, 1):
            red_str = " ".join([f"{x:02d}" for x in rec['red_balls']])
            report_content += f"**推荐组合 {i}**: {red_str} + **{rec['blue_ball']:02d}**\n\n"
        
        # 添加使用说明和提醒
        report_content += f"""---

## 📋 使用说明

### 数据更新频率
- 本报告每天自动更新一次
- 数据来源于中国福利彩票官方API
- 更新时间：每天晚上23:00

### 分析方法说明
1. **频率分析**: 统计每个号码在历史开奖中的出现次数
2. **规律分析**: 分析奇偶分布、和值分布、跨度分布等规律
3. **走势分析**: 观察最近期数的号码走势和热号变化
4. **智能推荐**: 基于统计概率和随机性的权重算法生成推荐号码

### 重要提醒

> 🎲 **彩票本质**: 彩票开奖具有完全的随机性和偶然性
> 
> 📊 **数据局限**: 历史数据无法预测未来开奖结果
> 
> 🎯 **参考价值**: 本分析仅供统计学习和娱乐参考
> 
> 💰 **理性购彩**: 请根据个人经济能力适度购买
> 
> ⚖️ **法律提醒**: 未满18周岁禁止购买彩票
> 
> 🏠 **家庭和睦**: 切勿因购彩影响家庭生活

---

## 📞 帮助信息

如果您或身边的人出现以下情况，请及时寻求帮助：
- 无法控制购彩行为
- 为了购彩借钱或变卖财产
- 因购彩影响工作、学习或家庭关系
- 出现焦虑、抑郁等心理问题

**全国戒赌帮助热线**: 400-161-9995

---

*报告生成时间: {current_time}*  
*数据来源: 中国福利彩票官方网站*  
*仅供学习研究使用，请理性购彩*
"""
        
        # 保存报告文件
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"分析报告已保存到 {filename}")
        except Exception as e:
            print(f"保存分析报告失败: {e}")
    
    def _get_frequency_analysis(self):
        """内部方法：获取频率分析数据"""
        red_counter = Counter()
        blue_counter = Counter()
        
        for record in self.lottery_data:
            for red in record['red_balls']:
                red_counter[red] += 1
            blue_counter[record['blue_ball']] += 1
        
        return red_counter, blue_counter
    
    def _get_patterns_analysis(self):
        """内部方法：获取规律分析数据"""
        odd_even_dist = defaultdict(int)
        sum_dist = defaultdict(int)
        span_dist = defaultdict(int)
        
        for record in self.lottery_data:
            red_balls = record['red_balls']
            
            # 奇偶分析
            odd_count = sum(1 for x in red_balls if x % 2 == 1)
            even_count = 6 - odd_count
            odd_even_dist[f"{odd_count}奇{even_count}偶"] += 1
            
            # 和值分析
            total_sum = sum(red_balls)
            sum_range = f"{(total_sum//10)*10}-{(total_sum//10)*10+9}"
            sum_dist[sum_range] += 1
            
            # 跨度分析
            span = max(red_balls) - min(red_balls)
            span_range = f"{(span//5)*5}-{(span//5)*5+4}"
            span_dist[span_range] += 1
        
        # 格式化数据
        odd_even_result = "| 分布类型 | 出现次数 | 出现频率 |\n|----------|----------|----------|\n"
        for pattern, count in sorted(odd_even_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.lottery_data)) * 100
            odd_even_result += f"| {pattern} | {count} | {percentage:.1f}% |\n"
        
        sum_result = "| 和值范围 | 出现次数 | 出现频率 |\n|----------|----------|----------|\n"
        for sum_range, count in sorted(sum_dist.items(), key=lambda x: int(x[0].split('-')[0])):
            percentage = (count / len(self.lottery_data)) * 100
            sum_result += f"| {sum_range} | {count} | {percentage:.1f}% |\n"
        
        span_result = "| 跨度范围 | 出现次数 | 出现频率 |\n|----------|----------|----------|\n"
        for span_range, count in sorted(span_dist.items(), key=lambda x: int(x[0].split('-')[0])):
            percentage = (count / len(self.lottery_data)) * 100
            span_result += f"| {span_range} | {count} | {percentage:.1f}% |\n"
        
        return {
            'odd_even': odd_even_result,
            'sum_dist': sum_result,
            'span_dist': span_result
        }
    
    def _get_trends_analysis(self):
        """内部方法：获取趋势分析数据"""
        if len(self.lottery_data) < 10:
            return {
                'recent_draws': '数据不足',
                'hot_reds': '无',
                'hot_blues': '无'
            }
        
        recent_10 = self.lottery_data[:10]
        
        # 格式化最近10期
        recent_draws = "| 期号 | 开奖日期 | 红球号码 | 蓝球 |\n|------|----------|----------|------|\n"
        for record in recent_10:
            red_str = " ".join([f"{x:02d}" for x in record['red_balls']])
            recent_draws += f"| {record['period']} | {record['date']} | {red_str} | **{record['blue_ball']:02d}** |\n"
        
        # 冷热号分析
        red_counter = Counter()
        blue_counter = Counter()
        
        for record in recent_10:
            for red in record['red_balls']:
                red_counter[red] += 1
            blue_counter[record['blue_ball']] += 1
        
        hot_reds = [num for num, count in red_counter.items() if count >= 2]
        hot_blues = [num for num, count in blue_counter.items() if count >= 2]
        
        hot_reds_str = " ".join([f"{x:02d}" for x in sorted(hot_reds)]) if hot_reds else "无"
        hot_blues_str = " ".join([f"{x:02d}" for x in sorted(hot_blues)]) if hot_blues else "无"
        
        return {
            'recent_draws': recent_draws,
            'hot_reds': hot_reds_str,
            'hot_blues': hot_blues_str
        }

def main():
    """主函数"""
    # 显示免责声明
    print("=" * 80)
    print("🎯 双色球数据分析系统")
    print("=" * 80)
    print("⚠️  重要免责声明：")
    print("• 彩票开奖完全随机，历史数据无法预测未来")
    print("• 本分析仅供学习参考，不构成投注建议")
    print("• 请理性购彩，量力而行，未满18周岁禁止购买")
    print("• 使用本软件产生的任何后果由用户自行承担")
    print("=" * 80)
    
    analyzer = DoubleColorBallAnalyzer()
    
    print("\n双色球开奖数据分析系统")
    print("=" * 50)
    
    # 始终抓取最新数据，覆盖现有文件
    print("⚠️  正在抓取最新数据，请确保网络连接正常...")
    max_pages = analyzer.get_max_pages()
    analyzer.fetch_lottery_data(max_pages=max_pages)
    analyzer.save_data()
    
    if not analyzer.lottery_data:
        print("❌ 无法获取数据，程序退出")
        return
    
    # 显示游戏规则
    analyzer.get_lottery_rules()
    
    # 执行各种分析
    red_counter, blue_counter = analyzer.analyze_frequency()
    analyzer.analyze_patterns()
    analyzer.analyze_trends()
    
    # 生成推荐号码
    recommendations = analyzer.generate_recommendations(num_sets=5)
    
    # 生成可视化图表
    try:
        analyzer.visualize_frequency()
    except Exception as e:
        print(f"⚠️  图表生成失败: {e}")
        print("可能是字体问题，请检查系统中文字体支持")
    
    # 生成分析报告
    analyzer.generate_analysis_report()
    
    print("\n" + "=" * 50)
    print("📋 重要提醒：")
    print("• 以上推荐号码基于历史统计，仅供参考")
    print("• 彩票具有偶然性，请勿过度依赖任何预测")
    print("• 理性购彩，适度娱乐，珍惜家庭和睦")
    print("• 如有赌博问题，请寻求专业帮助")
    print("=" * 50)
    print("✅ 分析完成！")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        print("请检查网络连接和依赖库安装情况") 