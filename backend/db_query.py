#!/usr/bin/env python3
"""Standalone CLI tool for running read-only queries against the brobiotic database."""

import argparse
import asyncio
import os

import asyncpg


DEFAULT_DATABASE_URL = "postgresql://localhost:5432/brobiotic"


async def run_query(sql: str, database_url: str) -> None:
    conn = await asyncpg.connect(database_url)
    try:
        async with conn.transaction():
            await conn.execute("SET TRANSACTION READ ONLY")
            stmt = await conn.prepare(sql)
            columns = [attr.name for attr in stmt.get_attributes()]
            rows = await stmt.fetch()
    finally:
        await conn.close()

    if not columns:
        print("(no results)")
        return

    # Convert all values to strings for display
    str_rows = [[str(v) for v in row.values()] for row in rows]

    # Calculate column widths
    widths = [len(c) for c in columns]
    for row in str_rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    # Print header
    header = "  ".join(col.ljust(w) for col, w in zip(columns, widths))
    print(header)
    print("  ".join("-" * w for w in widths))

    # Print rows
    for row in str_rows:
        print("  ".join(val.ljust(w) for val, w in zip(row, widths)))

    print(f"\n({len(str_rows)} row{'s' if len(str_rows) != 1 else ''})")


def main():
    parser = argparse.ArgumentParser(description="Run a read-only SQL query against the brobiotic database")
    parser.add_argument("sql", help="SQL query to execute")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    asyncio.run(run_query(args.sql, database_url))


if __name__ == "__main__":
    main()
