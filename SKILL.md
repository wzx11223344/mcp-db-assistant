# Skill: 数据库助手MCP服务器

## 概述

数据库助手MCP服务器是一个基于MCP协议的数据库操作服务，为AI客户端提供完整的数据库交互能力，包括连接管理、SQL查询、Schema探索、数据分析和SQL生成。

## 触发条件

当用户需要以下操作时使用本技能：
- 连接和查询SQLite/PostgreSQL数据库
- 探索数据库Schema（表结构、索引、外键）
- 分析数据质量、分布、统计信息
- 构建SELECT/INSERT/UPDATE/CREATE TABLE/JOIN等SQL语句
- 分页查询、导出查询结果
- 分析查询执行计划

## 核心能力

### 1. 数据库连接管理
- `connect_sqlite`: 连接SQLite数据库文件
- `connect_postgres`: 连接PostgreSQL（需安装psycopg2）
- `list_databases`: 列出附加数据库
- `get_connection_status`: 获取连接状态

### 2. SQL查询执行
- `execute_query`: 执行SELECT，返回Markdown表格
- `execute_update`: 执行INSERT/UPDATE/DELETE
- `query_with_pagination`: 分页查询，自动计算总页数
- `export_query_result`: 导出为CSV/JSON/Markdown格式
- `explain_query`: EXPLAIN QUERY PLAN分析
- `count_rows`: 快速统计表行数

### 3. Schema探索
- `list_tables`: 列出所有表和视图
- `describe_table`: 表结构（列名/类型/约束/默认值/主键）
- `list_indexes`: 索引列表及创建语句
- `get_table_ddl`: 完整建表DDL
- `get_foreign_keys`: 外键关系（引用表/列/级联行为）

### 4. 数据分析（使用pandas）
- `table_stats`: 表级统计（行数/列数/索引数/外键数/文件大小）
- `column_stats`: 列级统计（distinct值/NULL比例/min/max/avg/中位数/标准差/Top5值）
- `data_quality_report`: 数据质量评分（完整性/唯一性/改进建议）
- `table_sample`: 表采样数据（前N行）
- `null_analysis`: 每列NULL值分析（数量/比例/状态）
- `value_distribution`: 值分布直方图（数值列分箱/文本列频率）

### 5. SQL构建（参数化）
- `build_select`: 构建SELECT语句
- `build_insert`: 构建参数化INSERT
- `build_update`: 构建参数化UPDATE
- `build_create_table`: 构建CREATE TABLE
- `build_join`: 构建JOIN查询（INNER/LEFT/RIGHT/FULL/CROSS）

## 使用示例

### 示例1：查询所有员工信息
```
工具: execute_query
参数: sql = "SELECT e.name, d.name AS department, e.position, e.hire_date FROM employees e JOIN departments d ON e.department_id = d.id ORDER BY e.hire_date"
```

### 示例2：分析工资分布
```
工具: value_distribution
参数: table_name = "salaries", column = "amount", bins = 10
```

### 示例3：数据质量报告
```
工具: data_quality_report
参数: table_name = "employees"
```

### 示例4：构建插入语句
```
工具: build_insert
参数: table = "employees", data = '{"name": "新员工", "department_id": 1, "position": "工程师", "email": "new@example.com", "is_active": 1}'
```

### 示例5：分页查询
```
工具: query_with_pagination
参数: sql = "SELECT * FROM employees ORDER BY id", page = 1, page_size = 5
```

## 技术细节

- **数据库引擎**: SQLite (Python sqlite3标准库) / PostgreSQL (psycopg2可选)
- **分析库**: pandas用于统计计算和数据质量分析
- **安全防护**: SQL标识符正则验证，SELECT/UPDATE分离执行
- **连接管理**: 全局ConnectionManager单例，线程安全(check_same_thread=False)
- **返回格式**: 所有工具返回Markdown格式字符串
- **示例数据**: 5个部门、20名员工、20条工资记录，含索引和外键
