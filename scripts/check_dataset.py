import sys
from pathlib import Path
import pandas as pd


if len(sys.argv) < 2:
    raise SystemExit("Usage: python scripts/check_dataset.py path/to/weather.csv")

path = Path(sys.argv[1])
if not path.exists():
    raise SystemExit(f"File not found: {path}")

df = pd.read_csv(path)
print(f"Rows: {len(df):,}")
print(f"Columns ({len(df.columns)}):")
for column in df.columns:
    missing = int(df[column].isna().sum())
    print(f"- {column}: dtype={df[column].dtype}, missing={missing:,}")
print("\nFirst 5 rows:")
print(df.head().to_string(index=False))
