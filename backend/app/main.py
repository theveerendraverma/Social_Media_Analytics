from datetime import date
from typing import Optional
import re
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import SocialMediaPost
from .analytics.calculations import add_metrics, safe_rate

app = FastAPI(title="Social Media Analytics API", version="1.0.0")
PLATFORMS = {"Instagram", "YouTube", "Facebook", "X/Twitter", "LinkedIn"}
CONTENT_TYPES = {"Image", "Video", "Carousel", "Reel", "Text", "Short", "Live"}

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)

def frame(db: Session, platform: Optional[str], start_date: Optional[date],
          end_date: Optional[date], content_type: Optional[str]):
    if platform and platform not in PLATFORMS:
        raise HTTPException(422, f"Unknown platform. Choose from {sorted(PLATFORMS)}")
    if content_type and content_type not in CONTENT_TYPES:
        raise HTTPException(422, f"Unknown content_type. Choose from {sorted(CONTENT_TYPES)}")
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, "start_date must be on or before end_date")
    q = select(SocialMediaPost)
    if platform: q = q.where(SocialMediaPost.platform == platform)
    if content_type: q = q.where(SocialMediaPost.content_type == content_type)
    if start_date: q = q.where(SocialMediaPost.date >= start_date)
    if end_date: q = q.where(SocialMediaPost.date <= end_date)
    rows = db.execute(q).scalars().all()
    columns = ["post_id", "date", "platform", "content_type", "reach", "impressions", "likes", "comments", "shares", "followers_start", "new_followers", "lost_followers", "sentiment", "posted_hour", "caption", "hashtags"]
    if not rows: return add_metrics(pd.DataFrame(columns=columns))
    return add_metrics(pd.DataFrame([{c: getattr(r, c) for c in columns} for r in rows]))

def clean(v):
    if hasattr(v, "item"): v = v.item()
    if hasattr(v, "isoformat"): return v.isoformat()
    return v
def records(df):
    return [{k: clean(v) for k, v in row.items()} for row in df.to_dict("records")]

FilterPlatform = Query(None)
def filters(platform: Optional[str] = Query(None), start_date: Optional[date] = Query(None),
            end_date: Optional[date] = Query(None), content_type: Optional[str] = Query(None)):
    return platform, start_date, end_date, content_type

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    return {"status": "ok", "records": db.scalar(select(func.count()).select_from(SocialMediaPost))}

@app.get("/api/overview")
def overview(f=Depends(filters), db: Session = Depends(get_db)):
    d = frame(db, *f)
    if d.empty: return {"records": 0, "metrics": {}, "message": "No data for selected filters"}
    latest_followers = d.sort_values("date").groupby("platform", as_index=False).tail(1).followers_start.sum()
    best_post = d.sort_values(["engagement_rate", "reach"], ascending=False).iloc[0]
    return {"records": len(d), "metrics": {
        "posts": len(d), "followers": int(latest_followers), "likes": int(d.likes.sum()),
        "comments": int(d.comments.sum()), "shares": int(d.shares.sum()),
        "reach": int(d.reach.sum()), "impressions": int(d.impressions.sum()),
        "engagement": int(d.engagement.sum()), "engagement_rate": safe_rate(d.engagement.sum(), d.reach.sum()),
        "new_followers": int(d.new_followers.sum()), "lost_followers": int(d.lost_followers.sum()),
        "net_follower_growth": int((d.new_followers-d.lost_followers).sum())
    }, "best_platform": str(d.groupby("platform").engagement.sum().idxmax()),
    "best_content_type": str(d.groupby("content_type").engagement_rate.mean().idxmax()),
    "best_post": {"post_id": str(best_post.post_id), "engagement_rate": float(best_post.engagement_rate)}}

@app.get("/api/platforms")
def platforms(f=Depends(filters), db: Session = Depends(get_db)):
    d = frame(db, *f)
    if d.empty: return {"data": []}
    g = d.groupby("platform", as_index=False).agg(posts=("platform","size"), reach=("reach","sum"), impressions=("impressions","sum"), engagement=("engagement","sum"), engagement_rate=("engagement_rate","mean"), followers=("new_followers","sum"))
    return {"data": records(g.sort_values("engagement", ascending=False))}

@app.get("/api/engagement")
def engagement(f=Depends(filters), db: Session = Depends(get_db)):
    d = frame(db, *f)
    if d.empty: return {"summary": {}, "timeseries": []}
    d["period"] = pd.to_datetime(d.date).dt.to_period("M").astype(str)
    g = d.groupby("period", as_index=False).agg(reach=("reach","sum"), engagement=("engagement","sum"), engagement_rate=("engagement_rate","mean"))
    return {"summary": {"total_engagement": int(d.engagement.sum()), "average_rate": round(float(d.engagement_rate.mean()),2)}, "timeseries": records(g)}

