#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双色球分析器测试脚本
"""

import sys
import json
from lottery_analyzer import DoubleColorBallAnalyzer

def test_analyzer():
    """测试分析器基本功能"""
    print("🧪 开始测试双色球分析器...")
    
    analyzer = DoubleColorBallAnalyzer()
    
    # 测试获取最大页码
    print("\n1. 测试获取最大页码...")
    try:
        max_pages = analyzer.get_max_pages()
        print(f"✅ 获取最大页码成功: {max_pages}")
    except Exception as e:
        print(f"❌ 获取最大页码失败: {e}")
        return False
    
    # 测试抓取少量数据
    print("\n2. 测试数据抓取功能...")
    try:
        analyzer.fetch_lottery_data(max_pages=2)  # 只抓取2页测试
        if analyzer.lottery_data:
            print(f"✅ 数据抓取成功: 获取到 {len(analyzer.lottery_data)} 条记录")
            
            # 显示第一条记录作为示例
            first_record = analyzer.lottery_data[0]
            print(f"📊 最新一期: {first_record['period']}")
            print(f"🔴 红球: {first_record['red_balls']}")
            print(f"🔵 蓝球: {first_record['blue_ball']}")
        else:
            print("❌ 数据抓取失败: 无数据")
            return False
    except Exception as e:
        print(f"❌ 数据抓取失败: {e}")
        return False
    
    # 测试数据保存
    print("\n3. 测试数据保存...")
    try:
        analyzer.save_data("test_lottery_data.json")
        print("✅ 数据保存成功")
    except Exception as e:
        print(f"❌ 数据保存失败: {e}")
        return False
    
    # 测试分析功能
    print("\n4. 测试分析功能...")
    try:
        print("📈 频率分析:")
        red_counter, blue_counter = analyzer.analyze_frequency()
        
        print("\n📊 规律分析:")
        analyzer.analyze_patterns()
        
        print("\n📉 趋势分析:")
        analyzer.analyze_trends()
        
        print("\n🎯 推荐号码:")
        recommendations = analyzer.generate_recommendations(num_sets=3)
        
        print("✅ 所有分析功能正常")
    except Exception as e:
        print(f"❌ 分析功能失败: {e}")
        return False
    
    # 测试报告生成
    print("\n5. 测试报告生成...")
    try:
        analyzer.generate_analysis_report("test_analysis_report.md")
        print("✅ 分析报告生成成功")
    except Exception as e:
        print(f"❌ 分析报告生成失败: {e}")
        return False
    
    print("\n🎉 所有测试通过！分析器工作正常。")
    return True

if __name__ == "__main__":
    success = test_analyzer()
    sys.exit(0 if success else 1) 