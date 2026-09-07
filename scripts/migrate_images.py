import argparse
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from PIL import Image

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*a, **k):
        return False


import psycopg2
import psycopg2.extras

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(SCRIPT_DIR)
try:
    load_dotenv(os.path.join(BACKEND_ROOT, ".env"))
except Exception:
    pass
try:
    load_dotenv()
except Exception:
    pass

IMGPILE_UPLOADS_URL = "https://imgpile.com/uploads"
SELECT_SQL = "SELECT id, title, image1, image2, image3 FROM products ORDER BY id;"


def log_line(fh, obj):
    fh.write(json.dumps(obj) + "\n")
    fh.flush()


def classify(raw):
    if raw is None:
        return "empty"
    s = str(raw).strip()
    if s == "":
        return "empty"
    low = s.lower()
    if low in ("null", "none", "undefined", "uploading...", "uploading"):
        return "invalid"
    if not (low.startswith("http://") or low.startswith("https://")):
        return "invalid"
    if " " in s or "\n" in s or "\t" in s:
        return "invalid"
    try:
        host = (urlparse(s).netloc or "").lower()
    except Exception:
        return "invalid"
    if not host:
        return "invalid"
    if (
        "cdn.imgpile.com" in host
        or host.endswith(".imgpile.com")
        or host == "imgpile.com"
    ):
        return "imgpile"
    if "imgpile" in host:
        return "imgpile"
    if "cloudinary" in host:
        return "cloudinary"
    if "pinimg" in host:
        return "pinimg"
    return "other"


def download_image(url, timeout):
    r = requests.get(
        url, timeout=timeout, headers={"User-Agent": "keralajersey-migration/1.0"}
    )
    if r.status_code < 200 or r.status_code >= 300:
        raise RuntimeError("download HTTP " + str(r.status_code))
    data = r.content or b""
    if not data:
        raise RuntimeError("download empty body")
    ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip()
    if not ctype.lower().startswith("image/"):
        raise RuntimeError("download Content-Type not image: " + ctype)
    with Image.open(io.BytesIO(data)) as im:
        im.verify()
    with Image.open(io.BytesIO(data)) as im:
        fmt = str(im.format)
        size = [int(im.size[0]), int(im.size[1])]
    return data, ctype, fmt, size


def upload_imgpile(data, filename, api_key, timeout):
    url = IMGPILE_UPLOADS_URL + "?filename=" + filename
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/octet-stream",
    }
    last = None
    for attempt in range(5):
        r = requests.post(url, data=data, headers=headers, timeout=timeout)
        if r.status_code == 201:
            try:
                payload = r.json()
            except Exception as e:
                raise RuntimeError("imgpile non-JSON response: " + str(e))
            node = payload.get("data") or {}
            urls = node.get("urls") or {}
            original = urls.get("original") or ""
            if not original.startswith("https://"):
                raise RuntimeError("imgpile missing original URL")
            return r.status_code, node, original
        last = r.status_code
        body = (r.text or "")[:500]
        if r.status_code == 429 or (500 <= r.status_code < 600):
            time.sleep((2**attempt) * 3)
            continue
        raise RuntimeError("imgpile HTTP " + str(r.status_code) + " body: " + body)
    raise RuntimeError("imgpile retries exhausted, last HTTP " + str(last))


def verify_url(url, timeout):
    r = requests.get(
        url, timeout=timeout, headers={"User-Agent": "keralajersey-migration/1.0"}
    )
    if r.status_code != 200:
        raise RuntimeError("verify HTTP " + str(r.status_code))
    ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip()
    if (
        not ctype.lower().startswith("image/")
        and ctype.lower() != "application/octet-stream"
    ):
        raise RuntimeError("verify Content-Type not image: " + ctype)
    if not (r.content or b""):
        raise RuntimeError("verify empty body")
    return ctype, len(r.content)


