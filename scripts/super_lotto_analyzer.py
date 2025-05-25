#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大乐透开奖数据抓取与分析脚本

⚠️  重要免责声明 ⚠️
1. 本脚本仅用于技术学习和数据分析研究目的
2. 彩票开奖结果完全随机，历史数据无法预测未来结果
3. 本分析结果仅供参考，不构成任何投注建议
4. 请理性购彩，量力而行，未满18周岁禁止购买彩票
5. 开发者不承担因使用本脚本产生的任何损失

功能：
1. 抓取大乐透历史开奖数据
2. 分析开奖号码规律
3. 基于统计分析生成推荐号码
"""

import requests
import time
import json
import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class SuperLottoAnalyzer:
    """大乐透分析器"""
    
    def __init__(self):
        self.base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://www.sporttery.cn/',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.lottery_data = []
        # 设置UTC+8时区
        self.utc8_tz = timezone(timedelta(hours=8))
        
    def get_current_time_utc8(self):
        """获取UTC+8时区的当前时间"""
        return datetime.now(self.utc8_tz)
        
    def format_time_utc8(self, dt=None):
        """格式化UTC+8时区的时间"""
        if dt is None:
            dt = self.get_current_time_utc8()
        return dt.strftime('%Y年%m月%d日 %H:%M:%S')
    
    def get_max_pages(self):
        """获取总页数"""
        print("正在获取总页数...")
        
        try:
            params = {
                'gameNo': '85',  # 大乐透
                'provinceId': '0',
                'pageSize': '30',
                'isVerify': '1',
                'pageNo': '1'
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('success', False):
                print(f"API返回错误: {data.get('errorMessage', '未知错误')}")
                return 10
            
            value = data.get('value', {})
            total_pages = value.get('pages', 10)
            total_records = value.get('total', 0)
            
            print(f"发现总共 {total_records} 条记录，共 {total_pages} 页")
            return total_pages
            
        except Exception as e:
            print(f"获取总页数时出错: {e}")
            return 100  # 默认返回100页
    
    def fetch_lottery_data(self, max_pages=10):
        """抓取大乐透开奖数据"""
        print("开始抓取大乐透开奖数据...")
        
        for page in range(1, max_pages + 1):
            print(f"正在抓取第 {page} 页数据...")
            
            try:
                params = {
                    'gameNo': '85',  # 大乐透
                    'provinceId': '0',
                    'pageSize': '30',
                    'isVerify': '1',
                    'pageNo': str(page)
                }
                
                response = self.session.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get('success', False):
                    print(f"API返回错误: {data.get('errorMessage', '未知错误')}")
                    continue
                
                value = data.get('value', {})
                results = value.get('list', [])
                
                if not results:
                    print(f"第 {page} 页无数据")
                    break
                
                print(f"第 {page} 页获取到 {len(results)} 条记录")
                
                for item in results:
                    try:
                        # 解析期号
                        period = item.get('lotteryDrawNum', '')
                        
                        # 解析开奖日期
                        date_str = item.get('lotteryDrawTime', '')
                        
                        # 解析开奖号码
                        draw_result = item.get('lotteryDrawResult', '')
                        if not draw_result:
                            continue
                        
                        # 解析号码：格式如 "09 10 11 12 29 01 10"
                        # 前5个是前区号码，后2个是后区号码
                        numbers = [int(x.strip()) for x in draw_result.split()]
                        if len(numbers) != 7:
                            continue
                        
                        front_balls = numbers[:5]  # 前区5个号码
                        back_balls = numbers[5:]   # 后区2个号码
                        
                        # 解析销售额
                        sales_amount = self._parse_number(item.get('totalSaleAmount', '0'))
                        pool_amount = self._parse_number(item.get('poolBalanceAfterdraw', '0'))
                        
                        # 解析奖级信息
                        prize_levels = item.get('prizeLevelList', [])
                        first_prize_count = 0
                        first_prize_amount = 0
                        second_prize_count = 0
                        second_prize_amount = 0
                        
                        for prize in prize_levels:
                            if prize.get('prizeLevel') == '一等奖' and prize.get('awardType') == 0:
                                first_prize_count = self._parse_number(prize.get('stakeCount', '0'))
                                first_prize_amount = self._parse_number(prize.get('stakeAmountFormat', '0'))
                            elif prize.get('prizeLevel') == '二等奖' and prize.get('awardType') == 0:
                                second_prize_count = self._parse_number(prize.get('stakeCount', '0'))
                                second_prize_amount = self._parse_number(prize.get('stakeAmountFormat', '0'))
                        
                        # 存储数据
                        lottery_record = {
                            'period': period,
                            'date': date_str,
                            'front_balls': front_balls,
                            'back_balls': back_balls,
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
        if not text or text == '-' or text == '---':
            return 0
        # 移除逗号、￥符号等
        cleaned = re.sub(r'[,￥¥元]', '', str(text))
        try:
            return int(float(cleaned))
        except:
            return 0
    
    def save_data(self, filename="super_lotto_data.json"):
        """保存数据到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.lottery_data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}")
    
    def load_data(self, filename="super_lotto_data.json"):
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
        
        # 前区和后区频率分析
        front_counter = Counter()
        back_counter = Counter()
        
        for record in self.lottery_data:
            for front in record['front_balls']:
                front_counter[front] += 1
            for back in record['back_balls']:
                back_counter[back] += 1
        
        # 前区频率排序
        front_freq = sorted(front_counter.items(), key=lambda x: x[1], reverse=True)
        print("\n前区号码出现频率排行榜（前15）：")
        for i, (num, count) in enumerate(front_freq[:15], 1):
            percentage = (count / len(self.lottery_data)) * 100
            print(f"{i:2d}. 号码 {num:2d}: 出现 {count:3d} 次 ({percentage:.1f}%)")
        
        # 后区频率排序
        back_freq = sorted(back_counter.items(), key=lambda x: x[1], reverse=True)
        print("\n后区号码出现频率排行榜：")
        for i, (num, count) in enumerate(back_freq, 1):
            percentage = (count / len(self.lottery_data)) * 100
            print(f"{i:2d}. 号码 {num:2d}: 出现 {count:3d} 次 ({percentage:.1f}%)")
        
        return front_counter, back_counter
    
    def analyze_patterns(self):
        """分析号码规律"""
        print("\n=== 号码规律分析 ===")
        
        # 奇偶分布分析（前区）
        odd_even_dist = defaultdict(int)
        sum_dist = defaultdict(int)
        span_dist = defaultdict(int)
        
        for record in self.lottery_data:
            front_balls = record['front_balls']
            
            # 奇偶分析
            odd_count = sum(1 for x in front_balls if x % 2 == 1)
            even_count = 5 - odd_count
            odd_even_dist[f"{odd_count}奇{even_count}偶"] += 1
            
            # 和值分析
            total_sum = sum(front_balls)
            sum_range = f"{(total_sum//10)*10}-{(total_sum//10)*10+9}"
            sum_dist[sum_range] += 1
            
            # 跨度分析
            span = max(front_balls) - min(front_balls)
            span_range = f"{(span//5)*5}-{(span//5)*5+4}"
            span_dist[span_range] += 1
        
        print("\n前区奇偶分布统计：")
        for pattern, count in sorted(odd_even_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.lottery_data)) * 100
            print(f"{pattern}: {count} 次 ({percentage:.1f}%)")
        
        print("\n前区和值分布统计：")
        for sum_range, count in sorted(sum_dist.items(), key=lambda x: int(x[0].split('-')[0])):
            percentage = (count / len(self.lottery_data)) * 100
            print(f"{sum_range}: {count} 次 ({percentage:.1f}%)")
        
        print("\n前区跨度分布统计：")
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
            front_str = " ".join([f"{x:2d}" for x in record['front_balls']])
            back_str = " ".join([f"{x:2d}" for x in record['back_balls']])
            print(f"{record['period']}: {front_str} | {back_str}")
        
        # 冷热号分析
        front_counter = Counter()
        back_counter = Counter()
        
        for record in recent_10:
            for front in record['front_balls']:
                front_counter[front] += 1
            for back in record['back_balls']:
                back_counter[back] += 1
        
        print(f"\n最近10期前区热号（出现2次及以上）：")
        hot_fronts = [num for num, count in front_counter.items() if count >= 2]
        if hot_fronts:
            hot_fronts.sort()
            print(" ".join([f"{x:2d}" for x in hot_fronts]))
        else:
            print("无")
        
        print(f"\n最近10期后区热号（出现2次及以上）：")
        hot_backs = [num for num, count in back_counter.items() if count >= 2]
        if hot_backs:
            hot_backs.sort()
            print(" ".join([f"{x:2d}" for x in hot_backs]))
        else:
            print("无")
    
    def generate_recommendations(self, num_sets=8):
        """生成推荐号码（基于智能分析的动态推荐）"""
        print(f"\n=== 生成 {num_sets} 组推荐号码 ===")
        
        if not self.lottery_data:
            print("无数据，无法生成推荐")
            return []
        
        # 统计频率
        front_counter = Counter()
        back_counter = Counter()
        
        for record in self.lottery_data:
            for front in record['front_balls']:
                front_counter[front] += 1
            for back in record['back_balls']:
                back_counter[back] += 1
        
        # 确保所有号码都有记录
        for i in range(1, 36):  # 前区1-35
            if i not in front_counter:
                front_counter[i] = 0
                
        for i in range(1, 13):  # 后区1-12
            if i not in back_counter:
                back_counter[i] = 0
        
        # 获取频率排序
        front_freq_sorted = sorted(front_counter.items(), key=lambda x: x[1], reverse=True)
        back_freq_sorted = sorted(back_counter.items(), key=lambda x: x[1], reverse=True)
        
        # 分层分组：高频、中频、低频
        total_fronts = len(front_freq_sorted)
        high_cutoff = max(8, total_fronts // 3)
        mid_cutoff = max(16, 2 * total_fronts // 3)
        
        high_freq_fronts = [num for num, _ in front_freq_sorted[:high_cutoff]]
        mid_freq_fronts = [num for num, _ in front_freq_sorted[high_cutoff:mid_cutoff]]
        low_freq_fronts = [num for num, _ in front_freq_sorted[mid_cutoff:]]
        
        # 后区分组
        high_freq_backs = [num for num, _ in back_freq_sorted[:6]]
        mid_freq_backs = [num for num, _ in back_freq_sorted[6:]]
        
        print(f"高频前区({len(high_freq_fronts)}个): {sorted(high_freq_fronts)}")
        print(f"中频前区({len(mid_freq_fronts)}个): {sorted(mid_freq_fronts)}")
        print(f"低频前区({len(low_freq_fronts)}个): {sorted(low_freq_fronts)}")
        print(f"高频后区: {sorted(high_freq_backs)}")
        print(f"中频后区: {sorted(mid_freq_backs)}")
        
        recommendations = []
        
        # 定义多种智能选号策略
        strategies = [
            {
                'name': '高频主导',
                'front_high': 3, 'front_mid': 2, 'front_low': 0,
                'back_high': 2, 'back_mid': 0,
                'description': '基于最高频号码的稳定组合'
            },
            {
                'name': '均衡分布', 
                'front_high': 2, 'front_mid': 2, 'front_low': 1,
                'back_high': 1, 'back_mid': 1,
                'description': '高中低频均衡的平衡组合'
            },
            {
                'name': '中频优先',
                'front_high': 2, 'front_mid': 3, 'front_low': 0, 
                'back_high': 1, 'back_mid': 1,
                'description': '中频主导的稳健组合'
            },
            {
                'name': '冷热结合',
                'front_high': 2, 'front_mid': 1, 'front_low': 2,
                'back_high': 1, 'back_mid': 1,
                'description': '热号与冷号结合的对冲组合'
            },
            {
                'name': '超高频',
                'front_high': 4, 'front_mid': 1, 'front_low': 0,
                'back_high': 2, 'back_mid': 0,
                'description': '超高频号码的激进组合'
            },
            {
                'name': '低频反选',
                'front_high': 1, 'front_mid': 2, 'front_low': 2,
                'back_high': 0, 'back_mid': 2,
                'description': '低频号码的反向思维组合'
            },
            {
                'name': '随机均衡',
                'front_high': 2, 'front_mid': 2, 'front_low': 1,
                'back_high': 1, 'back_mid': 1,
                'description': '各频段随机均衡组合'
            },
            {
                'name': '奇偶优化',
                'front_high': 2, 'front_mid': 2, 'front_low': 1,
                'back_high': 1, 'back_mid': 1,
                'description': '考虑奇偶平衡的优化组合'
            }
        ]
        
        import random
        random.seed(42)  # 固定种子，确保结果可重现
        
        for i, strategy in enumerate(strategies[:num_sets]):
            selected_fronts = []
            
            # 从各频段选择前区号码
            front_pools = [
                (high_freq_fronts, strategy['front_high']),
                (mid_freq_fronts, strategy['front_mid']),
                (low_freq_fronts, strategy['front_low'])
            ]
            
            for pool, count in front_pools:
                if count > 0 and pool:
                    actual_count = min(count, len(pool))
                    if len(pool) >= actual_count:
                        if strategy['name'] == '奇偶优化':
                            selected_from_pool = self._select_with_odd_even_balance(pool, actual_count, selected_fronts, target_total=5)
                        else:
                            selected_from_pool = random.sample(pool, actual_count)
                        selected_fronts.extend(selected_from_pool)
            
            # 确保有5个前区号码
            while len(selected_fronts) < 5:
                all_available = set(high_freq_fronts + mid_freq_fronts + low_freq_fronts) - set(selected_fronts)
                if all_available:
                    selected_fronts.append(random.choice(list(all_available)))
                else:
                    remaining = set(range(1, 36)) - set(selected_fronts)
                    if remaining:
                        selected_fronts.append(random.choice(list(remaining)))
                    else:
                        break
            
            selected_fronts = sorted(selected_fronts[:5])
            
            # 选择后区号码
            selected_backs = []
            back_pools = [
                (high_freq_backs, strategy['back_high']),
                (mid_freq_backs, strategy['back_mid'])
            ]
            
            for pool, count in back_pools:
                if count > 0 and pool:
                    actual_count = min(count, len(pool))
                    if len(pool) >= actual_count:
                        selected_from_pool = random.sample(pool, actual_count)
                        selected_backs.extend(selected_from_pool)
            
            # 确保有2个后区号码
            while len(selected_backs) < 2:
                all_available = set(high_freq_backs + mid_freq_backs) - set(selected_backs)
                if all_available:
                    selected_backs.append(random.choice(list(all_available)))
                else:
                    remaining = set(range(1, 13)) - set(selected_backs)
                    if remaining:
                        selected_backs.append(random.choice(list(remaining)))
                    else:
                        break
            
            selected_backs = sorted(selected_backs[:2])
            
            # 计算组合特征
            odd_count = sum(1 for x in selected_fronts if x % 2 == 1)
            even_count = 5 - odd_count
            total_sum = sum(selected_fronts)
            span = max(selected_fronts) - min(selected_fronts)
            
            recommendations.append({
                'front_balls': selected_fronts,
                'back_balls': selected_backs,
                'description': strategy['description'],
                'strategy': strategy['name'],
                'odd_even': f"{odd_count}奇{even_count}偶",
                'sum': total_sum,
                'span': span
            })
        
        print("\n基于智能策略的推荐号码：")
        for i, rec in enumerate(recommendations, 1):
            front_str = " ".join([f"{x:02d}" for x in rec['front_balls']])
            back_str = " ".join([f"{x:02d}" for x in rec['back_balls']])
            print(f"推荐 {i}: {front_str} | {back_str}")
            print(f"       策略: {rec['strategy']} | {rec['odd_even']} | 和值:{rec['sum']} | 跨度:{rec['span']}")
            print(f"       说明: {rec['description']}")
        
        return recommendations
    
    def _select_with_odd_even_balance(self, pool, count, existing_numbers, target_total=5):
        """在选择时考虑奇偶平衡"""
        if count <= 0:
            return []
            
        existing_odd = sum(1 for x in existing_numbers if x % 2 == 1)
        existing_even = len(existing_numbers) - existing_odd
        
        # 目标：5个球中2-3个奇数比较平衡
        target_total_odd = 3 if len(existing_numbers) + count <= target_total else 2
        needed_odd = max(0, target_total_odd - existing_odd)
        needed_even = count - needed_odd
        
        odd_pool = [x for x in pool if x % 2 == 1]
        even_pool = [x for x in pool if x % 2 == 0]
        
        selected = []
        
        # 选择奇数
        import random
        if needed_odd > 0 and odd_pool:
            actual_odd = min(needed_odd, len(odd_pool))
            selected.extend(random.sample(odd_pool, actual_odd))
        
        # 选择偶数
        if needed_even > 0 and even_pool:
            actual_even = min(needed_even, len(even_pool))
            selected.extend(random.sample(even_pool, actual_even))
        
        # 如果还不够，从剩余的球中补充
        while len(selected) < count and len(selected) < len(pool):
            remaining = [x for x in pool if x not in selected]
            if remaining:
                selected.append(random.choice(remaining))
            else:
                break
        
        return selected[:count]
    
    def visualize_frequency(self, save_plots=True):
        """可视化频率分析"""
        if not self.lottery_data:
            print("无数据，无法生成图表")
            return
        
        # 统计频率
        front_counter = Counter()
        back_counter = Counter()
        
        for record in self.lottery_data:
            for front in record['front_balls']:
                front_counter[front] += 1
            for back in record['back_balls']:
                back_counter[back] += 1
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
        
        # 前区频率图
        front_nums = list(range(1, 36))
        front_freqs = [front_counter.get(num, 0) for num in front_nums]
        
        bars1 = ax1.bar(front_nums, front_freqs, color='red', alpha=0.7)
        ax1.set_title('前区号码出现频率分布', fontsize=16, fontweight='bold')
        ax1.set_xlabel('前区号码', fontsize=12)
        ax1.set_ylabel('出现次数', fontsize=12)
        ax1.set_xticks(front_nums)
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar, freq in zip(bars1, front_freqs):
            if freq > 0:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                        str(freq), ha='center', va='bottom', fontsize=8)
        
        # 后区频率图
        back_nums = list(range(1, 13))
        back_freqs = [back_counter.get(num, 0) for num in back_nums]
        
        bars2 = ax2.bar(back_nums, back_freqs, color='blue', alpha=0.7)
        ax2.set_title('后区号码出现频率分布', fontsize=16, fontweight='bold')
        ax2.set_xlabel('后区号码', fontsize=12)
        ax2.set_ylabel('出现次数', fontsize=12)
        ax2.set_xticks(back_nums)
        ax2.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar, freq in zip(bars2, back_freqs):
            if freq > 0:
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                        str(freq), ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        if save_plots:
            plt.savefig('super_lotto_frequency_analysis.png', dpi=300, bbox_inches='tight')
            print("频率分析图表已保存为 super_lotto_frequency_analysis.png")
        
        plt.show()
    
    def get_lottery_rules(self):
        """获取大乐透游戏规则"""
        rules = """
        === 大乐透游戏规则 ===
        
        1. 号码范围：
           - 前区：01-35，选择5个号码
           - 后区：01-12，选择2个号码
        
        2. 中奖等级：
           一等奖：5个前区号码 + 2个后区号码（浮动奖金，1000万元起）
           二等奖：5个前区号码 + 1个后区号码（浮动奖金）
           三等奖：5个前区号码（固定10000元）
           四等奖：4个前区号码 + 2个后区号码（固定3000元）
           五等奖：4个前区号码 + 1个后区号码（固定300元）
           六等奖：3个前区号码 + 2个后区号码（固定200元）
           七等奖：4个前区号码（固定100元）
           八等奖：3个前区号码 + 1个后区号码 或 2个前区号码 + 2个后区号码（固定15元）
           九等奖：3个前区号码 或 1个前区号码 + 2个后区号码 或 2个前区号码 + 1个后区号码 或 2个后区号码（固定5元）
        
        3. 开奖时间：每周一、三、六晚20:30
        
        4. 投注方式：
           - 单式投注：手动选择号码
           - 复式投注：选择6个以上前区号码或3个后区号码进行组合
           - 机选投注：系统随机选择号码
        
        5. 中奖概率：
           一等奖：1/21,425,712
           二等奖：1/1,785,476
           三等奖：1/109,389
           
        注意：彩票投注有风险，请理性购彩，量力而行！
        """
        print(rules)
    
    def generate_analysis_report(self, filename="super_lotto_analysis_report.md"):
        """生成完整的分析报告文件"""
        print(f"正在生成分析报告: {filename}")
        
        if not self.lottery_data:
            print("无数据，无法生成报告")
            return
        
        # 执行所有分析
        front_counter, back_counter = self._get_frequency_analysis()
        patterns_data = self._get_patterns_analysis()
        trends_data = self._get_trends_analysis()
        recommendations = self.generate_recommendations(num_sets=8)
        
        # 生成报告内容 - 使用UTC+8时区
        current_time = self.format_time_utc8()
        
        report_content = f"""# 🎯 大乐透数据分析报告

## 📊 报告信息
- **生成时间**: {current_time} (UTC+8)
- **数据期数**: 共 {len(self.lottery_data)} 期
- **最新期号**: {self.lottery_data[0]['period'] if self.lottery_data else 'N/A'}
- **数据来源**: 国家体彩中心官方API

## ⚠️ 重要免责声明
**本分析报告仅供学习和研究使用，彩票开奖完全随机，历史数据无法预测未来结果。请理性购彩，量力而行！**

---

## 📈 最新开奖信息

"""
        
        # 添加最近5期开奖信息
        if len(self.lottery_data) >= 5:
            report_content += "### 最近5期开奖号码\n\n"
            for i, record in enumerate(self.lottery_data[:5]):
                front_str = " ".join([f"{x:02d}" for x in record['front_balls']])
                back_str = " ".join([f"{x:02d}" for x in record['back_balls']])
                report_content += f"**{record['period']}期** ({record['date']}): {front_str} | **{back_str}**\n\n"
        
        # 添加号码频率分析
        report_content += """---

## 🔥 号码频率分析

### 前区号码出现频率排行榜（前20名）

| 排名 | 号码 | 出现次数 | 出现频率 |
|------|------|----------|----------|
"""
        
        front_freq = sorted(front_counter.items(), key=lambda x: x[1], reverse=True)
        for i, (num, count) in enumerate(front_freq[:20], 1):
            percentage = (count / len(self.lottery_data)) * 100
            report_content += f"| {i:02d} | **{num:02d}** | {count} | {percentage:.1f}% |\n"
        
        report_content += """
### 后区号码出现频率排行榜

| 排名 | 号码 | 出现次数 | 出现频率 |
|------|------|----------|----------|
"""
        
        back_freq = sorted(back_counter.items(), key=lambda x: x[1], reverse=True)
        for i, (num, count) in enumerate(back_freq, 1):
            percentage = (count / len(self.lottery_data)) * 100
            report_content += f"| {i:02d} | **{num:02d}** | {count} | {percentage:.1f}% |\n"
        
        # 添加规律分析
        report_content += f"""
---

## 📊 号码规律分析

### 前区奇偶分布统计

{patterns_data['odd_even']}

### 前区和值分布统计

{patterns_data['sum_dist']}

### 前区跨度分布统计

{patterns_data['span_dist']}

---

## 📉 走势分析

### 最近10期开奖记录

{trends_data['recent_draws']}

### 热号分析

**最近10期前区热号（出现2次及以上）**: {trends_data['hot_fronts']}

**最近10期后区热号（出现2次及以上）**: {trends_data['hot_backs']}

---

## 🎯 智能推荐号码

**⚠️ 以下推荐号码仅基于历史统计分析，不保证中奖，请理性参考！**

"""
        
        for i, rec in enumerate(recommendations, 1):
            front_str = " ".join([f"{x:02d}" for x in rec['front_balls']])
            back_str = " ".join([f"{x:02d}" for x in rec['back_balls']])
            report_content += f"**推荐组合 {i}** ({rec['strategy']}): {front_str} | **{back_str}**\n"
            report_content += f"- 特征: {rec['odd_even']} | 和值:{rec['sum']} | 跨度:{rec['span']}\n"
            report_content += f"- 说明: {rec['description']}\n\n"
        
        # 添加使用说明和提醒
        report_content += f"""---

## 📋 使用说明

### 数据更新频率
- 本报告每天自动更新一次
- 数据来源于国家体彩中心官方API
- 更新时间：每天晚上23:00 (UTC+8)

### 分析方法说明
1. **频率分析**: 统计每个号码在历史开奖中的出现次数
2. **规律分析**: 分析前区奇偶分布、和值分布、跨度分布等规律
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

*报告生成时间: {current_time} (UTC+8)*  
*数据来源: 国家体彩中心官方网站*  
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
        front_counter = Counter()
        back_counter = Counter()
        
        for record in self.lottery_data:
            for front in record['front_balls']:
                front_counter[front] += 1
            for back in record['back_balls']:
                back_counter[back] += 1
        
        return front_counter, back_counter
    
    def _get_patterns_analysis(self):
        """内部方法：获取规律分析数据"""
        odd_even_dist = defaultdict(int)
        sum_dist = defaultdict(int)
        span_dist = defaultdict(int)
        
        for record in self.lottery_data:
            front_balls = record['front_balls']
            
            # 奇偶分析
            odd_count = sum(1 for x in front_balls if x % 2 == 1)
            even_count = 5 - odd_count
            odd_even_dist[f"{odd_count}奇{even_count}偶"] += 1
            
            # 和值分析
            total_sum = sum(front_balls)
            sum_range = f"{(total_sum//10)*10}-{(total_sum//10)*10+9}"
            sum_dist[sum_range] += 1
            
            # 跨度分析
            span = max(front_balls) - min(front_balls)
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
                'hot_fronts': '无',
                'hot_backs': '无'
            }
        
        recent_10 = self.lottery_data[:10]
        
        # 格式化最近10期
        recent_draws = "| 期号 | 开奖日期 | 前区号码 | 后区号码 |\n|------|----------|----------|----------|\n"
        for record in recent_10:
            front_str = " ".join([f"{x:02d}" for x in record['front_balls']])
            back_str = " ".join([f"{x:02d}" for x in record['back_balls']])
            recent_draws += f"| {record['period']} | {record['date']} | {front_str} | **{back_str}** |\n"
        
        # 冷热号分析
        front_counter = Counter()
        back_counter = Counter()
        
        for record in recent_10:
            for front in record['front_balls']:
                front_counter[front] += 1
            for back in record['back_balls']:
                back_counter[back] += 1
        
        hot_fronts = [num for num, count in front_counter.items() if count >= 2]
        hot_backs = [num for num, count in back_counter.items() if count >= 2]
        
        hot_fronts_str = " ".join([f"{x:02d}" for x in sorted(hot_fronts)]) if hot_fronts else "无"
        hot_backs_str = " ".join([f"{x:02d}" for x in sorted(hot_backs)]) if hot_backs else "无"
        
        return {
            'recent_draws': recent_draws,
            'hot_fronts': hot_fronts_str,
            'hot_backs': hot_backs_str
        }

def main():
    """主函数"""
    # 显示免责声明
    print("=" * 80)
    print("🎯 大乐透数据分析系统")
    print("=" * 80)
    print("⚠️  重要免责声明：")
    print("• 彩票开奖完全随机，历史数据无法预测未来")
    print("• 本分析仅供学习参考，不构成投注建议")
    print("• 请理性购彩，量力而行，未满18周岁禁止购买")
    print("• 使用本软件产生的任何后果由用户自行承担")
    print("=" * 80)
    
    analyzer = SuperLottoAnalyzer()
    
    print("\n大乐透开奖数据分析系统")
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
    front_counter, back_counter = analyzer.analyze_frequency()
    analyzer.analyze_patterns()
    analyzer.analyze_trends()
    
    # 生成推荐号码
    recommendations = analyzer.generate_recommendations(num_sets=8)
    
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