@app.get("/api/content-performance")
def content_performance(f=Depends(filters), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    d = frame(db, *f)
    cols = ["date","platform","content_type","caption","hashtags","reach","impressions","likes","comments","shares","engagement","engagement_rate"]
    return {"data": records(d.sort_values(["engagement_rate","reach"], ascending=False)[cols].head(limit))}

@app.get("/api/top-posts")
def top_posts(f=Depends(filters), limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    return content_performance(f, limit, db)

@app.get("/api/follower-growth")
def follower_growth(f=Depends(filters), db: Session = Depends(get_db)):
    d = frame(db, *f)
    if d.empty: return {"data": [], "daily": [], "weekly": [], "monthly": []}
    dates = pd.to_datetime(d.date)
    d["followers"] = d["followers_start"] + d["new_followers"] - d["lost_followers"]
    def rollup(period):
        x = d.assign(period=getattr(dates.dt, "to_period")(period).astype(str))
        g = x.groupby(["period", "platform"], as_index=False).agg(
            followers=("followers", "last"), new_followers=("new_followers", "sum"),
            lost_followers=("lost_followers", "sum"))
        g["net_growth"] = g.new_followers - g.lost_followers
        return records(g)
    daily, weekly, monthly = rollup("D"), rollup("W"), rollup("M")
    return {"data": monthly, "daily": daily, "weekly": weekly, "monthly": monthly}

@app.get("/api/posting-analysis")
def posting_analysis(f=Depends(filters), db: Session = Depends(get_db)):
    d = frame(db, *f)
    if d.empty: return {"summary": {}, "weekday": [], "hour": [], "content_type": [], "heatmap": []}
    d["weekday"] = pd.to_datetime(d.date).dt.day_name()
    agg = lambda col: records(d.groupby(col, as_index=False).agg(posts=(col,"size"), engagement_rate=("engagement_rate","mean")).sort_values("posts", ascending=False))
    return {"summary": {"posts": len(d), "posts_per_week": round(len(d)/max(1, (pd.to_datetime(d.date).max()-pd.to_datetime(d.date).min()).days/7),2)}, "weekday": agg("weekday"), "hour": agg("posted_hour"), "content_type": agg("content_type"), "heatmap": records(d.groupby(["weekday","posted_hour"], as_index=False).size())}

@app.get("/api/sentiment")
def sentiment(f=Depends(filters), db: Session = Depends(get_db)):
    d = frame(db, *f)
    if d.empty: return {"data": [], "by_platform": [], "over_time": []}
    g = d.groupby("sentiment", as_index=False).agg(posts=("sentiment","size"), engagement_rate=("engagement_rate","mean"))
    by_platform = d.groupby(["platform", "sentiment"], as_index=False).agg(posts=("sentiment","size"), engagement_rate=("engagement_rate","mean"))
    over_time = d.assign(period=pd.to_datetime(d.date).dt.to_period("M").astype(str)).groupby(
        ["period", "sentiment"], as_index=False).agg(posts=("sentiment","size"), engagement_rate=("engagement_rate","mean"))
    return {"data": records(g), "by_platform": records(by_platform), "over_time": records(over_time)}

@app.get("/api/hashtags")
def hashtags(f=Depends(filters), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    d = frame(db, *f)
    if d.empty: return {"data": []}
    x = d.assign(hashtag=d.hashtags.str.lower().str.findall(r"#\w+")).explode("hashtag")
    g = x.groupby("hashtag", as_index=False).agg(posts=("hashtag","size"), engagement=("engagement","sum"), engagement_rate=("engagement_rate","mean"))
    by_platform = x.groupby(["platform", "hashtag"], as_index=False).agg(posts=("hashtag","size"), engagement_rate=("engagement_rate","mean"))
    return {"data": records(g.sort_values("posts", ascending=False).head(limit)),
            "by_platform": records(by_platform.sort_values("posts", ascending=False).head(limit * 5))}

@app.get("/api/insights")
def insights(f=Depends(filters), db: Session = Depends(get_db)):
    d = frame(db, *f)
    if d.empty: return {"insights": []}
    best = d.groupby("platform").engagement_rate.mean().idxmax()
    ctype = d.groupby("content_type").engagement_rate.mean().idxmax()
    weekday = d.assign(weekday=pd.to_datetime(d.date).dt.day_name()).groupby("weekday").engagement_rate.mean().idxmax()
    reach_post = d.loc[d.reach.idxmax()]
    growth = int((d.new_followers - d.lost_followers).sum())
    direction = "increasing" if growth >= 0 else "decreasing"
    return {"insights": [
        f"{best} has the highest average engagement rate ({d[d.platform == best].engagement_rate.mean():.2f}%).",
        f"{ctype} is the strongest content type by average engagement rate.",
        f"{weekday} has the highest average engagement rate in the selected period.",
        f"Post {reach_post.post_id} generated the highest reach ({int(reach_post.reach):,}).",
        f"Follower growth is {direction} with a net change of {growth:,}.",
        f"The selected period contains {len(d):,} posts and {int(d.engagement.sum()):,} total interactions."
    ]}
