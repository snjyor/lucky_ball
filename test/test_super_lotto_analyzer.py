#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大乐透分析器测试脚本
"""

from scripts.super_lotto_analyzer import SuperLottoAnalyzer

def test_analyzer():
    """测试大乐透分析器功能"""
    print("🧪 开始测试大乐透分析器...")
    
    analyzer = SuperLottoAnalyzer()
    
    # 测试获取最大页数
    print("\n1. 测试获取最大页数...")
    max_pages = analyzer.get_max_pages()
    print(f"✅ 获取到最大页数: {max_pages}")
    
    # 测试数据抓取（只抓取前2页进行测试）
    print("\n2. 测试数据抓取（前2页）...")
    test_pages = min(2, max_pages)
    analyzer.fetch_lottery_data(max_pages=test_pages)
    
    if not analyzer.lottery_data:
        print("❌ 数据抓取失败")
        return False
    
    print(f"✅ 成功抓取 {len(analyzer.lottery_data)} 期数据")
    
    # 显示前3期数据样例
    print("\n3. 数据样例（前3期）:")
    for i, record in enumerate(analyzer.lottery_data[:3]):
        front_str = " ".join([f"{x:02d}" for x in record['front_balls']])
        back_str = " ".join([f"{x:02d}" for x in record['back_balls']])
        print(f"   {record['period']}期 ({record['date']}): {front_str} | {back_str}")
    
    # 测试频率分析
    print("\n4. 测试频率分析...")
    front_counter, back_counter = analyzer.analyze_frequency()
    print("✅ 频率分析完成")
    
    # 测试规律分析
    print("\n5. 测试规律分析...")
    analyzer.analyze_patterns()
    print("✅ 规律分析完成")
    
    # 测试走势分析
    print("\n6. 测试走势分析...")
    analyzer.analyze_trends()
    print("✅ 走势分析完成")
    
    # 测试推荐生成
    print("\n7. 测试推荐生成...")
    recommendations = analyzer.generate_recommendations(num_sets=3)
    print("✅ 推荐生成完成")
    
    # 测试数据保存
    print("\n8. 测试数据保存...")
    analyzer.save_data("test_super_lotto_data.json")
    print("✅ 数据保存完成")
    
    # 测试报告生成
    print("\n9. 测试报告生成...")
    analyzer.generate_analysis_report("test_super_lotto_report.md")
    print("✅ 报告生成完成")
    
    print("\n🎉 所有测试通过！大乐透分析器工作正常。")
    return True

if __name__ == "__main__":
    try:
        test_analyzer()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 