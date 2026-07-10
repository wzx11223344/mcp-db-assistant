"""查询工具

提供SQL查询执行、分页、导出、执行计划分析等MCP工具。
所有工具自动使用当前连接（由 connection.db_manager 管理）。
"""

import json
import csv
import io

from mcp_db_assistant import mcp
from mcp_db_assistant import format_markdown_table
from mcp_db_assistant.connection import db_manager


@mcp.tool()
def execute_query(sql: str) -> str:
    """执行SELECT查询并以Markdown表格返回结果。

    仅允许SELECT语句，自动检测并拒绝非查询SQL。
    结果默认限制1000行以防止过大输出。

    Args:
        sql: SELECT查询语句，如 'SELECT * FROM employees LIMIT 10'

    Returns:
        查询结果（Markdown表格格式），包含列名和所有数据行
    """
    try:
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 安全检查：仅允许SELECT
        stripped = sql.strip().upper()
        if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
            return "❌ execute_query 仅支持 SELECT 语句。如需执行修改操作，请使用 execute_update。"

        cursor.execute(sql)
        rows = cursor.fetchall()
        column_names = (
            [desc[0] for desc in cursor.description] if cursor.description else []
        )

        if not column_names:
            return "查询执行成功，但未返回任何列。"

        # 限制返回行数
        max_rows = 1000
        truncated = len(rows) > max_rows
        display_rows = rows[:max_rows]

        # 转换数据
        data = []
        for row in display_rows:
            data.append([row[i] for i in range(len(column_names))])

        result = format_markdown_table(column_names, data)

        if truncated:
            result += f"\n\n⚠️ 结果已截断，仅显示前 {max_rows} 行（共 {len(rows)} 行）。"

        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 查询执行失败: {str(e)}"


@mcp.tool()
def execute_update(sql: str) -> str:
    """执行INSERT、UPDATE或DELETE语句。

    执行数据修改操作并返回影响的行数。
    自动提交事务。

    Args:
        sql: INSERT/UPDATE/DELETE语句，如 "INSERT INTO employees (name) VALUES ('张三')"

    Returns:
        执行结果，包含影响的行数
    """
    try:
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 安全检查：禁止SELECT
        stripped = sql.strip().upper()
        if stripped.startswith("SELECT"):
            return "❌ execute_update 不支持 SELECT 语句。请使用 execute_query。"

        cursor.execute(sql)
        affected_rows = cursor.rowcount
        conn.commit()

        return (
            f"✅ 执行成功\n\n"
            f"| 属性 | 值 |\n"
            f"|------|----|\n"
            f"| SQL类型 | {stripped.split()[0]} |\n"
            f"| 影响行数 | {affected_rows} |\n"
        )
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        # 回滚事务
        try:
            conn = db_manager.get_conn()
            conn.rollback()
        except Exception:
            pass
        return f"❌ 执行失败: {str(e)}"


@mcp.tool()
def query_with_pagination(sql: str, page: int = 1, page_size: int = 20) -> str:
    """分页查询数据。

    将原始查询包装在子查询中，添加LIMIT和OFFSET实现分页。
    返回当前页数据及分页信息（总行数、总页数等）。

    Args:
        sql: 基础SELECT查询语句，如 'SELECT * FROM employees'
        page: 页码，从1开始（默认1）
        page_size: 每页行数（默认20）

    Returns:
        当前页数据（Markdown表格）及分页信息
    """
    try:
        if page < 1:
            return "❌ 页码必须大于等于1。"
        if page_size < 1 or page_size > 1000:
            return "❌ 每页行数必须在1到1000之间。"

        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 安全检查
        stripped = sql.strip().upper()
        if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
            return "❌ query_with_pagination 仅支持 SELECT 语句。"

        # 统计总行数
        count_sql = f"SELECT COUNT(*) FROM ({sql}) AS _count_subquery"
        cursor.execute(count_sql)
        total_rows = cursor.fetchone()[0]
        total_pages = (total_rows + page_size - 1) // page_size

        if total_rows == 0:
            return "查询结果为空，没有数据可分页。"

        # 计算偏移量
        offset = (page - 1) * page_size
        if offset >= total_rows:
            return f"❌ 页码 {page} 超出范围。共 {total_pages} 页。"

        # 执行分页查询
        page_sql = (
            f"SELECT * FROM ({sql}) AS _page_subquery "
            f"LIMIT {page_size} OFFSET {offset}"
        )
        cursor.execute(page_sql)
        rows = cursor.fetchall()
        column_names = (
            [desc[0] for desc in cursor.description] if cursor.description else []
        )

        # 格式化数据
        data = []
        for row in rows:
            data.append([row[i] for i in range(len(column_names))])

        # 构建结果
        result = "## 分页查询结果\n\n"
        result += format_markdown_table(column_names, data)
        result += "\n\n## 分页信息\n\n"
        result += format_markdown_table(
            ["属性", "值"],
            [
                ["当前页", str(page)],
                ["每页行数", str(page_size)],
                ["总行数", str(total_rows)],
                ["总页数", str(total_pages)],
                ["是否有上一页", "是" if page > 1 else "否"],
                ["是否有下一页", "是" if page < total_pages else "否"],
            ],
        )
        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 分页查询失败: {str(e)}"


