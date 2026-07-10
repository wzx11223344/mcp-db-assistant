"""SQL构建工具

提供SELECT、INSERT、UPDATE、CREATE TABLE、JOIN等SQL语句的构建MCP工具。
返回SQL语句字符串和参数列表，方便AI客户端理解和使用。
"""

import json

from mcp_db_assistant import mcp
from mcp_db_assistant import format_markdown_table


@mcp.tool()
def build_select(
    table: str,
    columns: str = "*",
    where: str = "",
    order_by: str = "",
    limit: int = 0,
) -> str:
    """构建SELECT查询语句。

    根据参数生成完整的SELECT语句，支持列选择、条件过滤、排序和限制。

    Args:
        table: 表名，如 'employees'
        columns: 要查询的列，多个列用逗号分隔，默认 '*' 查询所有列
        where: WHERE条件（不含WHERE关键字），如 'department_id = 1 AND is_active = 1'
        order_by: 排序条件（不含ORDER BY关键字），如 'hire_date DESC'
        limit: 限制返回行数，0表示不限制

    Returns:
        构建的SELECT语句（SQL代码块格式）
    """
    # 构建SQL
    sql = f"SELECT {columns} FROM {table}"

    if where:
        sql += f" WHERE {where}"

    if order_by:
        sql += f" ORDER BY {order_by}"

    if limit > 0:
        sql += f" LIMIT {limit}"

    result = "## 构建的SELECT语句\n\n"
    result += f"```sql\n{sql}\n```\n\n"
    result += "### 参数说明\n\n"
    result += format_markdown_table(
        ["参数", "值"],
        [
            ["表名", table],
            ["列", columns],
            ["WHERE条件", where or "(无)"],
            ["排序", order_by or "(无)"],
            ["行数限制", str(limit) if limit > 0 else "无限制"],
        ],
    )
    return result


@mcp.tool()
def build_insert(table: str, data: str) -> str:
    """构建INSERT语句。

    根据提供的列值数据生成参数化的INSERT语句。

    Args:
        table: 表名，如 'employees'
        data: JSON格式的列值数据，如 '{"name": "张三", "department_id": 1, "position": "工程师"}'

    Returns:
        构建的INSERT语句和参数（SQL代码块格式）
    """
    try:
        # 解析JSON数据
        data_dict = json.loads(data) if isinstance(data, str) else data

        if not data_dict:
            return "❌ 数据不能为空。"

        columns = list(data_dict.keys())
        values = [data_dict[col] for col in columns]

        # 构建参数化SQL
        placeholders = ", ".join(["?"] * len(columns))
        col_str = ", ".join(columns)
        sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})"

        result = "## 构建的INSERT语句\n\n"
        result += f"```sql\n{sql}\n```\n\n"
        result += "### 参数\n\n"

        param_data = []
        for i, (col, val) in enumerate(zip(columns, values), 1):
            param_data.append([i, col, repr(val)])
        result += format_markdown_table(["序号", "列名", "参数值"], param_data)

        result += "\n\n### 使用示例\n\n"
        result += f"```python\nimport sqlite3\nconn = sqlite3.connect('your_db.db')\n"
        result += f"cursor = conn.cursor()\ncursor.execute(sql, {values!r})\nconn.commit()\n```"

        return result
    except json.JSONDecodeError as e:
        return f"❌ JSON解析失败: {str(e)}\n\n请确保data参数是有效的JSON字符串。"
    except Exception as e:
        return f"❌ 构建INSERT语句失败: {str(e)}"


@mcp.tool()
def build_update(table: str, set_values: str, where: str = "") -> str:
    """构建UPDATE语句。

    根据提供的列值和条件生成参数化的UPDATE语句。

    Args:
        table: 表名，如 'employees'
        set_values: JSON格式的SET值，如 '{"position": "高级工程师", "is_active": 1}'
        where: WHERE条件（不含WHERE关键字），如 'id = 1'。为空时不加WHERE（危险！）

    Returns:
        构建的UPDATE语句和参数（SQL代码块格式）
    """
    try:
        # 解析JSON数据
        set_dict = json.loads(set_values) if isinstance(set_values, str) else set_values

        if not set_dict:
            return "❌ SET值不能为空。"

        set_columns = list(set_dict.keys())
        set_vals = [set_dict[col] for col in set_columns]

        # 构建SET子句
        set_clause = ", ".join([f"{col} = ?" for col in set_columns])
        sql = f"UPDATE {table} SET {set_clause}"

        if where:
            sql += f" WHERE {where}"

        result = "## 构建的UPDATE语句\n\n"
        result += f"```sql\n{sql}\n```\n\n"

        if not where:
            result += "⚠️ **警告: 没有WHERE条件，将更新表中所有行！**\n\n"

        result += "### SET参数\n\n"
        param_data = []
        for i, (col, val) in enumerate(zip(set_columns, set_vals), 1):
            param_data.append([i, col, repr(val)])
        result += format_markdown_table(["序号", "列名", "新值"], param_data)

        result += "\n\n### 使用示例\n\n"
        result += f"```python\nimport sqlite3\nconn = sqlite3.connect('your_db.db')\n"
        result += f"cursor = conn.cursor()\ncursor.execute(sql, {set_vals!r})\nconn.commit()\n```"

        return result
    except json.JSONDecodeError as e:
        return f"❌ JSON解析失败: {str(e)}\n\n请确保set_values参数是有效的JSON字符串。"
    except Exception as e:
        return f"❌ 构建UPDATE语句失败: {str(e)}"


