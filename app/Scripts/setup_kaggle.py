"""
setup_kaggle.py

Downloads the Olist Brazilian E-Commerce dataset from Kaggle.
Reads credentials from .env — no kaggle.json file needed.

Run from project root:
    python scripts/setup_kaggle.py
"""

import os
import sys
import zipfile
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from project root ──────────────────────────────────────────────
load_dotenv()

KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
KAGGLE_API_KEY  = os.getenv("KAGGLE_API_KEY")

if not KAGGLE_USERNAME or not KAGGLE_API_KEY:
    print("ERROR: KAGGLE_USERNAME or KAGGLE_API_KEY not found in .env")
    print("Add these to your .env file:")
    print("  KAGGLE_USERNAME=your_username")
    print("  KAGGLE_API_KEY=your_api_key")
    sys.exit(1)

# Kaggle library reads from these env vars natively
os.environ["KAGGLE_USERNAME"] = KAGGLE_USERNAME
os.environ["KAGGLE_KEY"]      = KAGGLE_API_KEY

# ── Directories ───────────────────────────────────────────────────────────────
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

DATASET_SLUG = "olistbr/brazilian-ecommerce"

EXPECTED_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_geolocation_dataset.csv",
]


def download_dataset():
    """Download Olist dataset from Kaggle."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("ERROR: kaggle package not installed.")
        print("Run: pip install kaggle")
        sys.exit(1)

    print(f"Authenticating with Kaggle as '{KAGGLE_USERNAME}'...")
    api = KaggleApi()
    api.authenticate()
    print("Authentication successful.")

    print(f"\nDownloading dataset: {DATASET_SLUG}")
    print(f"Destination: {RAW_DIR}/")
    api.dataset_download_files(
        DATASET_SLUG,
        path=str(RAW_DIR),
        unzip=False,   # We unzip manually for progress tracking
        quiet=False
    )
    print("Download complete.")


def unzip_dataset():
    """Unzip the downloaded dataset."""
    zip_files = list(RAW_DIR.glob("*.zip"))
    if not zip_files:
        print("ERROR: No zip file found in data/raw/")
        print("Download may have failed — check your Kaggle credentials.")
        sys.exit(1)

    zip_path = zip_files[0]
    print(f"\nUnzipping: {zip_path.name}")

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(RAW_DIR)
    print("Unzip complete.")

    # Remove zip after extraction
    zip_path.unlink()
    print(f"Removed zip file: {zip_path.name}")


def verify_files():
    """Verify all expected CSV files are present and print row counts."""
    import pandas as pd

    print("\nVerifying downloaded files:")
    print("-" * 50)

    all_ok = True
    for filename in EXPECTED_FILES:
        filepath = RAW_DIR / filename
        if not filepath.exists():
            print(f"  MISSING  {filename}")
            all_ok = False
        else:
            df = pd.read_csv(filepath)
            print(f"  OK  {filename:<45} {len(df):>7,} rows  {len(df.columns)} cols")

    print("-" * 50)

    if all_ok:
        print("\nAll 8 CSV files downloaded successfully.")
        print("Next step: python scripts/setup_mysql.py")
    else:
        print("\nSome files are missing. Re-run this script.")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("  Olist Dataset Downloader")
    print("=" * 50)

    download_dataset()
    unzip_dataset()
    verify_files()
