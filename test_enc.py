import pandas as pd

path = r"C:\LCT\LCT-Pyatnashka-MISISxMIPT\ml\data\samples\csv_example.csv"  # укажи путь к твоему файлу, если он не рядом, то полный путь

encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'utf-16', 'utf-16le', 'utf-16be']

for enc in encodings:
    try:
        df = pd.read_csv(path, encoding=enc, sep=None, engine='python')
        print(f"{enc} -> shape={df.shape}, columns={df.columns[:5].tolist()}")
    except Exception as e:
        print(f"{enc} -> fail: {e}")
