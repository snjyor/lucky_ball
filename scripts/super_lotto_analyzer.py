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
import os
import hjson
import random

# 添加DrissionPage导入
try:
    from DrissionPage import Chromium, ChromiumOptions
    DRISSIONPAGE_AVAILABLE = True
    print("✅ DrissionPage 可用，将使用浏览器模式获取数据")
except ImportError:
    DRISSIONPAGE_AVAILABLE = False
    print("⚠️  DrissionPage 不可用，将使用传统requests模式")

warnings.filterwarnings('ignore')

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class SuperLottoAnalyzer:
    """大乐透分析器"""
    
    def __init__(self):
        self.base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
        
        # 多个真实的User-Agent，用于轮换
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        
        self.session = requests.Session()
        self.lottery_data = []
        # 设置UTC+8时区
        self.utc8_tz = timezone(timedelta(hours=8))
        
        # DrissionPage相关初始化
        self.browser = None
        self.tab = None
        self.use_drissionpage = DRISSIONPAGE_AVAILABLE
        
        # 配置session
        self._setup_session()
        
    def _setup_session(self):
        """配置session的基本设置"""
        # 设置连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 设置基本headers
        self._update_headers()
    
    def _update_headers(self):
        """更新请求头，使用随机User-Agent和正确的referer等信息"""
        user_agent = random.choice(self.user_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Origin': 'https://static.sporttery.cn',
            'Referer': 'https://static.sporttery.cn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Ch-Ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Priority': 'u=1, i',
            'X-Full-Ref': '//www.lottery.gov.cn/kj/kjlb.html?dlt'
        }
        
        self.session.headers.update(headers)
        print(f"🔄 更新User-Agent: {user_agent[:50]}...")
        print(f"🔄 设置Origin: https://static.sporttery.cn")
        print(f"🔄 设置Referer: https://static.sporttery.cn/")
    
    def get_current_time_utc8(self):
        """获取UTC+8时区的当前时间"""
        return datetime.now(self.utc8_tz)
        
    def format_time_utc8(self, dt=None):
        """格式化UTC+8时区的时间"""
        if dt is None:
            dt = self.get_current_time_utc8()
        return dt.strftime('%Y年%m月%d日 %H:%M:%S')
    
    def get_max_pages(self):
        """获取总页数，增强错误处理"""
        print("正在获取总页数...")
        
        max_retries = 8  # 增加重试次数
        base_delay = 3   # 增加基础延时
        
        for attempt in range(max_retries):
            try:
                # 每次尝试都更新headers
                self._update_headers()
                
                params = {
                    'gameNo': '85',  # 大乐透
                    'provinceId': '0',
                    'pageSize': '30',
                    'isVerify': '1',
                    'pageNo': '1'
                }
                
                # 增加延时，特别是对567错误
                if attempt > 0:
                    if attempt <= 2:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                    else:
                        # 对于后续重试，使用更长的延时
                        delay = 15 + random.uniform(0, 10)
                    print(f"⏳ 第 {attempt + 1} 次尝试，等待 {delay:.1f} 秒...")
                    time.sleep(delay)
                else:
                    # 初始延时也增加
                    time.sleep(random.uniform(3, 6))
                
                print(f"🌐 正在请求API... (尝试 {attempt + 1}/{max_retries})")
                response = self.session.get(self.base_url, params=params, timeout=45)  # 增加超时时间
                
                print(f"📡 响应状态码: {response.status_code}")
                
                # 特殊处理567错误
                if response.status_code == 567:
                    print(f"⚠️  遇到567错误，这通常是服务器反爬虫机制")
                    if attempt < max_retries - 1:
                        print(f"🔄 将在更长延时后重试...")
                        continue
                    else:
                        print("❌ 多次尝试后仍然是567错误，使用默认页数")
                        return 100
                
                # 处理其他HTTP错误
                if response.status_code == 429:
                    print(f"🚫 遇到429限流错误，延长等待时间...")
                    time.sleep(20 + random.uniform(0, 10))
                    continue
                elif response.status_code == 403:
                    print(f"🚫 遇到403禁止访问错误，可能需要更换请求头...")
                    continue
                
                response.raise_for_status()
                
                data = response.json()
                print(f"📊 API响应: isSuccess={data.get('isSuccess')}, errorMessage={data.get('errorMessage')}")
                
                # 特殊处理：某些情况下errorMessage是"处理成功"但isSuccess是false
                if not data.get('isSuccess', False):
                    error_msg = data.get('errorMessage', '未知错误')
                    if error_msg == '处理成功':
                        print("✅ API返回'处理成功'，继续处理数据")
                    else:
                        print(f"❌ API返回错误: {error_msg}")
                        if attempt < max_retries - 1:
                            continue
                        else:
                            return 100
                
                value = data.get('value', {})
                total_pages = value.get('pages', 100)
                total_records = value.get('total', 0)
                
                print(f"✅ 成功获取页数信息: 总记录 {total_records} 条，共 {total_pages} 页")
                return total_pages
                
            except requests.exceptions.Timeout:
                print(f"⏰ 请求超时 (尝试 {attempt + 1}/{max_retries})")
            except requests.exceptions.ConnectionError:
                print(f"🔌 连接错误 (尝试 {attempt + 1}/{max_retries})")
            except requests.exceptions.HTTPError as e:
                print(f"🌐 HTTP错误: {e} (尝试 {attempt + 1}/{max_retries})")
            except Exception as e:
                print(f"❌ 获取总页数时出错: {e} (尝试 {attempt + 1}/{max_retries})")
            
            if attempt < max_retries - 1:
                print("🔄 准备重试...")
        
        print("⚠️  所有尝试都失败，使用默认页数 100")
        return 100
    
    def fetch_lottery_data(self, max_pages=None):
        """抓取大乐透数据，优先使用DrissionPage，失败时回退到requests"""
        print("🎯 开始抓取大乐透数据...")
        
        # 优先尝试DrissionPage模式
        if self.use_drissionpage:
            print("🚀 尝试使用DrissionPage模式...")
            success = self.fetch_lottery_data_with_drissionpage(max_pages)
            if success:
                print("✅ DrissionPage模式成功获取数据")
                return True
            else:
                print("⚠️  DrissionPage模式失败，回退到requests模式")
                self.use_drissionpage = False
        
        # 回退到原有的requests模式
        print("🔄 使用传统requests模式...")
        return self.fetch_lottery_data_with_requests(max_pages)
    
    def fetch_lottery_data_with_requests(self, max_pages=None):
        """使用requests抓取大乐透数据（原有方法重命名）"""
        print("🎯 使用requests模式抓取大乐透数据...")
        
        if max_pages is None:
            max_pages = self.get_max_pages()
        
        print(f"📄 计划抓取 {max_pages} 页数据")
        
        all_data = []
        failed_pages = []
        consecutive_failures = 0
        max_consecutive_failures = 5  # 连续失败阈值
        
        for page in range(1, max_pages + 1):
            print(f"\n📖 正在抓取第 {page}/{max_pages} 页...")
            
            # 每次请求前更新headers
            if page % 10 == 1:  # 每10页更新一次headers
                self._update_headers()
            
            max_retries = 6  # 增加单页重试次数
            page_success = False
            
            for attempt in range(max_retries):
                try:
                    params = {
                        'gameNo': '85',
                        'provinceId': '0',
                        'pageSize': '30',
                        'isVerify': '1',
                        'pageNo': str(page)
                    }
                    
                    # 增加延时策略
                    if attempt > 0:
                        if attempt <= 2:
                            delay = 3 * (2 ** attempt) + random.uniform(0, 2)
                        else:
                            delay = 20 + random.uniform(0, 10)
                        print(f"⏳ 第 {attempt + 1} 次尝试，等待 {delay:.1f} 秒...")
                        time.sleep(delay)
                    else:
                        # 页面间的基础延时
                        base_delay = random.uniform(2, 5)
                        if consecutive_failures > 0:
                            base_delay += consecutive_failures * 2  # 连续失败时增加延时
                        time.sleep(base_delay)
                    
                    response = self.session.get(self.base_url, params=params, timeout=45)
                    
                    # 特殊处理567错误
                    if response.status_code == 567:
                        print(f"⚠️  第{page}页遇到567错误")
                        if attempt < max_retries - 1:
                            print(f"🔄 将延长等待时间后重试...")
                            time.sleep(15 + random.uniform(0, 10))
                            continue
                        else:
                            print(f"❌ 第{page}页多次567错误，跳过此页")
                            failed_pages.append(page)
                            break
                    
                    # 处理其他HTTP错误
                    if response.status_code == 429:
                        print(f"🚫 第{page}页遇到429限流错误")
                        time.sleep(25 + random.uniform(0, 15))
                        continue
                    elif response.status_code == 403:
                        print(f"🚫 第{page}页遇到403错误，更新请求头...")
                        self._update_headers()
                        time.sleep(10 + random.uniform(0, 5))
                        continue
                    
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # 检查API响应
                    if not data.get('isSuccess', False):
                        error_msg = data.get('errorMessage', '未知错误')
                        if error_msg == '处理成功':
                            print("✅ API返回'处理成功'，继续处理")
                        else:
                            print(f"❌ 第{page}页API错误: {error_msg}")
                            if attempt < max_retries - 1:
                                continue
                            else:
                                failed_pages.append(page)
                                break
                    
                    # 处理数据
                    value = data.get('value', {})
                    page_data = value.get('list', [])
                    
                    if not page_data:
                        print(f"⚠️  第{page}页无数据")
                        if attempt < max_retries - 1:
                            continue
                        else:
                            failed_pages.append(page)
                            break
                    
                    # 解析并存储数据
                    parsed_count = 0
                    for item in page_data:
                        try:
                            # 解析期号
                            period = item.get('lotteryDrawNum', '')
                            
                            # 解析开奖时间
                            draw_time = item.get('lotteryDrawTime', '')
                            # 提取日期部分
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', draw_time)
                            if not date_match:
                                continue
                            draw_date = date_match.group(1)
                            
                            # 解析开奖号码
                            draw_result = item.get('lotteryDrawResult', '')
                            if not draw_result:
                                continue
                            
                            # 分割号码：前5个是前区，后2个是后区
                            numbers = draw_result.split(' ')
                            if len(numbers) < 7:
                                continue
                            
                            front_balls = [int(x) for x in numbers[:5]]
                            back_balls = [int(x) for x in numbers[5:7]]
                            
                            # 解析奖级信息
                            prize_list = item.get('prizeLevelList', [])
                            first_prize_count = 0
                            first_prize_amount = 0
                            second_prize_count = 0
                            second_prize_amount = 0
                            
                            for prize in prize_list:
                                if prize.get('awardLevel') == '一等奖':
                                    first_prize_count = prize.get('awardLevelNum', 0)
                                    first_prize_amount = prize.get('awardMoney', 0)
                                elif prize.get('awardLevel') == '二等奖':
                                    second_prize_count = prize.get('awardLevelNum', 0)
                                    second_prize_amount = prize.get('awardMoney', 0)
                            
                            # 解析其他信息
                            sales_amount = item.get('drawMoney', 0)
                            pool_amount = item.get('poolBalanceAfterdraw', 0)
                            
                            # 存储数据
                            lottery_record = {
                                'period': period,
                                'date': draw_date,
                                'front_balls': front_balls,
                                'back_balls': back_balls,
                                'first_prize_count': first_prize_count,
                                'first_prize_amount': first_prize_amount,
                                'second_prize_count': second_prize_count,
                                'second_prize_amount': second_prize_amount,
                                'sales_amount': sales_amount,
                                'pool_amount': pool_amount
                            }
                            
                            all_data.append(lottery_record)
                            parsed_count += 1
                            
                        except Exception as e:
                            print(f"⚠️  解析记录时出错: {e}")
                            continue
                    
                    page_success = True
                    consecutive_failures = 0  # 重置连续失败计数
                    print(f"✅ 第{page}页成功，解析 {parsed_count} 条有效记录")
                    break
                    
                except requests.exceptions.Timeout:
                    print(f"⏰ 第{page}页请求超时 (尝试 {attempt + 1}/{max_retries})")
                except requests.exceptions.ConnectionError:
                    print(f"🔌 第{page}页连接错误 (尝试 {attempt + 1}/{max_retries})")
                except Exception as e:
                    print(f"❌ 第{page}页出错: {e} (尝试 {attempt + 1}/{max_retries})")
            
            if not page_success:
                consecutive_failures += 1
                print(f"❌ 第{page}页最终失败 (连续失败: {consecutive_failures})")
                
                # 如果连续失败太多，提前结束
                if consecutive_failures >= max_consecutive_failures:
                    print(f"⚠️  连续失败 {consecutive_failures} 页，提前结束抓取")
                    break
        
        print(f"\n📊 requests数据抓取完成:")
        print(f"✅ 成功获取 {len(all_data)} 条记录")
        if failed_pages:
            print(f"❌ 失败页面: {failed_pages[:10]}{'...' if len(failed_pages) > 10 else ''} (共{len(failed_pages)}页)")
        
        self.lottery_data = all_data
        return len(all_data) > 0
    
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
    
    def save_data(self, filename="data/super_lotto_data.json"):
        """保存数据到文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.lottery_data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}")
    
    def load_data(self, filename="data/super_lotto_data.json"):
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
            # 确保目录存在
            os.makedirs('pics', exist_ok=True)
            plt.savefig('pics/super_lotto_frequency_analysis.png', dpi=300, bbox_inches='tight')
            print("频率分析图表已保存为 pics/super_lotto_frequency_analysis.png")
    
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
    
    def generate_analysis_report(self, filename="reports/super_lotto_analysis_report.md"):
        """生成完整的分析报告文件"""
        print(f"正在生成分析报告: {filename}")
        
        if not self.lottery_data:
            print("无数据，无法生成报告")
            return
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
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
**本分析报告仅供学习和研究使用，彩票开奖完全随机，历史数据无法预测未来。请理性购彩，量力而行！**

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

    def generate_aggregated_data_hjson(self, filename="data/super_lotto_aggregated_data.hjson"):
        """生成聚合分析数据的HJSON文件，包含详细注释供AI理解数据用途"""
        print(f"正在生成聚合数据文件: {filename}")
        
        if not self.lottery_data:
            print("无数据，无法生成聚合数据文件")
            return
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # 获取所有分析数据
        front_counter, back_counter = self._get_frequency_analysis()
        patterns_data = self._get_patterns_analysis_raw()
        trends_data = self._get_trends_analysis_raw()
        recommendations = self.generate_recommendations(num_sets=8)
        
        # 生成时间 UTC+8
        current_time = self.format_time_utc8()
        
        # 构建聚合数据结构
        aggregated_data = {
            "// 数据文件说明": "大乐透彩票数据聚合分析结果，包含频率、规律、走势等统计数据",
            "// 文件用途": "供AI系统理解数据含义并生成相应的数据可视化图表",
            "// 更新频率": "每天自动更新一次，与开奖数据同步",
            
            "metadata": {
                "// 元数据说明": "包含数据的基本信息和统计概况",
                "lottery_type": "大乐透",
                "lottery_type_en": "super_lotto", 
                "game_rules": "前区1-35选5个，后区1-12选2个",
                "generated_time": current_time,
                "timezone": "UTC+8",
                "total_periods": len(self.lottery_data),
                "latest_period": self.lottery_data[0]['period'] if self.lottery_data else None,
                "latest_date": self.lottery_data[0]['date'] if self.lottery_data else None,
                "data_source": "国家体彩中心官方API"
            },
            
            "frequency_analysis": {
                "// 频率分析说明": "统计每个号码在历史开奖中的出现次数和频率",
                "// 图表建议": "适合绘制柱状图、热力图、频率分布图",
                "// 可视化用途": "展示号码冷热程度，识别高频低频号码",
                
                "front_balls": {
                    "// 前区频率数据": "前区1-35的历史出现统计",
                    "// 数据结构": "number: 号码, count: 出现次数, frequency: 出现频率(%)",
                    "data": [
                        {
                            "number": num,
                            "count": front_counter.get(num, 0),
                            "frequency": round((front_counter.get(num, 0) / len(self.lottery_data)) * 100, 2)
                        } for num in range(1, 36)
                    ],
                    "// 统计摘要": "前区频率分析的关键指标",
                    "summary": {
                        "highest_freq_number": max(front_counter.items(), key=lambda x: x[1])[0] if front_counter else None,
                        "highest_freq_count": max(front_counter.items(), key=lambda x: x[1])[1] if front_counter else 0,
                        "lowest_freq_number": min(front_counter.items(), key=lambda x: x[1])[0] if front_counter else None,
                        "lowest_freq_count": min(front_counter.items(), key=lambda x: x[1])[1] if front_counter else 0,
                        "average_frequency": round(sum(front_counter.values()) / len(front_counter) if front_counter else 0, 2)
                    }
                },
                
                "back_balls": {
                    "// 后区频率数据": "后区1-12的历史出现统计", 
                    "// 数据结构": "number: 号码, count: 出现次数, frequency: 出现频率(%)",
                    "data": [
                        {
                            "number": num,
                            "count": back_counter.get(num, 0),
                            "frequency": round((back_counter.get(num, 0) / len(self.lottery_data)) * 100, 2)
                        } for num in range(1, 13)
                    ],
                    "// 统计摘要": "后区频率分析的关键指标",
                    "summary": {
                        "highest_freq_number": max(back_counter.items(), key=lambda x: x[1])[0] if back_counter else None,
                        "highest_freq_count": max(back_counter.items(), key=lambda x: x[1])[1] if back_counter else 0,
                        "lowest_freq_number": min(back_counter.items(), key=lambda x: x[1])[0] if back_counter else None,
                        "lowest_freq_count": min(back_counter.items(), key=lambda x: x[1])[1] if back_counter else 0,
                        "average_frequency": round(sum(back_counter.values()) / len(back_counter) if back_counter else 0, 2)
                    }
                }
            },
            
            "pattern_analysis": {
                "// 规律分析说明": "分析前区号码的奇偶分布、和值分布、跨度分布等规律",
                "// 图表建议": "适合绘制饼图、堆叠柱状图、分布直方图",
                "// 可视化用途": "展示号码组合的规律性和分布特征",
                "// 分析范围": "仅分析前区5个号码的规律",
                
                "odd_even_distribution": {
                    "// 奇偶分布": "前区5个号码中奇数偶数的分布情况",
                    "// 图表类型": "饼图或柱状图展示各种奇偶组合的出现频率",
                    "data": patterns_data['odd_even_dist'],
                    "total_periods": len(self.lottery_data)
                },
                
                "sum_distribution": {
                    "// 和值分布": "前区5个号码总和的分布区间统计",
                    "// 图表类型": "直方图或折线图展示和值的分布规律",
                    "// 分析意义": "帮助识别号码组合的和值趋势",
                    "data": patterns_data['sum_dist'],
                    "total_periods": len(self.lottery_data)
                },
                
                "span_distribution": {
                    "// 跨度分布": "前区最大号码与最小号码差值的分布统计",
                    "// 图表类型": "柱状图展示不同跨度范围的出现频率",
                    "// 分析意义": "反映号码选择的分散程度",
                    "data": patterns_data['span_dist'],
                    "total_periods": len(self.lottery_data)
                }
            },
            
            "trend_analysis": {
                "// 走势分析说明": "分析最近期数的号码走势和热号变化",
                "// 图表建议": "适合绘制时间序列图、热力图、趋势线图",
                "// 可视化用途": "展示短期内号码的冷热变化趋势",
                "// 分析周期": "最近10期开奖数据",
                
                "recent_draws": trends_data['recent_draws'],
                "hot_numbers": {
                    "// 热号定义": "最近10期中出现2次及以上的号码",
                    "// 图表类型": "标记图或高亮显示热号在走势图中的位置",
                    "front_hot_numbers": trends_data['hot_fronts'],
                    "back_hot_numbers": trends_data['hot_backs']
                }
            },
            
            "recommendations": {
                "// 推荐号码说明": "基于历史统计分析生成的8种策略推荐组合",
                "// 图表建议": "表格展示或卡片式布局展示推荐组合",
                "// 重要提醒": "仅供参考，彩票开奖完全随机",
                "// 策略说明": "包含高频主导、均衡分布、冷热结合等多种选号策略",
                
                "strategies": [
                    {
                        "strategy_name": rec['strategy'],
                        "description": rec['description'],
                        "front_balls": rec['front_balls'],
                        "back_balls": rec['back_balls'],
                        "characteristics": {
                            "odd_even_ratio": rec['odd_even'],
                            "sum_value": rec['sum'],
                            "span_value": rec['span']
                        }
                    } for rec in recommendations
                ],
                
                "strategy_summary": {
                    "total_strategies": len(recommendations),
                    "strategy_types": [rec['strategy'] for rec in recommendations]
                }
            },
            
            "visualization_suggestions": {
                "// 可视化建议": "针对不同数据类型的图表绘制建议",
                
                "frequency_charts": {
                    "chart_types": ["bar_chart", "heatmap", "bubble_chart"],
                    "description": "频率数据适合用柱状图展示排名，热力图展示分布，气泡图展示频率大小",
                    "special_note": "前区和后区需要分别绘制，因为号码范围不同"
                },
                
                "pattern_charts": {
                    "chart_types": ["pie_chart", "stacked_bar", "histogram"],
                    "description": "规律数据适合用饼图展示比例，堆叠柱状图展示分类，直方图展示分布"
                },
                
                "trend_charts": {
                    "chart_types": ["line_chart", "scatter_plot", "timeline"],
                    "description": "走势数据适合用折线图展示变化，散点图展示分布，时间轴展示历史"
                },
                
                "recommendation_display": {
                    "display_types": ["table", "card_layout", "grid_view"],
                    "description": "推荐数据适合用表格展示详情，卡片布局展示策略，网格视图展示组合",
                    "layout_note": "前区5个号码和后区2个号码需要分开显示"
                }
            }
        }
        
        # 保存HJSON文件
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                hjson.dump(aggregated_data, f, ensure_ascii=False, indent=2)
            print(f"聚合数据文件已保存到 {filename}")
        except Exception as e:
            print(f"保存聚合数据文件失败: {e}")
    
    def _get_patterns_analysis_raw(self):
        """内部方法：获取原始规律分析数据"""
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
        
        return {
            'odd_even_dist': dict(odd_even_dist),
            'sum_dist': dict(sum_dist),
            'span_dist': dict(span_dist)
        }
    
    def _get_trends_analysis_raw(self):
        """内部方法：获取原始趋势分析数据"""
        if len(self.lottery_data) < 10:
            return {
                'recent_draws': [],
                'hot_fronts': [],
                'hot_backs': []
            }
        
        recent_10 = self.lottery_data[:10]
        
        # 最近10期数据
        recent_draws = []
        for record in recent_10:
            recent_draws.append({
                'period': record['period'],
                'date': record['date'],
                'front_balls': record['front_balls'],
                'back_balls': record['back_balls']
            })
        
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
        
        return {
            'recent_draws': recent_draws,
            'hot_fronts': sorted(hot_fronts),
            'hot_backs': sorted(hot_backs)
        }

    def update_readme_recommendations(self, readme_path="README.md", timestamp=None):
        """更新README.md中的大乐透推荐号码"""
        print(f"正在更新README.md中的大乐透推荐号码...")
        
        if not self.lottery_data:
            print("无数据，无法更新README推荐号码")
            return
        
        try:
            # 生成推荐号码
            recommendations = self.generate_recommendations(num_sets=5)
            
            # 读取现有README内容
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用传入的时间戳或生成新的时间戳 UTC+8
            if timestamp:
                current_time = timestamp
            else:
                current_time = self.format_time_utc8()
            
            # 构建大乐透推荐号码内容
            dlt_recommendations_content = f"""
