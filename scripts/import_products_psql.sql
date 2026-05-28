-- SQL helper to load products CSV into PostgreSQL using psql's \copy (client-side)
-- Usage (from project root):
-- 1) Open a shell and set DATABASE_URL or pass it to psql directly.
--    PowerShell: $env:DATABASE_URL='postgresql://...'
-- 2) Run: psql "$DATABASE_URL" -f keralajersey_backend/scripts/import_products_psql.sql
--    Or run interactively and execute the \copy line below (replace path if needed).

-- 1) Create final table with the correct schema for this import
DROP TABLE IF EXISTS products;
CREATE TABLE products (
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

-- 2) Create a staging table matching the CSV headers (note the quoted names for $-prefixed headers)
DROP TABLE IF EXISTS products_stage;
CREATE TABLE products_stage (
  "$id" TEXT PRIMARY KEY,
  "$permissions" TEXT,
  "$createdAt" TIMESTAMPTZ,
  "$updatedAt" TIMESTAMPTZ,
  title TEXT,
  description TEXT,
  image1 TEXT,
  image2 TEXT,
  image3 TEXT,
  available_sizes TEXT,
  stock_left INTEGER,
  price NUMERIC,
  stock BOOLEAN,
  free_delivery BOOLEAN,
  category TEXT,
  original_price NUMERIC,
  sub_category TEXT
);

-- 3) Use psql's client-side COPY to load the local CSV into the staging table.
-- Run this from the project root so the relative path is correct, or change the path to the CSV file.
\copy products_stage FROM 'C:/Users/MY PC/keralajersey/keralajersey_backend/products_2026-05-21_01-14-57.csv' CSV HEADER NULL 'null'

-- The SQL below will move rows from staging into the final table (upsert by id).
-- You can run it after the \copy completes.

INSERT INTO products (id, permissions, created_at, updated_at, title, description,
  image1, image2, image3, available_sizes, stock_left, price, stock, free_delivery, category, original_price, sub_category)
SELECT
  "$id", "$permissions", "$createdAt", "$updatedAt", title, description,
  image1, image2, image3,
  CASE WHEN available_sizes IS NULL OR trim(available_sizes) = '' THEN NULL ELSE available_sizes::jsonb END,
  stock_left, price, stock, free_delivery, category, original_price, sub_category
FROM products_stage
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

-- Optional: drop staging table when done
-- DROP TABLE products_stage;
