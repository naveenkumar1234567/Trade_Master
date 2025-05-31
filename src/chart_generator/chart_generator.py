# src/chart_generator/chart_generator.py

import mplfinance as mpf
import pandas as pd
import os

def save_candlestick_chart(df: pd.DataFrame, symbol: str, output_dir: str = "charts"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df = df.copy()
    df.index = pd.to_datetime(df['date'])
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    file_path = os.path.join(output_dir, f"{symbol}.png")
    mpf.plot(df, type='candle', style='charles', savefig=file_path)
    return file_path
