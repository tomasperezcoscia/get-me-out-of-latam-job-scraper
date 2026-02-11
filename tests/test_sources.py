"""Tests for data source normalization."""

from app.sources.remoteok import RemoteOKSource
from app.sources.arbeitnow import ArbeitnowSource
from app.sources.remotive import RemotiveSource
from app.utils.parsers import clean_html, extract_tags, parse_salary


def test_clean_html():
    """Test HTML cleaning."""
    result = clean_html("<p>Hello <b>World</b></p>")
    assert "Hello" in result and "World" in result
    assert clean_html("") == ""
    assert clean_html(None) == ""


def test_parse_salary_range():
    """Test salary parsing."""
    sal_min, sal_max, currency = parse_salary("$50,000 - $80,000")
    assert sal_min == 50000
    assert sal_max == 80000
    assert currency == "USD"


def test_parse_salary_euro():
    """Test Euro salary parsing."""
    sal_min, sal_max, currency = parse_salary("€60,000 - €90,000")
    assert sal_min == 60000
    assert sal_max == 90000
    assert currency == "EUR"


def test_parse_salary_k_notation():
    """Test k-notation salary parsing."""
    sal_min, sal_max, currency = parse_salary("50k - 80k USD")
    assert sal_min == 50000
    assert sal_max == 80000


def test_parse_salary_empty():
    """Test empty salary."""
    sal_min, sal_max, currency = parse_salary("")
    assert sal_min is None
    assert sal_max is None


def test_extract_tags():
    """Test tag extraction from text."""
    tags = extract_tags("We need a Python developer with React and PostgreSQL experience")
    assert "python" in tags
    assert "react" in tags
    assert "postgresql" in tags


def test_remoteok_normalize():
    """Test RemoteOK job normalization."""
    source = RemoteOKSource()
    result = source.normalize({
        "position": "Backend Engineer",
        "company": "TestCo",
        "description": "<p>Build APIs with Python</p>",
        "url": "/remote-jobs/backend-engineer",
        "tags": ["python", "api"],
    })

    assert result is not None
    assert result["title"] == "Backend Engineer"
    assert result["company"] == "TestCo"
    assert result["url"].startswith("https://remoteok.com")
    assert "python" in result["tags"]


def test_remoteok_normalize_skip_empty():
    """Test that empty jobs are skipped."""
    source = RemoteOKSource()
    assert source.normalize({}) is None
    assert source.normalize({"position": "", "company": "", "url": ""}) is None
