import pandas as pd
from pathlib import Path

# CSVを読み込んでParquetとして保存
df = pd.read_csv(r"M:\DB\hitaiou\data\dashboard\dummy.csv")
df.to_parquet(r"M:\DB\hitaiou\data\dashboard\dummy.parquet", engine='pyarrow')