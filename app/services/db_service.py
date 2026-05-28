import json
import uuid
from psycopg2.extras import RealDictCursor
from app.config import get_db_connection

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


class DBService:
    @staticmethod
    def ensure_table_exists():
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)
                conn.commit()

    @staticmethod
    def _row_to_product(row):
        if not row:
            return None

        return {
            "$id": row.get("id"),
            "title": row.get("title"),
            "description": row.get("description"),
            "category": row.get("category"),
            "available_sizes": row.get("available_sizes") or [],
            "stock": bool(row.get("stock")) if row.get("stock") is not None else True,
            "stock_left": row.get("stock_left") if row.get("stock_left") is not None else 0,
            "price": float(row["price"]) if row.get("price") is not None else 0.0,
            "original_price": float(row["original_price"]) if row.get("original_price") is not None else None,
            "sub_category": row.get("sub_category"),
            "free_delivery": bool(row.get("free_delivery")) if row.get("free_delivery") is not None else False,
            "image1": row.get("image1"),
            "image2": row.get("image2"),
            "image3": row.get("image3"),
        }

    @staticmethod
    def create_product(product):
        DBService.ensure_table_exists()
        product_data = product.model_dump()
        product_id = str(uuid.uuid4())
        available_sizes = json.dumps(product_data.get("available_sizes")) if product_data.get("available_sizes") is not None else None

        insert_sql = """
INSERT INTO products(
  id, title, description, image1, image2, image3, available_sizes,
  stock_left, price, stock, free_delivery, category, original_price, sub_category,
  created_at, updated_at
) VALUES (
  %(id)s, %(title)s, %(description)s, %(image1)s, %(image2)s, %(image3)s,
  %(available_sizes)s, %(stock_left)s, %(price)s, %(stock)s, %(free_delivery)s,
  %(category)s, %(original_price)s, %(sub_category)s, now(), now()
) RETURNING *;
"""

        params = {
            "id": product_id,
            "title": product_data.get("title"),
            "description": product_data.get("description"),
            "image1": product_data.get("image1"),
            "image2": product_data.get("image2"),
            "image3": product_data.get("image3"),
            "available_sizes": available_sizes,
            "stock_left": product_data.get("stock_left"),
            "price": product_data.get("price"),
            "stock": product_data.get("stock"),
            "free_delivery": product_data.get("free_delivery"),
            "category": product_data.get("category"),
            "original_price": product_data.get("original_price"),
            "sub_category": product_data.get("sub_category"),
        }

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(insert_sql, params)
                row = cur.fetchone()
                conn.commit()
                return DBService._row_to_product(row)

    @staticmethod
    def get_products():
        DBService.ensure_table_exists()
        query = "SELECT * FROM products ORDER BY created_at DESC NULLS LAST;"
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                rows = cur.fetchall()
                return [DBService._row_to_product(row) for row in rows]

    @staticmethod
    def get_product(product_id: str):
        DBService.ensure_table_exists()
        query = "SELECT * FROM products WHERE id = %s;"
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (product_id,))
                row = cur.fetchone()
                return DBService._row_to_product(row)

    @staticmethod
    def update_product(product_id: str, product_update):
        DBService.ensure_table_exists()
        data = product_update.model_dump(exclude_unset=True)
        if not data:
            return DBService.get_product(product_id)

        set_clauses = []
        params = {"id": product_id}
        for key, value in data.items():
            if key == "available_sizes":
                value = json.dumps(value) if value is not None else None
            set_clauses.append(f"{key} = %({key})s")
            params[key] = value

        set_clauses.append("updated_at = now()")
        query = f"UPDATE products SET {', '.join(set_clauses)} WHERE id = %(id)s RETURNING *;"

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                conn.commit()
                return DBService._row_to_product(row)

    @staticmethod
    def delete_product(product_id: str):
        DBService.ensure_table_exists()
        query = "DELETE FROM products WHERE id = %s;"
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (product_id,))
                conn.commit()
