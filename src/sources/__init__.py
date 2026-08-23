from . import arxiv, github_releases, hackernews, npm, rss

REGISTRY = {
    "github_releases": github_releases.fetch,
    "npm": npm.fetch,
    "rss": rss.fetch,
    "hackernews": hackernews.fetch,
    "arxiv": arxiv.fetch,
}

__all__ = ["REGISTRY"]
