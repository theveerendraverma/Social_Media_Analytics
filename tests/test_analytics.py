from backend.app.analytics.calculations import safe_rate

def test_safe_rate_handles_zero():
    assert safe_rate(10, 0) == 0.0
    assert safe_rate(25, 100) == 25.0
