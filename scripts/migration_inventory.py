import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*a, **k):
        return False


import psycopg2
import psycopg2.extras

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(SCRIPT_DIR)
for _p in (BACKEND_ROOT, os.getcwd()):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    load_dotenv(os.path.join(BACKEND_ROOT, ".env"))
except Exception:
    pass
try:
    load_dotenv()
except Exception:
    pass

SELECT_SQL = "SELECT id, title, image1, image2, image3 FROM products ORDER BY id;"

KNOWN_EXTS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",
    "avif",
    "mp4",
    "mov",
    "webm",
    "svg",
    "bmp",
}


def get_connection(dsn):
    if not dsn:
        dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in .env or pass --db."
        )
    conn = psycopg2.connect(dsn)
    try:
        conn.set_session(readonly=True, autocommit=True)
    except Exception:
        pass
    return conn


def classify_url(raw):
    if raw is None:
        return ("empty", "", "", "unknown")
    s = str(raw).strip()
    if s == "":
        return ("empty", "", "", "unknown")
    if len(s) > 2048 or " " in s or "\n" in s or "\t" in s:
        return ("invalid", "", "", detect_extension(s))
    low = s.lower()
    if low in ("null", "none", "undefined", "uploading...", "uploading"):
        return ("invalid", "", "", "unknown")
    if not (low.startswith("http://") or low.startswith("https://")):
        return ("invalid", "", "", detect_extension(s))
    try:
        parts = urlparse(s)
    except Exception:
        return ("invalid", "", "", "unknown")
    host = (parts.netloc or "").lower()
    if not host:
        return ("invalid", "", "", detect_extension(s))
    if (
        "cdn.imgpile.com" in host
        or host == "imgpile.com"
        or host.endswith(".imgpile.com")
    ):
        return ("imgpile", host, "", detect_extension(s))
    if "imgpile" in host:
        return ("imgpile", host, "", detect_extension(s))
    if "cloudinary" in host:
        return (
            "cloudinary",
            host,
            extract_cloudinary_cloud(host, parts.path),
            detect_extension(s),
        )
    if "pinimg" in host:
        return ("pinimg", host, "", detect_extension(s))
    return ("other", host, "", detect_extension(s))


def extract_cloudinary_cloud(host, path):
    if host == "res.cloudinary.com":
        seg = (path or "").strip("/").split("/")
        if seg and seg[0]:
            return seg[0]
        return ""
    return host


def detect_extension(raw):
    try:
        s = str(raw or "").strip().split("?")[0].split("#")[0]
        s = s.rstrip("/")
        name = s.rsplit("/", 1)[-1]
        if "." not in name:
            return "unknown"
        ext = name.rsplit(".", 1)[-1].lower().strip()
        ext = re.sub(r"[^a-z0-9]", "", ext)
        if not ext:
            return "unknown"
        if ext in KNOWN_EXTS:
            return ext
        if len(ext) <= 5:
            return "other:" + ext
        return "unknown"
    except Exception:
        return "unknown"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--out-dir", default=SCRIPT_DIR)
    parser.add_argument("--out-file", default="")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = args.out_file or os.path.join(
        args.out_dir, "inventory_" + stamp + ".csv"
    )

    conn = get_connection(args.db)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(SELECT_SQL)
            rows = cur.fetchall()
    finally:
        try:
            conn.close()
        except Exception:
            pass

    total_products = len(rows)
    total_slots = total_products * 3
    filled = 0
    empty = 0
    class_counts = Counter()
    cloud_counts = Counter()
    host_counts = Counter()
    ext_counts = Counter()
    url_counts = Counter()
    per_product_filled = []
    records = []

    for r in rows:
        pid = r.get("id")
        title = r.get("title") or ""
        n_filled = 0
        for slot in ("image1", "image2", "image3"):
            raw = r.get(slot)
            classification, host, cloud, ext = classify_url(raw)
            old_url = "" if raw is None else str(raw).strip()
            if classification == "empty":
                old_url = ""
                host = ""
                cloud = ""
                ext = "unknown"
                empty += 1
            else:
                filled += 1
                n_filled += 1
                if old_url:
                    url_counts[old_url] += 1
            class_counts[classification] += 1
            if host:
                host_counts[host] += 1
            if classification == "cloudinary":
                cloud_counts[cloud or "(unknown-cloud)"] += 1
            ext_counts[ext] += 1
            records.append(
                {
                    "product_id": pid,
                    "product_title": title,
                    "slot": slot,
                    "old_url": old_url,
                    "host": host,
                    "classification": classification,
                    "cloudinary_cloud": cloud,
                    "extension": ext,
                }
            )
        per_product_filled.append(n_filled)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "product_id",
                "product_title",
                "slot",
                "old_url",
                "host",
                "classification",
                "cloudinary_cloud",
                "extension",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    dup_urls = sum(1 for _, c in url_counts.items() if c > 1)
    dup_occurrences = sum(c for _, c in url_counts.items() if c > 1)
    n1 = sum(1 for n in per_product_filled if n == 1)
    n2 = sum(1 for n in per_product_filled if n == 2)
    n3 = sum(1 for n in per_product_filled if n == 3)
    n0 = sum(1 for n in per_product_filled if n == 0)
    already = sum(1 for rec in records if rec["host"] == "cdn.imgpile.com")

    print("=== Product image inventory (READ-ONLY) ===")
    print("output: " + out_path)
    print("total products: " + str(total_products))
    print("total image slots examined: " + str(total_slots))
    print("filled image slots: " + str(filled))
    print("empty image slots: " + str(empty))
    print("cloudinary: " + str(class_counts.get("cloudinary", 0)))
    print(
        "imgpile: "
        + str(class_counts.get("imgpile", 0))
        + " (cdn.imgpile.com: "
        + str(already)
        + " already-migrated, do not touch)"
    )
    print("pinimg: " + str(class_counts.get("pinimg", 0)))
    print("other: " + str(class_counts.get("other", 0)))
    print("invalid: " + str(class_counts.get("invalid", 0)))
    print("empty: " + str(class_counts.get("empty", 0)))
    print("--- by cloudinary cloud ---")
    if cloud_counts:
        for k, v in cloud_counts.most_common():
            print("  " + str(k) + ": " + str(v))
    else:
        print("  (none)")
    print("--- by host (top 20) ---")
    if host_counts:
        for k, v in host_counts.most_common(20):
            print("  " + str(k) + ": " + str(v))
    else:
        print("  (none)")
    print("--- by extension ---")
    for k, v in ext_counts.most_common():
        print("  " + str(k) + ": " + str(v))
    print("duplicate urls (distinct urls used >1 time): " + str(dup_urls))
    print("duplicate occurrences (slots sharing a url): " + str(dup_occurrences))
    print("products with 0 images: " + str(n0))
    print("products with 1 image: " + str(n1))
    print("products with 2 images: " + str(n2))
    print("products with 3 images: " + str(n3))
    print("note: duplicates are reported only, not treated as errors.")


if __name__ == "__main__":
    main()
