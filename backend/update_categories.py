#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量更新现有数据的分类
根据新的分类逻辑重新分类所有记录
"""

import sqlite3
import asyncio
from ai_service import AIService

def get_new_category(content):
    """根据新的分类逻辑获取分类"""
    content_lower = content.lower()
    
    # 运动相关关键词（优先匹配）
    exercise_keywords = ['运动', '锻炼', '跑步', '健身', '瑜伽', '晨间运动', '锻炼身体', '健身操', '游泳', '骑车', '爬山', '散步', '慢跑', '快走', '举重', '拉伸', '有氧', '无氧', '训练', '练习', '走', '走了', '走了一大圈', '走路', '步行', '徒步', '远足', '骑行', '骑自行车']
    if any(keyword in content for keyword in exercise_keywords):
        return "运动"
    
    # 睡眠相关关键词（优先匹配）
    sleep_keywords = ['睡', '睡觉', '睡眠', '睡足', '睡醒', '午睡', '小憩', '休息', '困', '累', '疲惫', '熬夜', '早睡', '晚睡', '失眠', '做梦', '打盹']
    if any(keyword in content for keyword in sleep_keywords):
        return "睡眠"
    
    # 饮食相关关键词（包括购买食物）
    food_keywords = ['水果', '蔬菜', '面包', '鸡蛋', '牛油果', '樱桃', '桃子', '汤', '土豆', '有机', '吃', '喝', '早餐', '午餐', '晚餐', '零食', '饮料', '咖啡', '茶', '牛奶', '酸奶', '米饭', '面条', '饺子', '包子', '蛋糕', '饼干', '巧克力', '冰淇淋']
    if any(keyword in content_lower for keyword in [kw.lower() for kw in food_keywords]):
        return "饮食"
    
    # 阅读相关关键词（优先匹配）
    reading_keywords = ['读书', '阅读', '听书', '看书', '听', '书', '小说', '文章', '杂志', '报纸', '博客', '电子书', '有声书', '播客', '听播客', '听节目', '听讲座', '听课程', '听音频', '听音乐', '听歌', '《', '》', '书名号']
    if any(keyword in content for keyword in reading_keywords):
        return "阅读"
    
    # 学习相关关键词（优先于工作匹配）
    study_keywords = ['学习', '课程', '技能', '教育', '知识', '研究', '练习', '复习', '预习', '考试', '作业', '论文', '报告', '笔记', '开智', '开智学堂', '卡片', '知识卡片', '学习卡片', '记忆卡片', '复习卡片', '粤语', '德语', '英语', '法语', '日语', '韩语', '西班牙语', '意大利语', '俄语', '语言', '学语言', '学外语', '演讲', '访谈', '分享', '功能', '讲座', '培训', '工作坊', '研讨会', '交流会', '分享会', '学习会', '读书会', '上课', '开课', '结业', '学员', '成长的心智', '第几课', 'ch04', 'ch', '章节', '课', '课程', '学习课程', '学习班', '培训班', '训练班', '学习小组', '学习群', '学习社区', '测试', '测验', '考试', '考核', '评估', '测评', '练习', '训练', '实验', '实践', '实习', '见习']
    if any(keyword in content for keyword in study_keywords):
        return "学习"
    
    # 工作相关关键词
    work_keywords = ['工作', '项目', '会议', '职场', '编程', '代码', '开发', '设计', '任务', 'zotero', '科研', '研究', 'gemini', 'ai', '人工智能', '机器学习', '深度学习', '算法', '模型', '数据', '分析', '统计', '实验', '论文', '发表', '期刊', '会议', '学术']
    if any(keyword in content_lower for keyword in [kw.lower() for kw in work_keywords]):
        return "工作"
    
    # 购物相关关键词（排除食物相关，优先级较低）
    shopping_keywords = ['买', '购物', '超市', 'walmart', 'target', '商店', '商场', '网购', '下单', '付款', '结账']
    if any(keyword in content_lower for keyword in [kw.lower() for kw in shopping_keywords]):
        return "生活"
    
    # 日常生活相关关键词
    daily_life_keywords = ['头发', '头皮', '洗澡', '洗碗', '天气', '下雨', '晴天', '阴天', '多云', '刮风', '下雪', '住房', '客厅', '卧室', '厨房', '卫生间', '阳台', '院子', '花园', '清洁', '打扫', '整理', '收拾', '洗衣', '晾衣', '做饭', '烹饪', '家务', '日常', '生活用品', '日用品', '洗漱', '刷牙', '洗脸', '护肤', '保养', '头部精华', '洗完后涂抹', '涂抹', '精华', '面霜', '乳液', '维修', '修理', '装修', '布置', '装饰']
    if any(keyword in content for keyword in daily_life_keywords):
        return "生活"
    
    # 娱乐相关关键词
    entertainment_keywords = ['游戏', '电影', '音乐', '娱乐', '休闲', '放松', '看剧', '听歌', '玩游戏']
    if any(keyword in content for keyword in entertainment_keywords):
        return "娱乐"
    
    # 家庭相关关键词
    family_keywords = ['家人', '家庭', '父母', '孩子', '配偶', '家庭活动', '家庭关系']
    if any(keyword in content for keyword in family_keywords):
        return "家庭"
    
    # 朋友相关关键词
    friend_keywords = ['朋友', '聚会', '社交', '聊天', '见面', '聚餐']
    if any(keyword in content for keyword in friend_keywords):
        return "朋友"
    
    
    # 默认分类
    return "其他"

async def update_categories():
    """批量更新分类"""
    # 连接数据库
    db_path = "../data/awesome.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有记录
    cursor.execute("SELECT id, content, category FROM entries ORDER BY id")
    entries = cursor.fetchall()
    
    print(f"找到 {len(entries)} 条记录需要更新")
    
    # 统计更新情况
    update_count = 0
    category_stats = {}
    other_entries = []  # 存储被分类为"其他"的记录
    updates = []  # 存储所有更新记录
    
    for entry_id, content, old_category in entries:
        new_category = get_new_category(content)
        
        # 更新分类
        cursor.execute("UPDATE entries SET category = ? WHERE id = ?", (new_category, entry_id))
        
        # 收集更新记录
        updates.append((entry_id, content, old_category, new_category))
        
        # 统计
        if old_category != new_category:
            update_count += 1
            print(f"ID {entry_id}: '{content[:30]}...' {old_category} → {new_category}")
        
        # 统计新分类
        category_stats[new_category] = category_stats.get(new_category, 0) + 1
        
        # 收集被分类为"其他"的记录
        if new_category == "其他":
            other_entries.append((entry_id, content))
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print(f"\n更新完成！")
    print(f"共更新了 {update_count} 条记录")
    print(f"\n新分类统计：")
    for category, count in sorted(category_stats.items()):
        print(f"  {category}: {count} 条")
    
    # 显示被分类为"成长"的记录
    growth_entries = []
    for entry_id, content, old_category, new_category in updates:
        if new_category == "成长":
            growth_entries.append((entry_id, content))
    
    if growth_entries:
        print(f"\n被分类为「成长」的记录（共 {len(growth_entries)} 条）：")
        print("=" * 60)
        for entry_id, content in growth_entries:
            print(f"ID {entry_id}: {content}")
        print("=" * 60)
        print("请查看这些记录，看是否有更好的分类方式。")
    
    # 显示被分类为"其他"的记录
    if other_entries:
        print(f"\n被分类为「其他」的记录（共 {len(other_entries)} 条）：")
        print("=" * 60)
        for entry_id, content in other_entries:
            print(f"ID {entry_id}: {content}")
        print("=" * 60)
        print("请查看这些记录，看是否有更好的分类方式。")

if __name__ == "__main__":
    asyncio.run(update_categories())