@mcp.tool()
def build_create_table(table_name: str, columns: str) -> str:
    """构建CREATE TABLE语句。

    根据列定义生成建表语句。

    Args:
        table_name: 表名，如 'products'
        columns: JSON格式的列定义列表，每个元素是一个列定义字符串，
                 如 '["id INTEGER PRIMARY KEY AUTOINCREMENT", "name TEXT NOT NULL", "price REAL DEFAULT 0"]'

    Returns:
        构建的CREATE TABLE语句（SQL代码块格式）
    """
    try:
        # 解析JSON数据
        col_list = json.loads(columns) if isinstance(columns, str) else columns

        if not col_list:
            return "❌ 列定义不能为空。"

        # 构建列定义
        col_defs = ",\n    ".join(col_list)
        sql = f"CREATE TABLE {table_name} (\n    {col_defs}\n)"

        result = "## 构建的CREATE TABLE语句\n\n"
        result += f"```sql\n{sql}\n```\n\n"
        result += "### 列定义\n\n"

        col_data = []
        for i, col_def in enumerate(col_list, 1):
            col_data.append([i, col_def])
        result += format_markdown_table(["序号", "列定义"], col_data)

        result += "\n\n### 使用示例\n\n"
        result += f"```python\nimport sqlite3\nconn = sqlite3.connect('your_db.db')\n"
        result += f"cursor = conn.cursor()\ncursor.execute('''{sql}''')\nconn.commit()\n```"

        return result
    except json.JSONDecodeError as e:
        return f"❌ JSON解析失败: {str(e)}\n\n请确保columns参数是有效的JSON字符串列表。"
    except Exception as e:
        return f"❌ 构建CREATE TABLE语句失败: {str(e)}"


@mcp.tool()
def build_join(
    table1: str,
    table2: str,
    on: str,
    select_columns: str = "*",
    join_type: str = "INNER",
) -> str:
    """构建JOIN查询语句。

    生成两个表的JOIN查询，支持INNER、LEFT、RIGHT、FULL等连接类型。

    Args:
        table1: 第一个表名，如 'employees'
        table2: 第二个表名，如 'departments'
        on: JOIN条件（不含ON关键字），如 'employees.department_id = departments.id'
        select_columns: 要查询的列，默认 '*' 查询所有列
        join_type: 连接类型，可选 'INNER'、'LEFT'、'RIGHT'、'FULL'（默认 'INNER'）

    Returns:
        构建的JOIN查询语句（SQL代码块格式）
    """
    # 验证连接类型
    join_type = join_type.upper().strip()
    valid_types = ["INNER", "LEFT", "RIGHT", "FULL", "CROSS"]
    if join_type not in valid_types:
        return (
            f"❌ 不支持的连接类型: {join_type}\n"
            f"请使用以下之一: {', '.join(valid_types)}"
        )

    # 构建SQL
    if join_type == "CROSS":
        sql = f"SELECT {select_columns} FROM {table1} CROSS JOIN {table2}"
    else:
        sql = (
            f"SELECT {select_columns} FROM {table1}\n"
            f"{join_type} JOIN {table2} ON {on}"
        )

    result = "## 构建的JOIN查询语句\n\n"
    result += f"```sql\n{sql}\n```\n\n"
    result += "### 参数说明\n\n"
    result += format_markdown_table(
        ["参数", "值"],
        [
            ["表1", table1],
            ["表2", table2],
            ["连接类型", join_type + " JOIN"],
            ["ON条件", on],
            ["查询列", select_columns],
        ],
    )

    if join_type == "LEFT":
        result += "\n\n💡 **LEFT JOIN** 会返回左表(table1)的所有行，即使在右表(table2)中没有匹配。"
    elif join_type == "RIGHT":
        result += "\n\n💡 **RIGHT JOIN** 会返回右表(table2)的所有行，即使在左表(table1)中没有匹配。"
    elif join_type == "INNER":
        result += "\n\n💡 **INNER JOIN** 只返回两表中都有匹配的行。"
    elif join_type == "FULL":
        result += "\n\n💡 **FULL JOIN** 返回两表的所有行（SQLite不支持，需要UNION模拟）。"
    elif join_type == "CROSS":
        result += "\n\n💡 **CROSS JOIN** 返回两表的笛卡尔积。"

    return result
