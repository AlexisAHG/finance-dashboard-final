from pathlib import Path
import pandas as pd

CACHE_DIR = Path("reports/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _path(key: str) -> Path:
    return CACHE_DIR / f"{key}.parquet"

def load_cache(key: str) -> pd.DataFrame | None:
    path = _path(key)
    if path.exists():
        return pd.read_parquet(path)
    return None

def save_cache(key: str, df: pd.DataFrame) -> None:
    df.to_parquet(_path(key))