@mcp.tool()
def export_query_result(sql: str, format: str = "csv") -> str:
    """导出查询结果为指定格式。

    支持CSV、JSON和Markdown三种格式。
    结果以文本形式返回，可复制保存到文件。

    Args:
        sql: SELECT查询语句
        format: 导出格式，可选 'csv'、'json' 或 'markdown'（默认 'csv'）

    Returns:
        导出的数据文本
    """
    try:
        format = format.lower().strip()
        if format not in ("csv", "json", "markdown"):
            return (
                "❌ 不支持的格式。请使用以下之一：\n"
                "- csv: 逗号分隔值\n"
                "- json: JSON格式\n"
                "- markdown: Markdown表格"
            )

        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 安全检查
        stripped = sql.strip().upper()
        if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
            return "❌ export_query_result 仅支持 SELECT 语句。"

        cursor.execute(sql)
        rows = cursor.fetchall()
        column_names = (
            [desc[0] for desc in cursor.description] if cursor.description else []
        )

        if not rows:
            return "查询结果为空，没有数据可导出。"

        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(column_names)
            for row in rows:
                writer.writerow([row[i] for i in range(len(column_names))])
            return f"```csv\n{output.getvalue()}```"

        elif format == "json":
            data_list = []
            for row in rows:
                record = {}
                for i, col in enumerate(column_names):
                    val = row[i]
                    # 处理不可序列化的类型
                    if hasattr(val, "isoformat"):
                        val = val.isoformat()
                    record[col] = val
                data_list.append(record)
            return f"```json\n{json.dumps(data_list, ensure_ascii=False, indent=2)}```"

        else:  # markdown
            data = []
            for row in rows:
                data.append([row[i] for i in range(len(column_names))])
            return format_markdown_table(column_names, data)
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 导出失败: {str(e)}"


@mcp.tool()
def explain_query(sql: str) -> str:
    """分析查询执行计划（EXPLAIN QUERY PLAN）。

    返回SQLite查询优化器的执行计划，帮助理解查询的执行方式，
    包括是否使用索引、扫描方式等信息。

    Args:
        sql: 要分析的SELECT查询语句

    Returns:
        执行计划详情（Markdown格式）
    """
    try:
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 安全检查
        stripped = sql.strip().upper()
        if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
            return "❌ explain_query 仅支持 SELECT 语句。"

        explain_sql = f"EXPLAIN QUERY PLAN {sql}"
        cursor.execute(explain_sql)
        rows = cursor.fetchall()

        if not rows:
            return "执行计划为空。"

        headers = ["序号", "节点ID", "父节点", "辅助字段", "详情"]
        data = []
        for i, row in enumerate(rows, 1):
            data.append([i, row[0], row[1], row[2], row[3]])

        result = "## 查询执行计划\n\n"
        result += f"**分析的SQL:** `{sql}`\n\n"
        result += format_markdown_table(headers, data)
        result += "\n\n**说明:**\n"
        result += "- `SCAN`: 全表扫描，考虑添加索引优化\n"
        result += "- `SEARCH`: 使用索引查找，效率较高\n"
        result += "- `USE INDEX`: 使用了指定索引\n"
        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 执行计划分析失败: {str(e)}"


@mcp.tool()
def count_rows(table_name: str) -> str:
    """统计指定表的总行数。

    Args:
        table_name: 表名，如 'employees'

    Returns:
        表的行数统计信息
    """
    try:
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 验证表名安全性
        _validate_identifier(table_name)

        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]

        headers = ["属性", "值"]
        rows = [
            ["表名", table_name],
            ["总行数", str(count)],
        ]
        return "## 行数统计\n\n" + format_markdown_table(headers, rows)
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 统计行数失败: {str(e)}"


def _validate_identifier(name: str) -> str:
    """验证SQL标识符（表名/列名）的合法性。

    仅允许字母、数字和下划线，且必须以字母或下划线开头。
    防止SQL注入。

    Args:
        name: 要验证的标识符

    Returns:
        验证通过的标识符

    Raises:
        ValueError: 如果标识符不合法
    """
    import re

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise ValueError(
            f"无效的标识符: '{name}'。仅允许字母、数字和下划线，"
            "且必须以字母或下划线开头。"
        )
    return name
