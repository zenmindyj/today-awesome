# -*- coding: utf-8 -*-
"""
本脚本用于将 SQLite 数据库中的 "Today Awesome" 记录导出为 JSON 格式，
作为应用的演示（种子）数据。

运行方式：
1. 确保此脚本位于 `today-awesome/backend/` 目录下。
2. 确保 `today-awesome/data/awesome.db` 文件存在且包含数据。
3. 在 `backend` 目录下，激活虚拟环境后，执行 `python export_data.py`。
4. 脚本执行后，将在 `today-awesome/data/` 目录下生成 `seed_data.json` 文件。
"""

import sqlite3
import json
import os

def export_data():
    """
    从 SQLite 数据库导出数据到 JSON 文件。
    """
    # 构建数据库和输出文件的路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, '..', 'data', 'awesome.db')
    output_path = os.path.join(base_dir, '..', 'data', 'seed_data.json')

    if not os.path.exists(db_path):
        print(f"错误：数据库文件未找到于 {db_path}")
        return

    print(f"正在从 {db_path} 读取数据...")

    try:
        # 连接到数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 允许通过列名访问数据
        cursor = conn.cursor()

        # 查询所有记录，按创建时间排序
        cursor.execute("SELECT * FROM entries ORDER BY created_at ASC")
        rows = cursor.fetchall()

        # 将查询结果转换为字典列表
        data_to_export = [dict(row) for row in rows]

        conn.close()

        # 将数据写入 JSON 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_export, f, ensure_ascii=False, indent=4)

        print(f"成功！ {len(data_to_export)} 条记录已成功导出到 {output_path}")

    except Exception as e:
        print(f"导出过程中发生错误：{e}")

if __name__ == "__main__":
    export_data()
