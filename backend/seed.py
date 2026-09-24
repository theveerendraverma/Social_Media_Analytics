"""Create the SQLite database and import the generated CSV."""
from pathlib import Path
import sys
import pandas as pd
from sqlalchemy import delete
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import Base, SessionLocal, engine
from app.models import SocialMediaPost

def seed():
    csv_path = Path(__file__).resolve().parents[1] / "data" / "social_media_data.csv"
    if not csv_path.exists():
        exec(compile((csv_path.parent / "generate_data.py").read_text(), "generate_data.py", "exec"))
    Base.metadata.create_all(engine)
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df["date"] = df["date"].dt.date
    numeric = ["reach", "impressions", "likes", "comments", "shares",
               "followers_start", "new_followers", "lost_followers", "posted_hour"]
    for column in numeric:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).clip(lower=0)
    df["posted_hour"] = df["posted_hour"].clip(0, 23).astype(int)
    df["caption"] = df["caption"].fillna("")
    df["hashtags"] = df["hashtags"].fillna("")
    df["sentiment"] = df["sentiment"].fillna("neutral").str.lower()
    df = df.drop_duplicates(subset=["post_id"]).reset_index(drop=True)
    with SessionLocal() as db:
        db.execute(delete(SocialMediaPost))
        db.bulk_insert_mappings(SocialMediaPost, df.to_dict("records"))
        db.commit()
    return len(df)

if __name__ == "__main__":
    print(f"Seeded {seed()} records")
