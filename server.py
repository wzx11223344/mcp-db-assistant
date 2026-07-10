#!/usr/bin/env python
"""MCP数据库助手服务器入口

启动后自动创建示例数据库（含employees/departments/salaries表）并连接，
然后运行MCP服务器，为AI客户端提供数据库操作工具。

使用方法:
    python server.py

或通过MCP客户端配置:
    {
        "mcpServers": {
            "db-assistant": {
                "command": "python",
                "args": ["server.py"],
                "cwd": "<项目目录路径>"
            }
        }
    }
"""

import os
import sqlite3

# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DB_PATH = os.path.join(PROJECT_DIR, "sample.db")


def create_sample_database():
    """创建示例数据库。

    包含三个表：
    - departments: 部门表（5个部门）
    - employees: 员工表（20名员工）
    - salaries: 工资表（20条工资记录）

    表之间有外键关联：
    - employees.department_id -> departments.id
    - salaries.employee_id -> employees.id
    - departments.manager_id -> employees.id
    """
    # 如果已存在则删除重建
    if os.path.exists(SAMPLE_DB_PATH):
        os.remove(SAMPLE_DB_PATH)

    conn = sqlite3.connect(SAMPLE_DB_PATH)
    cursor = conn.cursor()

    # 开启外键支持
    cursor.execute("PRAGMA foreign_keys = ON")

    # ========== 创建表 ==========

    # 部门表
    cursor.execute("""
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            manager_id INTEGER,
            location TEXT,
            budget REAL,
            FOREIGN KEY (manager_id) REFERENCES employees(id)
        )
    """)

    # 员工表
    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department_id INTEGER,
            position TEXT,
            hire_date TEXT,
            email TEXT UNIQUE,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    """)

    # 工资表
    cursor.execute("""
        CREATE TABLE salaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            effective_date TEXT NOT NULL,
            end_date TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    """)

    # ========== 插入数据 ==========

    # 部门数据
    departments = [
        (1, "工程部", None, "北京", 5000000),
        (2, "销售部", None, "上海", 3000000),
        (3, "市场部", None, "广州", 2000000),
        (4, "人事部", None, "北京", 1000000),
        (5, "财务部", None, "上海", 1500000),
    ]
    cursor.executemany(
        "INSERT INTO departments (id, name, manager_id, location, budget) "
        "VALUES (?, ?, ?, ?, ?)",
        departments,
    )

    # 员工数据
    employees = [
        (1, "张伟", 1, "技术总监", "2018-03-15", "zhangwei@example.com", 1),
        (2, "王芳", 1, "高级工程师", "2019-07-01", "wangfang@example.com", 1),
        (3, "李强", 1, "初级工程师", "2021-01-10", "liqiang@example.com", 1),
        (4, "刘洋", 2, "销售经理", "2018-06-20", "liuyang@example.com", 1),
        (5, "陈静", 2, "销售代表", "2020-09-15", "chenjing@example.com", 1),
        (6, "赵磊", 3, "市场专员", "2021-03-01", "zhaolei@example.com", 1),
        (7, "孙丽", 4, "HR经理", "2017-11-10", "sunli@example.com", 1),
        (8, "周强", 5, "会计", "2019-04-05", "zhouqiang@example.com", 1),
        (9, "吴敏", 1, "测试工程师", "2020-02-20", "wumin@example.com", 1),
        (10, "郑浩", 2, "销售代表", "2022-01-15", "zhenghao@example.com", 1),
        (11, "冯雪", 3, "品牌经理", "2018-08-30", "fengxue@example.com", 1),
        (12, "蒋涛", 5, "财务分析师", "2021-06-01", "jiangtao@example.com", 0),
        (13, "韩梅", 4, "招聘专员", "2022-03-10", "hanmei@example.com", 1),
        (14, "杨光", 1, "架构师", "2016-05-15", "yangguang@example.com", 1),
        (15, "朱琳", 2, "客户经理", "2020-11-20", "zhulin@example.com", 1),
        (16, "秦宇", 3, "内容运营", "2021-09-05", "qinyu@example.com", 1),
        (17, "许文", 5, "出纳", "2019-10-15", "xuwen@example.com", 1),
        (18, "何丽", 4, "行政助理", "2022-07-01", "heli@example.com", 1),
        (19, "罗刚", 1, "DevOps工程师", "2020-04-10", "luogang@example.com", 1),
        (20, "梁芳", 2, "区域销售", "2021-12-01", "liangfang@example.com", 0),
    ]
    cursor.executemany(
        "INSERT INTO employees (id, name, department_id, position, hire_date, email, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        employees,
    )

    # 更新部门manager_id
    cursor.execute("UPDATE departments SET manager_id = 1 WHERE id = 1")
    cursor.execute("UPDATE departments SET manager_id = 4 WHERE id = 2")
    cursor.execute("UPDATE departments SET manager_id = 11 WHERE id = 3")
    cursor.execute("UPDATE departments SET manager_id = 7 WHERE id = 4")
    cursor.execute("UPDATE departments SET manager_id = 8 WHERE id = 5")

    # 工资数据
    salaries = [
        (1, 1, 35000, "2023-01-01", None),
        (2, 2, 25000, "2023-01-01", None),
        (3, 3, 18000, "2023-01-01", None),
        (4, 4, 30000, "2023-01-01", None),
        (5, 5, 15000, "2023-01-01", None),
        (6, 6, 12000, "2023-01-01", None),
        (7, 7, 28000, "2023-01-01", None),
        (8, 8, 20000, "2023-01-01", None),
        (9, 9, 20000, "2023-01-01", None),
        (10, 10, 14000, "2023-01-01", None),
        (11, 11, 26000, "2023-01-01", None),
        (12, 12, 22000, "2023-01-01", "2023-06-30"),
        (13, 13, 13000, "2023-01-01", None),
        (14, 14, 40000, "2023-01-01", None),
        (15, 15, 16000, "2023-01-01", None),
        (16, 16, 11000, "2023-01-01", None),
        (17, 17, 18000, "2023-01-01", None),
        (18, 18, 10000, "2023-01-01", None),
        (19, 19, 24000, "2023-01-01", None),
        (20, 20, 15500, "2023-01-01", "2023-09-30"),
    ]
    cursor.executemany(
        "INSERT INTO salaries (id, employee_id, amount, effective_date, end_date) "
        "VALUES (?, ?, ?, ?, ?)",
        salaries,
    )

    # ========== 创建索引 ==========
    cursor.execute("CREATE INDEX idx_employees_dept ON employees(department_id)")
    cursor.execute("CREATE INDEX idx_salaries_emp ON salaries(employee_id)")
    cursor.execute("CREATE INDEX idx_employees_email ON employees(email)")

    conn.commit()
    conn.close()
    print(f"[INFO] 示例数据库已创建: {SAMPLE_DB_PATH}")


def main():
    """启动MCP数据库助手服务器。

    1. 创建示例数据库
    2. 自动连接到示例数据库
    3. 运行MCP服务器，等待AI客户端连接
    """
    # 创建示例数据库
    create_sample_database()

    # 导入MCP服务器实例和连接管理器
    from mcp_db_assistant import mcp
    from mcp_db_assistant.connection import db_manager

    # 自动连接到示例数据库
    conn = sqlite3.connect(SAMPLE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    db_manager.connection = conn
    db_manager.db_path = SAMPLE_DB_PATH
    db_manager.db_type = "sqlite"

    print(f"[INFO] 已自动连接到示例数据库: {SAMPLE_DB_PATH}")
    print("[INFO] 启动MCP数据库助手服务器...")
    print("[INFO] 可用工具 (26个):")
    print("  连接管理: connect_sqlite, connect_postgres, list_databases, get_connection_status")
    print("  查询工具: execute_query, execute_update, query_with_pagination, "
          "export_query_result, explain_query, count_rows")
    print("  Schema:  list_tables, describe_table, list_indexes, "
          "get_table_ddl, get_foreign_keys")
    print("  分析:    table_stats, column_stats, data_quality_report, "
          "table_sample, null_analysis, value_distribution")
    print("  SQL构建: build_select, build_insert, build_update, "
          "build_create_table, build_join")
    print()

    # 运行MCP服务器
    mcp.run()


if __name__ == "__main__":
    main()
