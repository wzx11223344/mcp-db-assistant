"""Tests for mcp-db-assistant functions."""

import pytest
from mcp_db_assistant.sql_builder import (
    build_select, build_insert, build_update,
    build_create_table, build_join
)


class TestBuildSelect:
    """Tests for build_select function."""

    def test_select_all_columns(self):
        """Test building SELECT * query."""
        sql = build_select("employees")
        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "employees" in sql.lower()

    def test_select_specific_columns(self):
        """Test building SELECT with specific columns."""
        sql = build_select("employees", columns=["id", "name", "salary"])
        assert sql is not None
        assert "id" in sql
        assert "name" in sql

    def test_select_with_where(self):
        """Test building SELECT with WHERE clause."""
        sql = build_select("employees", where="department_id = 1")
        assert sql is not None
        assert "WHERE" in sql.upper()

    def test_select_with_order_by(self):
        """Test building SELECT with ORDER BY."""
        sql = build_select("employees", order_by="name ASC")
        assert sql is not None
        assert "ORDER BY" in sql.upper()

    def test_select_with_limit(self):
        """Test building SELECT with LIMIT."""
        sql = build_select("employees", limit=10)
        assert sql is not None
        assert "LIMIT" in sql.upper()


class TestBuildInsert:
    """Tests for build_insert function."""

    def test_build_insert_basic(self):
        """Test building a basic INSERT statement."""
        sql = build_insert(
            "employees",
            columns=["name", "position"],
            values=["张三", "工程师"]
        )
        assert sql is not None
        assert "INSERT" in sql.upper()
        assert "employees" in sql.lower()
        assert "name" in sql
        assert "position" in sql

    def test_build_insert_multiple_rows(self):
        """Test building INSERT with multiple rows."""
        sql = build_insert(
            "employees",
            columns=["name", "department_id"],
            values=[["张三", 1], ["李四", 2]]
        )
        assert sql is not None
        assert "INSERT" in sql.upper()

    def test_build_insert_no_columns(self):
        """Test that INSERT with no columns is handled."""
        sql = build_insert("employees", columns=[], values=[])
        assert sql is not None


class TestBuildUpdate:
    """Tests for build_update function."""

    def test_build_update_basic(self):
        """Test building a basic UPDATE statement."""
        sql = build_update(
            "employees",
            set_values={"name": "新名字"},
            where="id = 1"
        )
        assert sql is not None
        assert "UPDATE" in sql.upper()
        assert "SET" in sql.upper()
        assert "WHERE" in sql.upper()

    def test_build_update_multiple_columns(self):
        """Test building UPDATE with multiple columns."""
        sql = build_update(
            "employees",
            set_values={"salary": 20000, "position": "高级工程师"},
            where="id = 5"
        )
        assert sql is not None
        assert "salary" in sql
        assert "position" in sql

    def test_build_update_no_where(self):
        """Test building UPDATE without WHERE clause."""
        sql = build_update(
            "employees",
            set_values={"is_active": 1}
        )
        assert sql is not None
        assert "UPDATE" in sql.upper()


class TestBuildCreateTable:
    """Tests for build_create_table function."""

    def test_build_create_table_basic(self):
        """Test building a CREATE TABLE statement."""
        sql = build_create_table(
            "test_table",
            columns={
                "id": "INTEGER PRIMARY KEY",
                "name": "TEXT NOT NULL",
                "value": "REAL"
            }
        )
        assert sql is not None
        assert "CREATE TABLE" in sql.upper()
        assert "test_table" in sql
        assert "INTEGER PRIMARY KEY" in sql.upper()
        assert "TEXT NOT NULL" in sql.upper()

    def test_build_create_table_empty(self):
        """Test building CREATE TABLE with no columns."""
        sql = build_create_table("empty_table", columns={})
        assert sql is not None


class TestBuildJoin:
    """Tests for build_join function."""

    def test_build_inner_join(self):
        """Test building a JOIN query."""
        sql = build_join(
            table1="employees",
            table2="departments",
            join_type="INNER JOIN",
            on="employees.department_id = departments.id"
        )
        assert sql is not None
        assert "JOIN" in sql.upper()
        assert "employees" in sql.lower()
        assert "departments" in sql.lower()

    def test_build_left_join(self):
        """Test building a LEFT JOIN query."""
        sql = build_join(
            table1="employees",
            table2="salaries",
            join_type="LEFT JOIN",
            on="employees.id = salaries.employee_id"
        )
        assert sql is not None
        assert "LEFT JOIN" in sql.upper()
