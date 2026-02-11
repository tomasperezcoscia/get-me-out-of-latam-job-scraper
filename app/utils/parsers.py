"""Salary parsing, tag extraction, and HTML cleaning utilities."""

import re

from selectolax.parser import HTMLParser

# Common tech skills for tag extraction
KNOWN_SKILLS = {
    "python", "javascript", "typescript", "ruby", "go", "golang", "rust", "java",
    "c#", "c++", "php", "swift", "kotlin", "scala", "elixir", "clojure", "haskell",
    "smalltalk", "perl", "r", "sql", "nosql", "graphql",
    "react", "angular", "vue", "svelte", "next.js", "nextjs", "nuxt", "remix",
    "node.js", "nodejs", "express", "fastapi", "django", "flask",
    "ruby on rails", "rails", "spring", "laravel", ".net", "asp.net",
    "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform",
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "kafka", "rabbitmq", "celery",
    "git", "ci/cd", "jenkins", "github actions",
    "linux", "devops", "sre", "mlops",
    "machine learning", "deep learning", "ai", "llm", "nlp",
    "rest", "api", "microservices", "grpc",
    "agile", "scrum",
}

# Currency symbols and codes
CURRENCY_MAP = {
    "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY",
    "usd": "USD", "eur": "EUR", "gbp": "GBP", "cad": "CAD", "aud": "AUD",
}

# Salary multipliers
PERIOD_MULTIPLIERS = {
    "year": 1, "yr": 1, "annual": 1, "annually": 1, "pa": 1, "p.a.": 1,
    "month": 12, "mo": 12, "monthly": 12,
    "week": 52, "wk": 52, "weekly": 52,
    "hour": 2080, "hr": 2080, "hourly": 2080,
}


def clean_html(html: str) -> str:
    """Strip HTML tags and return clean text using selectolax."""
    if not html:
        return ""
    tree = HTMLParser(html)
    text = tree.text(separator="\n", strip=True)
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_salary(text: str | None) -> tuple[int | None, int | None, str]:
    """Parse salary information from text.

    Returns:
        Tuple of (min_salary, max_salary, currency) as annual USD equivalents.
        Returns (None, None, 'USD') if unparseable.
    """
    if not text:
        return None, None, "USD"

    text = text.lower().strip()

    # Detect currency
    currency = "USD"
    for symbol, code in CURRENCY_MAP.items():
        if symbol in text:
            currency = code
            break

    # Find numbers (handle formats like "50,000", "50k", "50.000")
    numbers = []
    for match in re.finditer(r"(\d[\d,\.]*)\s*k?", text):
        raw = match.group(1).replace(",", "")
        # Handle European decimal notation (50.000 = 50000)
        if "." in raw and len(raw.split(".")[-1]) == 3:
            raw = raw.replace(".", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        # Handle "k" suffix (50k = 50000)
        if match.group(0).rstrip().endswith("k"):
            val *= 1000
        numbers.append(int(val))

    if not numbers:
        return None, None, currency

    # Detect period and convert to annual
    multiplier = 1
    for period, mult in PERIOD_MULTIPLIERS.items():
        if period in text:
            multiplier = mult
            break

    numbers = [n * multiplier for n in numbers]

    # Filter out unreasonable values (likely not salaries)
    numbers = [n for n in numbers if 10000 <= n <= 1000000]

    if not numbers:
        return None, None, currency

    sal_min = min(numbers)
    sal_max = max(numbers) if len(numbers) > 1 else sal_min

    return sal_min, sal_max, currency


def extract_tags(text: str) -> list[str]:
    """Extract known tech skills/tags from text.

    Returns:
        Sorted list of unique matched skill tags.
    """
    if not text:
        return []

    text_lower = text.lower()
    found = set()

    for skill in KNOWN_SKILLS:
        # Use word boundary matching for short skills to avoid false positives
        if len(skill) <= 2:
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, text_lower):
                found.add(skill)
        elif skill in text_lower:
            found.add(skill)

    return sorted(found)