def load_checkpoint(path):
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--delay", type=float, default=2.0)
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument(
        "--checkpoint", default=os.path.join(SCRIPT_DIR, "migration_checkpoint.json")
    )
    p.add_argument("--log", default="")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--product-id", default="")
    args = p.parse_args()

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)
    api_key = os.getenv("IMGPILE_API_KEY") or ""
    if not api_key:
        print(
            "ERROR: IMGPILE_API_KEY is not set. No uploads attempted.", file=sys.stderr
        )
        sys.exit(1)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = args.log or os.path.join(SCRIPT_DIR, "migration_log_" + stamp + ".jsonl")
    checkpoint = load_checkpoint(args.checkpoint)

    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(SELECT_SQL)
            rows = cur.fetchall()
    finally:
        conn.close()

    if args.product_id:
        rows = [r for r in rows if str(r.get("id")) == args.product_id]

    stats = {"total": 0, "success": 0, "skipped": 0, "failed": 0}
    processed = 0

    log_fh = open(log_path, "a", encoding="utf-8")
    try:
        for r in rows:
            pid = str(r.get("id"))
            title = r.get("title") or ""
            for slot in ("image1", "image2", "image3"):
                key = pid + "|" + slot
                if checkpoint.get(key, {}).get("status") == "success":
                    continue
                raw = r.get(slot)
                cls = classify(raw)
                old_url = "" if raw is None else str(raw).strip()
                if cls != "cloudinary":
                    stats["skipped"] += 1
                    checkpoint[key] = {
                        "status": "skipped_" + cls,
                        "at": datetime.now(timezone.utc).isoformat(),
                    }
                    continue
                if args.limit and stats["total"] >= args.limit:
                    continue
                stats["total"] += 1
                entry = {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "product_id": pid,
                    "product_title": title,
                    "slot": slot,
                    "old_url": old_url,
                    "dry_run": bool(args.dry_run),
                }
                try:
                    data, ctype, fmt, size = download_image(old_url, args.timeout)
                    entry["download_bytes"] = len(data)
                    entry["download_type"] = ctype
                    entry["pil_format"] = fmt
                    entry["pil_size"] = size
                    safe_title = "".join(c if c.isalnum() else "_" for c in pid)[:16]
                    fname = "kj_" + safe_title + "_" + slot + ".jpg"
                    _, node, new_url = upload_imgpile(data, fname, api_key, 60)
                    entry["imgpile_slug"] = node.get("slug") or ""
                    entry["imgpile_filename"] = node.get("filename") or ""
                    entry["imgpile_ext"] = node.get("ext") or ""
                    entry["new_url"] = new_url
                    entry["imgpile_discard"] = node.get("discard")
                    entry["imgpile_processing"] = node.get("processing")
                    vtype, vlen = verify_url(new_url, args.timeout)
                    entry["verify_type"] = vtype
                    entry["verify_bytes"] = vlen
                    if args.dry_run:
                        entry["status"] = "verified_dry_run"
                        stats["success"] += 1
                        checkpoint[key] = {
                            "status": "success",
                            "new_url": new_url,
                            "dry_run": True,
                        }
                        log_line(log_fh, entry)
                        print("DRY " + pid + " " + slot + " -> " + new_url)
                    else:
                        wc = psycopg2.connect(dsn)
                        try:
                            with wc.cursor() as cur:
                                cur.execute(
                                    "UPDATE products SET "
                                    + slot
                                    + " = %s, updated_at = now() WHERE id = %s AND "
                                    + slot
                                    + " = %s",
                                    (new_url, pid, old_url),
                                )
                                if cur.rowcount != 1:
                                    wc.rollback()
                                    raise RuntimeError(
                                        "row guard failed (rowcount="
                                        + str(cur.rowcount)
                                        + "), concurrent change?"
                                    )
                                wc.commit()
                        finally:
                            try:
                                wc.close()
                            except Exception:
                                pass
                        entry["status"] = "success"
                        stats["success"] += 1
                        checkpoint[key] = {
                            "status": "success",
                            "new_url": new_url,
                            "old_url": old_url,
                        }
                        log_line(log_fh, entry)
                        print("OK " + pid + " " + slot + " -> " + new_url)
                except Exception as e:
                    entry["status"] = "failed"
                    entry["error"] = str(e)[:500]
                    stats["failed"] += 1
                    checkpoint[key] = {"status": "failed", "error": str(e)[:300]}
                    log_line(log_fh, entry)
                    print("FAIL " + pid + " " + slot + " : " + str(e)[:200])
                processed += 1
                try:
                    with open(args.checkpoint, "w", encoding="utf-8") as cf:
                        json.dump(checkpoint, cf, indent=1)
                except Exception:
                    pass
                time.sleep(args.delay)
    finally:
        try:
            log_fh.close()
        except Exception:
            pass

    print("=== migration done ===")
    print("candidates attempted: " + str(stats["total"]))
    print("success: " + str(stats["success"]))
    print("skipped (non-cloudinary/resumed): " + str(stats["skipped"]))
    print("failed: " + str(stats["failed"]))
    print("log: " + log_path)
    print("checkpoint: " + args.checkpoint)


if __name__ == "__main__":
    main()
