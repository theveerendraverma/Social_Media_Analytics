"""Generate a deterministic, realistic synthetic social media export."""
from datetime import date, timedelta
from pathlib import Path
import csv, random

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "social_media_data.csv"
random.seed(42)
platforms = {"Instagram": 1.25, "YouTube": 1.5, "Facebook": .85, "X/Twitter": .7, "LinkedIn": 1.05}
types = ["Image", "Video", "Carousel", "Reel", "Text", "Short", "Live"]
positive = ["Great results from our community! #success", "We love this helpful update #growth", "Amazing ideas for a better future #inspiration"]
negative = ["A difficult lesson, but we can improve #learning", "Challenges remain in this changing world #update"]
neutral = ["Here is this week's update from our team #news", "Learn more about our latest work #business"]
hashtags = ["#analytics", "#marketing", "#community", "#business", "#technology", "#growth", "#news", "#learning"]
start = date(2025, 1, 1)
fields = ["post_id","date","platform","content_type","caption","hashtags","reach","impressions","likes","comments","shares","followers_start","new_followers","lost_followers","sentiment","posted_hour"]
rows = []
for i in range(2400):
    d = start + timedelta(days=random.randrange(455))
    p, mult = random.choice(list(platforms.items()))
    t = random.choice(types)
    sentiment = random.choices(["positive","neutral","negative"], [0.52,.36,.12])[0]
    caption = random.choice({"positive": positive, "negative": negative, "neutral": neutral}[sentiment])
    tags = random.sample(hashtags, random.randint(1, 3))
    reach = max(0, int(random.lognormvariate(8.1, .55) * mult * (1.2 if t in ("Video","Reel") else 1)))
    impressions = int(reach * random.uniform(1.15, 2.6))
    likes = int(reach * random.uniform(.025, .11) * mult)
    comments = int(likes * random.uniform(.04, .2))
    shares = int(likes * random.uniform(.03, .16))
    followers = int(10000 * mult + d.timetuple().tm_yday * 12 * mult)
    new = max(0, int((likes + comments) * random.uniform(.01, .06)))
    lost = max(0, int(new * random.uniform(.1, .45)))
    rows.append([f"post_{i+1:05d}", d.isoformat(), p, t, caption, " ".join(tags), reach, impressions, likes, comments, shares, followers, new, lost, sentiment, random.randrange(24)])
with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f); writer.writerow(fields); writer.writerows(rows)
print(f"Wrote {len(rows)} rows to {OUT}")
