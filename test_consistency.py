#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试推荐算法一致性
"""

from lottery_analyzer import DoubleColorBallAnalyzer

def test_consistency():
    """测试推荐算法的一致性"""
    print("🔍 测试推荐算法一致性...")
    
    # 第一次运行
    print("\n📊 第一次运行：")
    analyzer1 = DoubleColorBallAnalyzer()
    analyzer1.fetch_lottery_data(max_pages=2)  # 测试数据
    recommendations1 = analyzer1.generate_recommendations()
    
    # 第二次运行（使用相同数据）
    print("\n\n📊 第二次运行（使用相同数据）：")
    analyzer2 = DoubleColorBallAnalyzer()
    analyzer2.lottery_data = analyzer1.lottery_data  # 复制相同数据
    recommendations2 = analyzer2.generate_recommendations()
    
    # 验证一致性
    print("\n\n✅ 验证一致性：")
    all_consistent = True
    
    for i in range(len(recommendations1)):
        rec1 = recommendations1[i]
        rec2 = recommendations2[i]
        
        red_same = rec1['red_balls'] == rec2['red_balls']
        blue_same = rec1['blue_ball'] == rec2['blue_ball']
        
        if red_same and blue_same:
            print(f"第{i+1}组推荐: ✅ 完全一致")
        else:
            print(f"第{i+1}组推荐: ❌ 不一致")
            print(f"  第1次: {rec1['red_balls']} + {rec1['blue_ball']}")
            print(f"  第2次: {rec2['red_balls']} + {rec2['blue_ball']}")
            all_consistent = False
    
    if all_consistent:
        print("\n🎉 所有推荐组合完全一致！算法已修复。")
    else:
        print("\n❌ 发现不一致的推荐，需要进一步检查。")
    
    # 显示推荐详情
    print("\n📋 推荐详情（基于统计频率）：")
    for i, rec in enumerate(recommendations1, 1):
        red_str = " ".join([f"{x:02d}" for x in rec['red_balls']])
        print(f"推荐 {i}: {red_str} + {rec['blue_ball']:02d}")
        print(f"        {rec['description']}")
        print(f"        红球总频次: {rec['red_freq_sum']}, 蓝球频次: {rec['blue_freq']}")
    
    return all_consistent

if __name__ == "__main__":
    test_consistency() 