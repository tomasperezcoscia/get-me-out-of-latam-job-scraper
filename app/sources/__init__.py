"""Data source registry."""

from app.sources.arbeitnow import ArbeitnowSource
from app.sources.adzuna import AdzunaSource
from app.sources.himalayas import HimalayasSource
from app.sources.jooble import JoobleSource
from app.sources.remoteok import RemoteOKSource
from app.sources.remotive import RemotiveSource
from app.sources.serpapi_google import SerpAPIGoogleSource
from app.sources.weworkremotely import WeWorkRemotelySource

# Registry of all available sources
SOURCE_REGISTRY: dict[str, type] = {
    # Tier 1 — free, no key needed
    "remoteok": RemoteOKSource,
    "arbeitnow": ArbeitnowSource,
    "himalayas": HimalayasSource,
    "weworkremotely": WeWorkRemotelySource,
    "remotive": RemotiveSource,
    # Tier 2 — free/paid, key required (skip gracefully if not set)
    "jooble": JoobleSource,
    "adzuna": AdzunaSource,
    "serpapi_google": SerpAPIGoogleSource,
}


def get_source(name: str):
    """Get a source instance by name."""
    cls = SOURCE_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown source: {name!r}. Available: {list(SOURCE_REGISTRY.keys())}")
    return cls()


def get_all_sources():
    """Get instances of all registered sources."""
    return [cls() for cls in SOURCE_REGISTRY.values()]
