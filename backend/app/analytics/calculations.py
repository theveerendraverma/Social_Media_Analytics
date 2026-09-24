import pandas as pd


def safe_rate(numerator, denominator):
    return round(float(numerator) / float(denominator) * 100, 2) if denominator else 0.0

def add_metrics(df):
    df = df.copy()
    metric_columns = ["likes", "comments", "shares", "reach"]
    for column in metric_columns:
        if column not in df:
            df[column] = 0
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)
    df["engagement"] = df[["likes", "comments", "shares"]].sum(axis=1)
    denominator = df["reach"].where(df["reach"].ne(0), 1)
    df["engagement_rate"] = (df["engagement"] / denominator * 100).round(2)
    return df
