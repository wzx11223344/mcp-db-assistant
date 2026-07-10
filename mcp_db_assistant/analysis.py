"""数据分析工具

提供表统计、列统计、数据质量报告、采样、NULL分析、值分布等MCP工具。
使用SQL查询结合pandas进行数据分析。
"""

import os

import pandas as pd

from mcp_db_assistant import mcp
from mcp_db_assistant import format_markdown_table
from mcp_db_assistant.connection import db_manager
from mcp_db_assistant.query_tools import _validate_identifier


@mcp.tool()
def table_stats(table_name: str) -> str:
    """获取表的统计信息（行数、列数、存储大小等）。

    Args:
        table_name: 表名，如 'employees'

    Returns:
        表统计信息（Markdown格式）
    """
    try:
        _validate_identifier(table_name)
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 行数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]

        # 列数
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_count = len(columns)

        # 列名列表
        col_names = [col[1] for col in columns]
        col_types = [col[2] or "未指定" for col in columns]

        # 索引数
        cursor.execute(f"PRAGMA index_list({table_name})")
        index_count = len(cursor.fetchall())

        # 外键数
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fk_count = len(cursor.fetchall())

        # 数据库文件大小（仅SQLite）
        db_size = ""
        if db_manager.db_type == "sqlite" and db_manager.db_path:
            if os.path.exists(db_manager.db_path):
                size_kb = os.path.getsize(db_manager.db_path) / 1024
                db_size = f"{size_kb:.1f} KB"

        headers = ["属性", "值"]
        rows = [
            ["表名", table_name],
            ["总行数", str(row_count)],
            ["列数", str(col_count)],
            ["索引数", str(index_count)],
            ["外键数", str(fk_count)],
            ["数据库文件大小", db_size or "N/A"],
        ]

        result = f"## 表统计: {table_name}\n\n"
        result += format_markdown_table(headers, rows)

        # 列信息
        result += "\n\n### 列信息\n\n"
        col_headers = ["序号", "列名", "类型"]
        col_data = []
        for i, (name, col_type) in enumerate(zip(col_names, col_types), 1):
            col_data.append([i, name, col_type])
        result += format_markdown_table(col_headers, col_data)

        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 获取表统计失败: {str(e)}"


@mcp.tool()
def column_stats(table_name: str, column: str) -> str:
    """获取列的统计信息（distinct值数、NULL比例、最值、分布等）。

    对数值列返回最小值、最大值、平均值、中位数等；
    对文本列返回不同值数量、最常见值等。

    Args:
        table_name: 表名，如 'employees'
        column: 列名，如 'salary'

    Returns:
        列统计信息（Markdown格式）
    """
    try:
        _validate_identifier(table_name)
        _validate_identifier(column)
        conn = db_manager.get_conn()

        # 使用pandas读取数据
        df = pd.read_sql_query(f"SELECT {column} FROM {table_name}", conn)
        col_data = df[column]
        total_count = len(col_data)

        if total_count == 0:
            return f"表 '{table_name}' 没有数据。"

        # 基本统计
        null_count = col_data.isnull().sum()
        non_null = total_count - null_count
        distinct_count = col_data.nunique()
        null_ratio = (null_count / total_count * 100) if total_count > 0 else 0

        headers = ["属性", "值"]
        rows = [
            ["表名", table_name],
            ["列名", column],
            ["总行数", str(total_count)],
            ["非空值数", str(non_null)],
            ["NULL值数", str(null_count)],
            ["NULL比例", f"{null_ratio:.2f}%"],
            ["不同值数", str(distinct_count)],
        ]

        # 根据数据类型添加不同的统计
        if pd.api.types.is_numeric_dtype(col_data):
            non_null_data = col_data.dropna()
            if len(non_null_data) > 0:
                rows.append(["最小值", str(non_null_data.min())])
                rows.append(["最大值", str(non_null_data.max())])
                rows.append(["平均值", f"{non_null_data.mean():.2f}"])
                rows.append(["中位数", str(non_null_data.median())])
                rows.append(["标准差", f"{non_null_data.std():.2f}"])
                rows.append(["总和", f"{non_null_data.sum():.2f}"])
        else:
            # 文本列：最常见值
            value_counts = col_data.value_counts()
            if len(value_counts) > 0:
                most_common = value_counts.index[0]
                most_common_count = value_counts.iloc[0]
                rows.append(["最常见值", str(most_common)])
                rows.append(["最常见值出现次数", str(most_common_count)])

        result = f"## 列统计: {table_name}.{column}\n\n"
        result += format_markdown_table(headers, rows)

        # 最常见值（Top 5）
        value_counts = col_data.value_counts().head(5)
        if len(value_counts) > 0:
            result += "\n\n### 最常见值 (Top 5)\n\n"
            vc_headers = ["排名", "值", "出现次数", "占比"]
            vc_data = []
            for rank, (val, count) in enumerate(value_counts.items(), 1):
                ratio = count / total_count * 100
                vc_data.append([rank, str(val), count, f"{ratio:.2f}%"])
            result += format_markdown_table(vc_headers, vc_data)

        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 获取列统计失败: {str(e)}"


