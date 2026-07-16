# 数据库助手MCP服务器 (mcp-db-assistant)

[![CI](https://github.com/wzx11223344/mcp-db-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/wzx11223344/mcp-db-assistant/actions/workflows/ci.yml)

基于 MCP (Model Context Protocol) 协议的数据库操作服务器，使用 FastMCP 框架构建，为 AI 客户端提供数据库连接、查询、Schema 探索、数据分析和 SQL 生成工具。

## 特性

- **26个MCP工具**，覆盖数据库操作全流程
- **SQLite内置支持**，启动即用，无需额外安装数据库
- **PostgreSQL可选支持**，通过 psycopg2 扩展
- **自动示例数据库**，包含 employees / departments / salaries 三张表和索引
- **pandas数据分析**，提供表统计、列统计、数据质量报告、值分布等高级分析
- **SQL构建器**，参数化生成 SELECT / INSERT / UPDATE / CREATE TABLE / JOIN
- **安全防护**，标识符验证防止 SQL 注入，SELECT/UPDATE 分离执行

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务器

```bash
python server.py
```

服务器启动后会自动创建示例数据库 `sample.db` 并连接。

### 在MCP客户端中配置

在 MCP 客户端配置文件中添加：

```json
{
  "mcpServers": {
    "db-assistant": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/mcp-db-assistant"
    }
  }
}
```

## 示例数据库

启动时自动创建的 `sample.db` 包含以下表：

### departments（部门表）
| 列名 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 部门ID |
| name | TEXT | 部门名称 |
| manager_id | INTEGER FK | 部门经理(引用employees.id) |
| location | TEXT | 所在地 |
| budget | REAL | 预算 |

### employees（员工表）
| 列名 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 员工ID |
| name | TEXT | 姓名 |
| department_id | INTEGER FK | 部门ID(引用departments.id) |
| position | TEXT | 职位 |
| hire_date | TEXT | 入职日期 |
| email | TEXT UNIQUE | 邮箱 |
| is_active | INTEGER | 是否在职(1=是, 0=否) |

### salaries（工资表）
| 列名 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 工资记录ID |
| employee_id | INTEGER FK | 员工ID(引用employees.id) |
| amount | REAL | 工资金额 |
| effective_date | TEXT | 生效日期 |
| end_date | TEXT | 结束日期(NULL表示当前有效) |

## 工具列表

### 连接管理（4个）

| 工具 | 说明 |
|------|------|
| `connect_sqlite(db_path)` | 连接 SQLite 数据库 |
| `connect_postgres(host, port, db, user, password)` | 连接 PostgreSQL（可选） |
| `list_databases()` | 列出所有数据库 |
| `get_connection_status()` | 获取当前连接状态 |

### 查询工具（6个）

| 工具 | 说明 |
|------|------|
| `execute_query(sql)` | 执行 SELECT 查询，返回 Markdown 表格 |
| `execute_update(sql)` | 执行 INSERT/UPDATE/DELETE |
| `query_with_pagination(sql, page, page_size)` | 分页查询 |
| `export_query_result(sql, format)` | 导出结果（CSV/JSON/Markdown） |
| `explain_query(sql)` | 执行计划分析 |
| `count_rows(table_name)` | 统计表行数 |

### Schema 探索（5个）

| 工具 | 说明 |
|------|------|
| `list_tables()` | 列出所有表 |
| `describe_table(table_name)` | 表结构详情 |
| `list_indexes(table_name)` | 列出索引 |
| `get_table_ddl(table_name)` | 获取建表语句 |
| `get_foreign_keys(table_name)` | 获取外键关系 |

### 数据分析（6个）

| 工具 | 说明 |
|------|------|
| `table_stats(table_name)` | 表统计（行数/列数/大小） |
| `column_stats(table_name, column)` | 列统计（distinct/NULL/min/max/avg） |
| `data_quality_report(table_name)` | 数据质量报告（完整性/唯一性） |
| `table_sample(table_name, n)` | 表采样数据 |
| `null_analysis(table_name)` | NULL 值分析 |
| `value_distribution(table_name, column, bins)` | 值分布分析（直方图） |

### SQL 构建（5个）

| 工具 | 说明 |
|------|------|
| `build_select(table, columns, where, order_by, limit)` | 构建 SELECT 语句 |
| `build_insert(table, data)` | 构建 INSERT 语句（参数化） |
| `build_update(table, set_values, where)` | 构建 UPDATE 语句（参数化） |
| `build_create_table(table_name, columns)` | 构建 CREATE TABLE 语句 |
| `build_join(table1, table2, on, select_columns, join_type)` | 构建 JOIN 查询 |

## 项目结构

```
mcp-db-assistant/
├── server.py                # MCP Server入口（创建示例数据库+启动服务）
├── mcp_db_assistant/
│   ├── __init__.py           # 包初始化（创建FastMCP实例+注册工具）
│   ├── connection.py         # 数据库连接管理（4个工具）
│   ├── query_tools.py       # 查询工具（6个工具）
│   ├── schema_tools.py      # Schema探索工具（5个工具）
│   ├── analysis.py          # 数据分析工具（6个工具）
│   └── sql_builder.py       # SQL构建工具（5个工具）
├── README.md
├── SKILL.md
└── requirements.txt
```

## 技术栈

- **FastMCP** - MCP协议Python实现
- **sqlite3** - Python标准库，SQLite数据库引擎
- **pandas** - 数据分析和处理
- **psycopg2**（可选） - PostgreSQL数据库适配器

## 测试

运行单元测试：

```bash
pip install pytest flake8
pytest tests/ -v --tb=short
```

代码质量检查：

```bash
flake8 . --count --max-line-length=120 --statistics
```

## 许可证

MIT License
