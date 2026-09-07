import argparse
import io
import os
import sys

import requests
from PIL import Image

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*a, **k):
        return False


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
DEFAULT_URL = "https://res.cloudinary.com/dy8vnstuw/image/upload/v1786702837/keralajersey/2026-08-13_Original.png"


def fail(msg, code=1):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--filename", default="migration_test.jpg")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    source_url = (args.url or "").strip()
    if not source_url.startswith("https://res.cloudinary.com/"):
        fail(
            "Refusing to test non-Cloudinary URL. Pass --url with a res.cloudinary.com product URL."
        )

    api_key = os.getenv("IMGPILE_API_KEY") or ""
    if not api_key:
        fail(
            "IMGPILE_API_KEY is not set. Set it in the environment or backend .env, then rerun. No upload attempted."
        )

    print("original Cloudinary URL: " + source_url)

    dl = requests.get(
        source_url,
        timeout=args.timeout,
        headers={"User-Agent": "keralajersey-migration-test/1.0"},
    )
    print("download HTTP status: " + str(dl.status_code))
    if dl.status_code < 200 or dl.status_code >= 300:
        fail("Download failed with status " + str(dl.status_code))
    data = dl.content or b""
    print("downloaded byte size: " + str(len(data)))
    if not data:
        fail("Downloaded bytes are empty.")
    content_type = (dl.headers.get("Content-Type") or "").split(";")[0].strip()
    print("detected content type: " + content_type)
    if not content_type.lower().startswith("image/"):
        fail("Download Content-Type is not an image: " + content_type)
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
    except Exception as e:
        fail("Pillow verification failed: " + str(e))
    try:
        with Image.open(io.BytesIO(data)) as im:
            print(
                "pillow format: "
                + str(im.format)
                + " size: "
                + str(im.size)
                + " mode: "
                + str(im.mode)
            )
    except Exception:
        pass

    upload_url = IMGPILE_UPLOADS_URL + "?filename=" + args.filename
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/octet-stream",
    }
    up = requests.post(upload_url, data=data, headers=headers, timeout=60)
    print("ImgPile HTTP status: " + str(up.status_code))
    if up.status_code != 201:
        print("ImgPile response body: " + up.text[:2000])
        fail("Expected HTTP 201 from ImgPile, got " + str(up.status_code))
    try:
        payload = up.json()
    except Exception as e:
        fail("ImgPile response is not JSON: " + str(e))
    node = payload.get("data") or {}
    urls = node.get("urls") or {}
    slug = node.get("slug") or ""
    filename = node.get("filename") or ""
    ext = node.get("ext") or ""
    original = urls.get("original") or ""
    processing = node.get("processing")
    discard = node.get("discard")
    print("ImgPile slug: " + str(slug))
    print("ImgPile filename: " + str(filename))
    print("ImgPile extension: " + str(ext))
    print("returned original CDN URL: " + str(original))
    print("processing status: " + str(processing))
    print("discard status: " + str(discard))
    if not original.startswith("https://"):
        fail("ImgPile original URL missing or invalid.")
    if "cdn.imgpile.com" not in original:
        print("WARNING: original URL host is not cdn.imgpile.com")

    v = requests.get(
        original, timeout=30, headers={"User-Agent": "keralajersey-migration-test/1.0"}
    )
    v_type = (v.headers.get("Content-Type") or "").split(";")[0].strip()
    v_len = len(v.content or b"")
    print("verification HTTP status: " + str(v.status_code))
    print("verification content type: " + v_type)
    print("verification byte size: " + str(v_len))
    if v.status_code != 200:
        fail("Verification failed: HTTP " + str(v.status_code))
    if not v_type.lower().startswith("image/") and v_type.lower() not in (
        "application/octet-stream",
    ):
        fail("Verification Content-Type is not an image: " + v_type)
    if v_len == 0:
        fail("Verification body is empty.")
    print("RESULT: PASS — single-image pipeline works. No database changes made.")


if __name__ == "__main__":
    main()