@mcp.tool()
def data_quality_report(table_name: str) -> str:
    """生成数据质量报告（完整性、唯一性、一致性）。

    对每列进行完整性（NULL比例）、唯一性（重复值比例）检查，
    并给出整体质量评分和改进建议。

    Args:
        table_name: 表名，如 'employees'

    Returns:
        数据质量报告（Markdown格式）
    """
    try:
        _validate_identifier(table_name)
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 获取列信息
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()

        if not columns_info:
            return f"❌ 表 '{table_name}' 不存在。"

        # 读取数据
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        total_rows = len(df)

        if total_rows == 0:
            return f"表 '{table_name}' 没有数据，无法生成质量报告。"

        # 每列的质量分析
        headers = ["列名", "类型", "NULL数", "NULL比例", "不同值数", "重复值数", "完整性", "唯一性"]
        data = []
        quality_scores = []

        for col_info in columns_info:
            col_name = col_info[1]
            col_type = col_info[2] or "未指定"

            col_data = df[col_name]
            null_count = col_data.isnull().sum()
            null_ratio = null_count / total_rows * 100
            distinct = col_data.nunique()
            duplicate = total_rows - distinct

            # 完整性评分 (0-100)
            completeness = 100 - null_ratio
            # 唯一性评分 (0-100)
            uniqueness = (distinct / total_rows * 100) if total_rows > 0 else 0

            quality_scores.append((completeness, uniqueness))

            data.append([
                col_name,
                col_type,
                str(null_count),
                f"{null_ratio:.2f}%",
                str(distinct),
                str(duplicate),
                f"{completeness:.1f}%",
                f"{uniqueness:.1f}%",
            ])

        result = f"## 数据质量报告: {table_name}\n\n"
        result += f"**总行数:** {total_rows}\n**列数:** {len(columns_info)}\n\n"
        result += "### 列级质量分析\n\n"
        result += format_markdown_table(headers, data)

        # 整体评分
        avg_completeness = sum(s[0] for s in quality_scores) / len(quality_scores)
        avg_uniqueness = sum(s[1] for s in quality_scores) / len(quality_scores)
        overall_score = (avg_completeness + avg_uniqueness) / 2

        result += "\n\n### 整体质量评分\n\n"
        result += format_markdown_table(
            ["指标", "评分"],
            [
                ["平均完整性", f"{avg_completeness:.1f}%"],
                ["平均唯一性", f"{avg_uniqueness:.1f}%"],
                ["综合质量评分", f"{overall_score:.1f}%"],
            ],
        )

        # 改进建议
        suggestions = []
        for i, col_info in enumerate(columns_info):
            col_name = col_info[1]
            completeness, uniqueness = quality_scores[i]
            if completeness < 90:
                suggestions.append(
                    f"- **{col_name}**: 完整性较低 ({completeness:.1f}%)，"
                    f"建议检查数据录入流程或设置默认值"
                )
            if uniqueness < 10 and col_type.upper() not in ("INTEGER", "REAL"):
                suggestions.append(
                    f"- **{col_name}**: 唯一性较低 ({uniqueness:.1f}%)，"
                    f"存在大量重复值"
                )

        if suggestions:
            result += "\n\n### 改进建议\n\n"
            result += "\n".join(suggestions)
        else:
            result += "\n\n✅ 数据质量良好，无需特别改进。"

        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 生成数据质量报告失败: {str(e)}"


@mcp.tool()
def table_sample(table_name: str, n: int = 10) -> str:
    """获取表的随机采样数据。

    返回指定数量的样本行，用于快速了解表内容。
    使用LIMIT和随机排序获取样本。

    Args:
        table_name: 表名，如 'employees'
        n: 采样行数，默认10，最大100

    Returns:
        采样数据（Markdown表格格式）
    """
    try:
        if n < 1 or n > 100:
            return "❌ 采样行数必须在1到100之间。"

        _validate_identifier(table_name)
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 使用LIMIT获取前n行
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {n}")
        rows = cursor.fetchall()
        column_names = (
            [desc[0] for desc in cursor.description] if cursor.description else []
        )

        if not rows:
            return f"表 '{table_name}' 没有数据。"

        data = []
        for row in rows:
            data.append([row[i] for i in range(len(column_names))])

        result = f"## 表 '{table_name}' 采样数据 (前{n}行)\n\n"
        result += format_markdown_table(column_names, data)
        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 获取采样数据失败: {str(e)}"


