import zhipuai
from datetime import datetime

class AIService:
    def __init__(self):
        # 使用您之前的 API Key
        self.api_key = "1aea23c7cf09481086501b71630fde25.LcchTbRpjvjLK7qa"
        zhipuai.api_key = self.api_key
        self.client = zhipuai.ZhipuAI(api_key=self.api_key)
    
    async def generate_weekly_summary(self, stats):
        if not stats or stats['total_entries'] == 0:
            return "这个时间段内没有记录任何好棒的时刻，加油！"
        
        # --- Prepare data for the prompt ---

        # 1. Overview Section
        overview_text = f"""- 总条目数：{stats['total_entries']}
- 每日平均条目数：{stats['avg_entries_per_day']}
- 条目最多的一天：{stats['most_active_day']['date']}（{stats['most_active_day']['count']}条）
- 条目最少的一天：{stats['least_active_day']['date']}（{stats['least_active_day']['count']}条）"""

        # 2. Category Statistics Section
        category_summary = ""
        # Sort categories by count, descending
        sorted_categories = sorted(stats['category_counts'].items(), key=lambda item: item[1], reverse=True)
        
        for category, count in sorted_categories:
            category_summary += f"\n### {category}（{count} 条）\n"
            # Get examples for this category
            examples = stats['category_examples'].get(category, [])
            for item in examples:
                category_summary += f"- {item}\n"
            if count > len(examples):
                category_summary += f"- ... 等{count}条\n"
            
            # Add a placeholder for the AI to fill in the analysis
            category_summary += f"\n**特点分析**：请基于以上 {count} 条关于“{category}”的记录，分析其主要特征、模式和个人特质。\n"

        # --- The New Prompt ---
        prompt = f"""
你是一个专业的个人成长数据分析师。你正在为一个名为“今天好棒啊”的应用生成总结报告。
你收到了由后端程序预先计算好的精确统计数据。你的任务是基于这些**事实**，生成一份结构清晰、分析深刻的报告。

**[任务要求]**
1.  **严格使用我提供的数据**：报告中的所有数字、日期和条目示例都必须直接来源于我提供的数据。**严禁自己进行任何计算或假设。**
2.  **保持指定结构**：报告必须严格遵循“1. 总览”、“2. 分类统计”、“3. 深度分析”的结构。
3.  **专注于分析**：你的核心价值在于“特点分析”和“深度分析”部分。要基于具体数据进行客观、有洞察力的分析，避免空话和套话。
4.  **使用“你”而不是“该用户”**。
5.  **严禁使用评价性语言**，如“看来”、“不错”、“很好”等。要用数据说话，例如：“数据显示你连续3天都记录了晨跑，说明运动频率较高”。

---
**[报告生成所需数据]**

**时间范围**：{stats['start_date']} 至 {stats['end_date']}

**1. 总览数据**
{overview_text}

**2. 分类统计数据**
{category_summary}

**3. 深度分析所需原始条目 (仅供参考，不要在报告中逐条罗列)**
{stats['raw_entries'][:20]} ... (只显示部分用于分析)

---
**[请根据以上数据，生成最终报告]**

请严格按照以下 Markdown 格式输出：

## 🗓 「今天好棒啊」总结（{stats['start_date']} 至 {stats['end_date']}）

### 1. 总览
{overview_text}

### 2. 分类统计
{category_summary}

### 3. 深度分析
请基于以上所有数据，撰写一段综合性的深度分析，发现独特的个人模式和行为特点。

"""
        
        try:
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI 总结生成失败：{str(e)}"
    
    async def generate_multi_week_analysis(self, entries):
        """生成多周趋势分析"""
        if not entries:
            return "还没有记录任何好棒的时刻，加油！"
        
        # 准备数据 - 包含content、date、time三列
        entries_text = "\n".join([f"- 内容：{entry[0]} | 日期：{entry[5]} | 时间：{entry[3]}" for entry in entries])
        
        prompt = f"""
你将收到用户若干条"今天好棒啊"记录，每条记录包含：内容、日期、时间信息。

**重要：请严格按照提供的真实数据进行分析，不要生成任何虚构的内容。所有统计数字、代表性条目、时间范围都必须基于实际提供的记录。**

**数据格式说明**：
- 内容：具体的记录内容
- 日期：记录发生的日期
- 时间：记录发生的时间

**请严格按照提供的真实记录进行分析，不要编造任何内容。**

请基于这些数据生成多周趋势分析总结，要求如下：

1. **按周划分**：
   - 自动按周（周一至周日）分组记录。
   - 每周生成一个小节，包括时间范围和周内条目。

2. **每周总结**：
   - 自动提取时间范围（最早到最晚记录日期）
   - 总条目数
   - 平均每日条目数
   - 条目最多的一天 / 条目最少的一天
   - 分类统计（学习/阅读、运动/健康、饮食/生活享受、学习/工作成果、休息/放松、其他）
   - 每类条目数量及代表性条目
   - 模式与规律（时间规律、习惯趋势、兴趣聚焦、生活方式、成果闭环、潜在改进点）
   - 关键词（3–5 个）
   - 总结段落（基于事实、突出"棒"的具体体现）

3. **跨周趋势分析**：
   - 比较各周总条目数变化、平均每日条目数趋势
   - 学习/运动/生活条目占比变化
   - 高峰和低谷活动规律变化
   - 是否出现新习惯或新兴趣方向
   - 休息、生活敏感度或作业/项目完成等闭环趋势变化
   - 综合发现跨周模式和潜在优化点

**输出格式**：

# 多周「今天好棒啊」趋势分析

## 周 1（YYYY-MM-DD 至 YYYY-MM-DD）
### 1. 总览
- 总条目数：
- 平均每日条目数：
- 条目最多的一天：
- 条目最少的一天：

### 2. 分类统计
**学习/阅读（X 条）**
- 代表性条目：
- 特点：

（依次列出其他分类）

### 3. 模式与规律
- …（具体观察的规律、趋势、习惯、兴趣等）

### 4. 关键词
- …（3–5 个）

### 5. 总结
- …（简短段落，突出本周"棒"的具体体现）

## 周 2（YYYY-MM-DD 至 YYYY-MM-DD）
- 同上格式

（依次生成每周总结）

## 跨周趋势
- 总条目数变化：
- 平均每日条目数变化：
- 学习/运动/生活条目占比变化：
- 高峰和低谷活动规律变化：
- 新习惯或新兴趣方向：
- 休息、生活敏感度或作业/项目闭环趋势：
- 综合模式与潜在优化建议：

记录内容：
{entries_text}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI 多周分析生成失败：{str(e)}"
    
    async def auto_categorize(self, content):
        """AI自动分类功能"""
        # 先进行关键词匹配，提高准确性
        content_lower = content.lower()
        
        # 运动相关关键词（优先匹配）
        exercise_keywords = ['运动', '锻炼', '跑步', '健身', '瑜伽', '晨间运动', '锻炼身体', '健身操', '游泳', '骑车', '爬山', '散步', '慢跑', '快走', '举重', '拉伸', '有氧', '无氧', '训练', '走', '走了', '走了一大圈', '走路', '步行', '徒步', '远足', '骑行', '骑自行车']
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
        
        # 如果关键词匹配没有结果，使用AI分类
        prompt = f"""
        请为以下内容自动分类，只返回一个最合适的分类标签，不要其他解释：
        
        内容：{content}
        
        分类规则：
        - 工作：与工作、职业、项目、会议、职场相关
        - 学习：与学习、课程、技能提升、教育、研究相关
        - 阅读：与读书、听书、阅读、听播客、听音频相关
        - 生活：与日常购物、家务、生活用品、日常活动相关（购买食物除外）
        - 饮食：与食物、饮料、餐饮、水果、蔬菜、烹饪相关（包括购买食物）
        - 运动：与运动、锻炼、健身、跑步、游泳等体育活动相关
        - 睡眠：与睡觉、休息、午睡、熬夜等睡眠相关
        - 娱乐：与游戏、电影、音乐、休闲娱乐相关
        - 家庭：与家人、家庭活动、家庭关系相关
        - 朋友：与朋友聚会、社交活动相关
        - 其他：不属于以上分类的内容
        
        请只返回分类名称，如：工作
        """
        
        try:
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            category = response.choices[0].message.content.strip()
            return category
        except Exception as e:
            return "其他"  # 如果AI分类失败，默认为"其他"
    
    async def answer_smart_query(self, question, entries):
        """智能查询功能"""
        # 准备数据 - entries格式: (id, content, category, created_at, completed_at, entry_date)
        entries_text = "\n".join([f"- {entry[1]}" for entry in entries if len(entry) > 1])
        
        prompt = f"""
        你问了一个关于好棒时刻的问题，请基于以下记录给出详细、有用的回答。
        
        你的问题：{question}
        
        好棒时刻记录：
        {entries_text}
        
        请根据记录内容回答你的问题，要求：
        1. 直接回答你的问题
        2. 如果记录中有相关信息，请具体列出
        3. 如果没有相关信息，请诚实说明
        4. 可以统计数量、分析趋势、总结特点等
        5. 用温暖、鼓励的语调
        6. 如果可能，给出一些积极的观察和建议
        7. 注意：这是基于所有历史记录的回答，不是仅限于本周
        8. 请仔细筛选相关记录，不要包含不相关的内容
        
        示例回答格式：
        - 对于"我提到了几次AI编程"：统计总次数，列出所有相关记录
        - 对于"我吃了哪些水果"：列出所有水果种类
        - 对于"我晨间运动了几次"：统计总次数，分析规律
        """
        
        try:
            # 生成详细回答
            detailed_response = self.client.chat.completions.create(
                model="glm-4",
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            detailed_answer = detailed_response.choices[0].message.content
            
            return {
                "answer": detailed_answer
            }
        except Exception as e:
            return {
                "answer": f"AI查询失败：{str(e)}"
            }