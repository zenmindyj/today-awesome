import sqlite3
from datetime import datetime, timedelta
from collections import Counter
import os
import json
from itertools import groupby

class Database:
    def __init__(self, db_path):
        """
        初始化数据库连接。
        :param db_path: SQLite数据库文件的路径。
        """
        self.db_path = db_path
    
    def generate_unique_code(self, entry_date, created_at):
        """
        生成唯一编码
        格式：年四位数-月两位数日两位数 时:分:秒
        例如：2025-0908 11:56:35
        """
        if isinstance(entry_date, str):
            date_obj = datetime.strptime(entry_date, '%Y-%m-%d').date()
        else:
            date_obj = entry_date
        
        if isinstance(created_at, str):
            try:
                time_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                time_obj = datetime.now() # Fallback
        elif created_at:
             time_obj = created_at
        else:
            time_obj = datetime.now() # Fallback

        year = date_obj.year
        month_day = f"{date_obj.month:02d}{date_obj.day:02d}"
        hour = f"{time_obj.hour:02d}"
        minute = f"{time_obj.minute:02d}"
        second = f"{time_obj.second:02d}"
        
        return f"{year}-{month_day} {hour}:{minute}:{second}"
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                entry_date DATE,
                unique_code TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_entry(self, content, category=None, entry_date=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        entry_date_str = entry_date
        if not entry_date_str:
            entry_date_str = datetime.now().date().strftime('%Y-%m-%d')
        
        completed_at = datetime.now()
        
        unique_code = self.generate_unique_code(entry_date_str, completed_at)
        
        cursor.execute(
            "INSERT INTO entries (content, category, completed_at, entry_date, unique_code) VALUES (?, ?, ?, ?, ?)",
            (content, category, completed_at, entry_date_str, unique_code)
        )
        
        conn.commit()
        conn.close()

    def delete_entry(self, entry_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
        finally:
            conn.close()
    
    def get_entries_count(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entries")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_entries_paginated(self, offset, limit):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC LIMIT ? OFFSET ?", (limit, offset))
        entries = cursor.fetchall()
        conn.close()
        return entries
    
    def get_entries(self, limit=None):
        """获取所有条目，按日期和创建时间排序"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        entries = cursor.fetchall()
        conn.close()
        return entries

    def get_entries_by_date_range(self, start_date, end_date):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM entries 
            WHERE entry_date >= ? AND entry_date <= ? 
            ORDER BY entry_date ASC, created_at ASC
        """, (start_date, end_date))
        entries = cursor.fetchall()
        conn.close()
        return entries

    def get_last_n_weeks_ranges(self, n=3):
        today = datetime.now().date()
        week_ranges = []
        for i in range(n):
            current_monday = today - timedelta(days=today.weekday())
            week_start = current_monday - timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            week_ranges.append({
                "name": f"最近第{i+1}周 ({week_start.strftime('%m-%d')} ~ {week_end.strftime('%m-%d')})",
                "start_date": week_start.strftime('%Y-%m-%d'),
                "end_date": week_end.strftime('%Y-%m-%d')
            })
        return week_ranges

    def get_data_containing_months_ranges(self):
        """获取数据库中包含数据的自然月的起始和结束日期 (已修复)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT entry_date FROM entries ORDER BY entry_date ASC")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        dates = [datetime.strptime(row[0], '%Y-%m-%d').date() for row in rows]
        
        month_options = []
        for month_str, group in groupby(dates, key=lambda d: d.strftime('%Y-%m')):
            month_dates = list(group)
            start_date = month_dates[0]
            end_date = month_dates[-1]
            
            month_name = start_date.strftime('%Y年%m月')
            month_options.append({
                "name": f"{month_name} ({start_date.strftime('%m-%d')} ~ {end_date.strftime('%m-%d')})",
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            })
        
        return sorted(month_options, key=lambda x: x['start_date'], reverse=True)

    def get_statistics_by_date_range(self, start_date_str, end_date_str):
        """根据日期范围获取详细统计数据 (已修复计算错误)"""
        entries = self.get_entries_by_date_range(start_date_str, end_date_str)
        
        total_entries = len(entries)
        if total_entries == 0:
            return None

        # 修复：正确计算实际有数据的天数
        daily_counts = Counter(entry[5] for entry in entries)
        actual_days_with_data = len(daily_counts)
        
        # 如果实际有数据的天数为0，避免除零错误
        if actual_days_with_data == 0:
            avg_entries_per_day = 0
        else:
            avg_entries_per_day = round(total_entries / actual_days_with_data, 1)
        
        category_counts = Counter(entry[2] for entry in entries if entry[2])
        
        most_active_day = daily_counts.most_common(1)[0] if daily_counts else ("无", 0)
        least_active_day = daily_counts.most_common()[-1] if daily_counts else ("无", 0)

        # Prepare raw entries with examples for each category
        category_examples = {}
        for category, count in category_counts.items():
            category_examples[category] = [
                entry[1] for entry in entries if entry[2] == category
            ][:3] # Get up to 3 examples per category

        return {
            "total_entries": total_entries,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "num_days": actual_days_with_data,  # 使用实际有数据的天数
            "avg_entries_per_day": avg_entries_per_day,
            "most_active_day": {"date": most_active_day[0], "count": most_active_day[1]},
            "least_active_day": {"date": least_active_day[0], "count": least_active_day[1]},
            "category_counts": dict(category_counts),
            "category_examples": category_examples,
            "raw_entries": entries 
        }

    def seed_database_if_empty(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entries")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("数据库为空，正在加载演示数据...")
            base_dir = os.path.dirname(os.path.abspath(__file__))
            seed_file_path = os.path.join(base_dir, '..', 'data', 'seed_data.json')
            
            if not os.path.exists(seed_file_path):
                print(f"警告：种子数据文件未找到于 {seed_file_path}")
                conn.close()
                return
                
            try:
                with open(seed_file_path, 'r', encoding='utf-8') as f:
                    seed_data = json.load(f)
                
                for entry in seed_data:
                    content = entry.get('content')
                    if content:
                        cursor.execute("""
                            INSERT INTO entries (content, category, entry_date, created_at, completed_at, unique_code)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            content, entry.get('category'), entry.get('entry_date'),
                            entry.get('created_at'), entry.get('completed_at'), entry.get('unique_code')
                        ))
                
                conn.commit()
                print(f"成功加载 {len(seed_data)} 条演示数据到数据库。")
            except Exception as e:
                print(f"加载演示数据时出错: {e}")
            finally:
                conn.close()
        else:
            conn.close()

    def delete_all_entries(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM entries")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM entries")
            conn.commit()
            return count
        except Exception:
            return 0
        finally:
            conn.close()