@mcp.tool()
def null_analysis(table_name: str) -> str:
    """分析表中每列的NULL值情况。

    对每列计算NULL值的数量和比例，
    帮助识别数据缺失问题和需要填充的列。

    Args:
        table_name: 表名，如 'employees'

    Returns:
        NULL值分析报告（Markdown格式）
    """
    try:
        _validate_identifier(table_name)
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 获取列信息
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()

        if not columns_info:
            return f"❌ 表 '{table_name}' 不存在。"

        # 读取数据
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        total_rows = len(df)

        if total_rows == 0:
            return f"表 '{table_name}' 没有数据。"

        headers = ["列名", "类型", "NULL数", "非空数", "NULL比例", "状态"]
        data = []

        for col_info in columns_info:
            col_name = col_info[1]
            col_type = col_info[2] or "未指定"
            not_null = col_info[3]  # 是否NOT NULL约束

            null_count = df[col_name].isnull().sum()
            non_null = total_rows - null_count
            null_ratio = null_count / total_rows * 100

            if null_count == 0:
                status = "✅ 完整"
            elif null_ratio > 50:
                status = "❌ 严重缺失"
            elif null_ratio > 10:
                status = "⚠️ 部分缺失"
            else:
                status = "⚠️ 轻微缺失"

            data.append([
                col_name,
                col_type,
                str(null_count),
                str(non_null),
                f"{null_ratio:.2f}%",
                status,
            ])

        result = f"## NULL值分析: {table_name}\n\n"
        result += f"**总行数:** {total_rows}\n\n"
        result += format_markdown_table(headers, data)

        # 汇总
        total_nulls = sum(df[col[1]].isnull().sum() for col in columns_info)
        total_cells = total_rows * len(columns_info)
        overall_null_ratio = total_nulls / total_cells * 100 if total_cells > 0 else 0

        result += "\n\n### 汇总\n\n"
        result += format_markdown_table(
            ["指标", "值"],
            [
                ["总单元格数", str(total_cells)],
                ["NULL单元格数", str(total_nulls)],
                ["整体NULL比例", f"{overall_null_ratio:.2f}%"],
            ],
        )

        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ NULL分析失败: {str(e)}"


@mcp.tool()
def value_distribution(table_name: str, column: str, bins: int = 10) -> str:
    """分析指定列的值分布。

    对数值列进行分箱统计（直方图），
    对文本列进行值频率统计。
    帮助理解数据分布特征。

    Args:
        table_name: 表名，如 'employees'
        column: 列名，如 'salary'
        bins: 分箱数量，默认10，最大50

    Returns:
        值分布分析（Markdown格式）
    """
    try:
        if bins < 1 or bins > 50:
            return "❌ 分箱数量必须在1到50之间。"

        _validate_identifier(table_name)
        _validate_identifier(column)
        conn = db_manager.get_conn()

        # 读取数据
        df = pd.read_sql_query(f"SELECT {column} FROM {table_name}", conn)
        col_data = df[column].dropna()
        total_count = len(df)

        if total_count == 0:
            return f"表 '{table_name}' 没有数据。"

        if len(col_data) == 0:
            return f"列 '{column}' 的所有值都是NULL，无法分析分布。"

        result = f"## 值分布分析: {table_name}.{column}\n\n"
        result += f"**总行数:** {total_count}\n**非空值数:** {len(col_data)}\n\n"

        if pd.api.types.is_numeric_dtype(col_data):
            # 数值列：分箱统计
            min_val = col_data.min()
            max_val = col_data.max()
            result += f"**最小值:** {min_val}\n**最大值:** {max_val}\n\n"

            # 使用pd.cut进行分箱
            bins_result = pd.cut(col_data, bins=bins, include_lowest=True)
            value_counts = bins_result.value_counts().sort_index()

            headers = ["区间", "计数", "占比", "柱状图"]
            data = []
            max_count = value_counts.max()

            for interval, count in value_counts.items():
                ratio = count / len(col_data) * 100
                bar_len = int(count / max_count * 30) if max_count > 0 else 0
                bar = "█" * bar_len
                data.append([str(interval), count, f"{ratio:.2f}%", bar])

            result += "### 分箱分布\n\n"
            result += format_markdown_table(headers, data)

            # 统计摘要
            result += "\n\n### 统计摘要\n\n"
            result += format_markdown_table(
                ["指标", "值"],
                [
                    ["均值", f"{col_data.mean():.2f}"],
                    ["中位数", f"{col_data.median():.2f}"],
                    ["标准差", f"{col_data.std():.2f}"],
                    ["25%分位数", f"{col_data.quantile(0.25):.2f}"],
                    ["75%分位数", f"{col_data.quantile(0.75):.2f}"],
                ],
            )
        else:
            # 文本列：值频率统计
            value_counts = col_data.value_counts().head(bins)

            headers = ["排名", "值", "计数", "占比", "柱状图"]
            data = []
            max_count = value_counts.max()

            for rank, (val, count) in enumerate(value_counts.items(), 1):
                ratio = count / len(col_data) * 100
                bar_len = int(count / max_count * 30) if max_count > 0 else 0
                bar = "█" * bar_len
                data.append([rank, str(val), count, f"{ratio:.2f}%", bar])

            result += "### 值频率分布 (Top " + str(bins) + ")\n\n"
            result += format_markdown_table(headers, data)

            distinct_count = col_data.nunique()
            result += (
                f"\n\n**不同值总数:** {distinct_count}\n"
                f"**显示前 {min(bins, distinct_count)} 个值**"
            )

        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 值分布分析失败: {str(e)}"
