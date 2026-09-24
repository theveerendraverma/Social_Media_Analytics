"""Small, framework-independent service functions used by API consumers."""
from .calculations import safe_rate

def engagement_summary(df):
    """Return the common engagement KPIs for an already filtered dataframe."""
    if df.empty:
        return {"posts": 0, "reach": 0, "engagement": 0, "engagement_rate": 0.0}
    total = int(df["engagement"].sum())
    reach = int(df["reach"].sum())
    return {
        "posts": len(df),
        "reach": reach,
        "engagement": total,
        "engagement_rate": safe_rate(total, reach),
    }