### 大乐透推荐 (更新时间: {current_time})

"""
            
            for i, rec in enumerate(recommendations, 1):
                front_str = " ".join([f"{x:02d}" for x in rec['front_balls']])
                back_str = " ".join([f"{x:02d}" for x in rec['back_balls']])
                dlt_recommendations_content += f"**推荐 {i}** ({rec['strategy']}): `{front_str}` + `{back_str}`  \n"
                dlt_recommendations_content += f"*{rec['description']} | {rec['odd_even']} | 和值:{rec['sum']} | 跨度:{rec['span']}*\n\n"
            
            # 查找双色球推荐部分，在其后添加大乐透推荐
            lines = content.split('\n')
            insert_index = -1
            
            # 查找双色球推荐部分的结束位置
            for i, line in enumerate(lines):
                if "双色球推荐" in line:
                    # 找到下一个H2或H3标题，或文件结束
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith('## ') and "推荐号码" not in lines[j]:
                            insert_index = j
                            break
                        elif lines[j].startswith('### ') and "大乐透推荐" in lines[j]:
                            # 如果已存在大乐透推荐，找到其结束位置
                            for k in range(j + 1, len(lines)):
                                if lines[k].startswith('## ') and "推荐号码" not in lines[k]:
                                    insert_index = k
                                    break
                            else:
                                insert_index = len(lines)
                            break
                    else:
                        insert_index = len(lines)
                    break
            
            if insert_index == -1:
                print("未找到双色球推荐部分，无法添加大乐透推荐")
                return
            
            # 检查是否已存在大乐透推荐
            existing_dlt_index = -1
            for i, line in enumerate(lines):
                if "大乐透推荐" in line:
                    existing_dlt_index = i
                    break
            
            if existing_dlt_index != -1:
                # 找到大乐透推荐部分的结束位置
                end_index = existing_dlt_index
                for i in range(existing_dlt_index + 1, len(lines)):
                    if lines[i].startswith('## ') and "推荐号码" not in lines[i]:
                        end_index = i
                        break
                else:
                    end_index = len(lines)
                
                # 替换现有大乐透推荐部分
                new_lines = lines[:existing_dlt_index] + dlt_recommendations_content.strip().split('\n') + lines[end_index:]
            else:
                # 在指定位置插入大乐透推荐
                new_lines = lines[:insert_index] + dlt_recommendations_content.strip().split('\n') + [''] + lines[insert_index:]
            
            new_content = '\n'.join(new_lines)
            
            # 写回文件
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"README.md中的大乐透推荐号码已更新")
            
        except Exception as e:
            print(f"更新README大乐透推荐号码失败: {e}")
    
    def _setup_drissionpage(self):
        """初始化DrissionPage浏览器"""
        if not DRISSIONPAGE_AVAILABLE:
            return False
            
        try:
            # 配置浏览器选项
            options = ChromiumOptions()
            options.headless(True)  # 无头模式，适合服务器环境
            options.set_argument('--no-sandbox')
            options.set_argument('--disable-dev-shm-usage')
            options.set_argument('--disable-gpu')
            options.set_argument('--disable-web-security')
            options.set_argument('--disable-features=VizDisplayCompositor')
            options.set_argument('--disable-extensions')
            options.set_argument('--disable-plugins')
            options.set_argument('--disable-images')  # 禁用图片加载，提高速度
            options.set_argument('--disable-javascript')  # 对于API请求，可以禁用JS
            
            # 设置用户代理
            user_agent = random.choice(self.user_agents)
            options.set_user_agent(user_agent)
            
            print(f"🚀 正在启动浏览器... (User-Agent: {user_agent[:50]}...)")
            
            # 创建浏览器实例
            self.browser = Chromium(options)
            self.tab = self.browser.latest_tab
            
            print("✅ 浏览器启动成功")
            return True
            
        except Exception as e:
            print(f"❌ 浏览器启动失败: {e}")
            self.use_drissionpage = False
            return False
    
    def _close_drissionpage(self):
        """关闭DrissionPage浏览器"""
        try:
            if self.browser:
                self.browser.quit()
                print("🔒 浏览器已关闭")
        except Exception as e:
            print(f"⚠️  关闭浏览器时出错: {e}")
    
    def fetch_lottery_data_with_drissionpage(self, max_pages=None):
        """使用DrissionPage获取大乐透数据"""
        print("🎯 使用DrissionPage模式抓取大乐透数据...")
        
        if not self._setup_drissionpage():
            print("❌ DrissionPage初始化失败，回退到requests模式")
            return self.fetch_lottery_data(max_pages)
        
        try:
            if max_pages is None:
                max_pages = self.get_max_pages_with_drissionpage()
            
            print(f"📄 计划抓取 {max_pages} 页数据")
            
            all_data = []
            failed_pages = []
            
            for page in range(1, max_pages + 1):
                print(f"\n📖 正在抓取第 {page}/{max_pages} 页...")
                
                try:
                    # 构建API URL
                    params = {
                        'gameNo': '85',
                        'provinceId': '0',
                        'pageSize': '30',
                        'isVerify': '1',
                        'pageNo': str(page)
                    }
                    
                    # 构建完整URL
                    url_params = '&'.join([f"{k}={v}" for k, v in params.items()])
                    full_url = f"{self.base_url}?{url_params}"
                    
                    print(f"🌐 访问URL: {full_url}")
                    
                    # 使用浏览器访问API
                    self.tab.get(full_url, retry=3, interval=2, timeout=30)
                    
                    # 等待页面加载
                    self.tab.wait.load_start()
                    time.sleep(random.uniform(2, 4))
                    
                    # 获取页面内容
                    page_content = self.tab.html
                    
                    # 尝试从页面中提取JSON数据
                    json_data = None
                    
                    # 方法1: 查找<pre>标签中的JSON
                    pre_element = self.tab.ele('tag:pre')
                    if pre_element:
                        json_text = pre_element.text
                        try:
                            json_data = json.loads(json_text)
                        except:
                            pass
                    
                    # 方法2: 直接从页面源码中提取JSON
                    if not json_data:
                        # 查找JSON格式的数据
                        json_pattern = r'\{.*"isSuccess".*\}'
                        matches = re.findall(json_pattern, page_content, re.DOTALL)
                        if matches:
                            try:
                                json_data = json.loads(matches[0])
                            except:
                                pass
                    
                    # 方法3: 执行JavaScript获取数据
                    if not json_data:
                        try:
                            # 执行JavaScript来获取响应数据
                            js_code = """
                            return fetch(arguments[0])
                                .then(response => response.json())
                                .then(data => data)
                                .catch(error => null);
                            """
                            json_data = self.tab.run_js(js_code, full_url)
                        except:
                            pass
                    
                    if not json_data:
                        print(f"❌ 第{page}页无法获取JSON数据")
                        failed_pages.append(page)
                        continue
                    
                    # 检查API响应
                    if not json_data.get('isSuccess', False):
                        error_msg = json_data.get('errorMessage', '未知错误')
                        if error_msg == '处理成功':
                            print("✅ API返回'处理成功'，继续处理")
                        else:
                            print(f"❌ 第{page}页API错误: {error_msg}")
                            failed_pages.append(page)
                            continue
                    
                    # 处理数据
                    value = json_data.get('value', {})
                    page_data = value.get('list', [])
                    
                    if not page_data:
                        print(f"⚠️  第{page}页无数据")
                        failed_pages.append(page)
                        continue
                    
                    # 解析并存储数据
                    parsed_count = 0
                    for item in page_data:
                        try:
                            # 解析期号
                            period = item.get('lotteryDrawNum', '')
                            
                            # 解析开奖时间
                            draw_time = item.get('lotteryDrawTime', '')
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', draw_time)
                            if not date_match:
                                continue
                            draw_date = date_match.group(1)
                            
                            # 解析开奖号码
                            draw_result = item.get('lotteryDrawResult', '')
                            if not draw_result:
                                continue
                            
                            numbers = draw_result.split(' ')
                            if len(numbers) < 7:
                                continue
                            
                            front_balls = [int(x) for x in numbers[:5]]
                            back_balls = [int(x) for x in numbers[5:7]]
                            
                            # 解析奖级信息
                            prize_list = item.get('prizeLevelList', [])
                            first_prize_count = 0
                            first_prize_amount = 0
                            second_prize_count = 0
                            second_prize_amount = 0
                            
                            for prize in prize_list:
                                if prize.get('awardLevel') == '一等奖':
                                    first_prize_count = prize.get('awardLevelNum', 0)
                                    first_prize_amount = prize.get('awardMoney', 0)
                                elif prize.get('awardLevel') == '二等奖':
                                    second_prize_count = prize.get('awardLevelNum', 0)
                                    second_prize_amount = prize.get('awardMoney', 0)
                            
                            # 解析其他信息
                            sales_amount = item.get('drawMoney', 0)
                            pool_amount = item.get('poolBalanceAfterdraw', 0)
                            
                            # 存储数据
                            lottery_record = {
                                'period': period,
                                'date': draw_date,
                                'front_balls': front_balls,
                                'back_balls': back_balls,
                                'first_prize_count': first_prize_count,
                                'first_prize_amount': first_prize_amount,
                                'second_prize_count': second_prize_count,
                                'second_prize_amount': second_prize_amount,
                                'sales_amount': sales_amount,
                                'pool_amount': pool_amount
                            }
                            
                            all_data.append(lottery_record)
                            parsed_count += 1
                            
                        except Exception as e:
                            print(f"⚠️  解析记录时出错: {e}")
                            continue
                    
                    print(f"✅ 第{page}页成功，解析 {parsed_count} 条有效记录")
                    
                    # 页面间延时
                    time.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    print(f"❌ 第{page}页出错: {e}")
                    failed_pages.append(page)
                    continue
            
            print(f"\n📊 DrissionPage数据抓取完成:")
            print(f"✅ 成功获取 {len(all_data)} 条记录")
            if failed_pages:
                print(f"❌ 失败页面: {failed_pages[:10]}{'...' if len(failed_pages) > 10 else ''} (共{len(failed_pages)}页)")
            
            self.lottery_data = all_data
            return len(all_data) > 0
            
        except Exception as e:
            print(f"❌ DrissionPage抓取过程出错: {e}")
            return False
        finally:
            self._close_drissionpage()
    
    def get_max_pages_with_drissionpage(self):
        """使用DrissionPage获取总页数"""
        print("正在使用DrissionPage获取总页数...")
        
        try:
            params = {
                'gameNo': '85',
                'provinceId': '0',
                'pageSize': '30',
                'isVerify': '1',
                'pageNo': '1'
            }
            
            url_params = '&'.join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{self.base_url}?{url_params}"
            
            print(f"🌐 访问URL: {full_url}")
            
            # 使用浏览器访问API
            self.tab.get(full_url, retry=3, interval=2, timeout=30)
            self.tab.wait.load_start()
            time.sleep(3)
            
            # 获取JSON数据
            json_data = None
            
            # 尝试多种方法获取数据
            pre_element = self.tab.ele('tag:pre')
            if pre_element:
                json_text = pre_element.text
                try:
                    json_data = json.loads(json_text)
                except:
                    pass
            
            if not json_data:
                page_content = self.tab.html
                json_pattern = r'\{.*"isSuccess".*\}'
                matches = re.findall(json_pattern, page_content, re.DOTALL)
                if matches:
                    try:
                        json_data = json.loads(matches[0])
                    except:
                        pass
            
            if json_data:
                value = json_data.get('value', {})
                total_pages = value.get('pages', 100)
                total_records = value.get('total', 0)
                
                print(f"✅ 成功获取页数信息: 总记录 {total_records} 条，共 {total_pages} 页")
                return total_pages
            else:
                print("⚠️  无法获取页数信息，使用默认值")
                return 100
                
        except Exception as e:
            print(f"❌ 获取总页数时出错: {e}")
            return 100

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
    
    # 生成聚合数据文件
    analyzer.generate_aggregated_data_hjson()
    
    # 更新README中的大乐透推荐号码
    analyzer.update_readme_recommendations()
    
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