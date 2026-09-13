from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from campus_system.config import DB_CONFIG


def _build_db_config():
    return {**DB_CONFIG, "cursorclass": DictCursor}


@contextmanager
def db_cursor(commit=False):
    connection = pymysql.connect(**_build_db_config())
    cursor = connection.cursor()
    try:
        yield connection, cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def fetch_all(sql, params=None):
    with db_cursor() as (_, cursor):
        cursor.execute(sql, params or ())
        return cursor.fetchall()


def fetch_one(sql, params=None):
    with db_cursor() as (_, cursor):
        cursor.execute(sql, params or ())
        return cursor.fetchone()


def execute(sql, params=None):
    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, params or ())
        return cursor.rowcount
