#!/usr/bin/env python3
"""
Import products from CSV into a PostgreSQL `products` table.

Usage:
  Set `DATABASE_URL` env var or pass `--db` with the full DSN.
  python import_products.py --csv ../products_2026-05-21_01-14-57.csv

The script will create `products` table if it doesn't exist and upsert rows
based on the `$id` column from the CSV.
"""
import argparse
import csv
import json
import os
from decimal import Decimal
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS products (
  id TEXT PRIMARY KEY,
  permissions TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  title TEXT,
  description TEXT,
  image1 TEXT,
  image2 TEXT,
  image3 TEXT,
  available_sizes JSONB,
  stock_left INTEGER,
  price NUMERIC,
  stock BOOLEAN,
  free_delivery BOOLEAN,
  category TEXT,
  original_price NUMERIC,
  sub_category TEXT
);
"""

UPSERT_SQL = """
INSERT INTO products(
  id, permissions, created_at, updated_at, title, description,
  image1, image2, image3, available_sizes, stock_left, price, stock,
  free_delivery, category, original_price, sub_category
)
VALUES %s
ON CONFLICT (id) DO UPDATE SET
  permissions = EXCLUDED.permissions,
  created_at = EXCLUDED.created_at,
  updated_at = EXCLUDED.updated_at,
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  image1 = EXCLUDED.image1,
  image2 = EXCLUDED.image2,
  image3 = EXCLUDED.image3,
  available_sizes = EXCLUDED.available_sizes,
  stock_left = EXCLUDED.stock_left,
  price = EXCLUDED.price,
  stock = EXCLUDED.stock,
  free_delivery = EXCLUDED.free_delivery,
  category = EXCLUDED.category,
  original_price = EXCLUDED.original_price,
  sub_category = EXCLUDED.sub_category;
"""


def parse_bool(v):
    if v is None:
        return None
    v = v.strip().lower()
    if v in ("true", "1", "t", "yes", "y"):
        return True
    if v in ("false", "0", "f", "no", "n"):
        return False
    return None


def parse_json_like(v):
    if not v:
        return None
    try:
        # CSV contains doubled double-quotes like [""S"",""M""]
        cleaned = v.replace('""', '"')
        return json.loads(cleaned)
    except Exception:
        try:
            return json.loads(v)
        except Exception:
            return None


def to_decimal(v):
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v))
    except Exception:
        try:
            return Decimal(v)
        except Exception:
            return None


def row_to_tuple(row):
    id_ = row.get('$id') or row.get('id')
    permissions = row.get('$permissions')
    created_at = row.get('$createdAt')
    updated_at = row.get('$updatedAt')
    title = row.get('title')
    description = row.get('description')
    image1 = row.get('image1')
    image2 = row.get('image2')
    image3 = row.get('image3')
    available_sizes = parse_json_like(row.get('available_sizes'))
    stock_left = int(row['stock_left']) if row.get('stock_left') not in (None, "") else None
    price = to_decimal(row.get('price'))
    stock = parse_bool(row.get('stock'))
    free_delivery = parse_bool(row.get('free_delivery'))
    category = row.get('category')
    original_price = to_decimal(row.get('original_price'))
    sub_category = row.get('sub_category')
    return (
        id_, permissions, created_at, updated_at, title, description,
        image1, image2, image3, json.dumps(available_sizes) if available_sizes is not None else None,
        stock_left, price, stock, free_delivery, category, original_price, sub_category
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True, help='Path to products CSV file')
    parser.add_argument('--db', default=os.environ.get('DATABASE_URL'), help='Postgres DSN (or set DATABASE_URL)')
    parser.add_argument('--batch', type=int, default=500, help='Batch size for inserts')
    args = parser.parse_args()

    if not args.db:
        print('Database DSN is required via --db or DATABASE_URL env var')
        return

    conn = psycopg2.connect(args.db)
    conn.autocommit = True
    cur = conn.cursor()

    print('Creating table if not exists...')
    cur.execute(CREATE_TABLE_SQL)

    tuples = []
    total = 0
    with open(args.csv, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            tup = row_to_tuple(row)
            if tup[0] is None:
                continue
            tuples.append(tup)
            total += 1
            if len(tuples) >= args.batch:
                execute_values(cur, UPSERT_SQL, tuples, template=None)
                print(f'Upserted {len(tuples)} rows...')
                tuples = []

    if tuples:
        execute_values(cur, UPSERT_SQL, tuples, template=None)
        print(f'Upserted {len(tuples)} rows...')

    print(f'Done. Processed {total} rows.')
    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
