import pprint

from constants import GITHUB_API_TOKEN
from github import Github, Repository
from loguru import logger


def get_repo(owner, name):
    g = Github(GITHUB_API_TOKEN)

    rate_limit = g.get_rate_limit()
    logger.info(f"Rate limit: {rate_limit}")

    repo = g.get_repo(f"{owner}/{name}")
    logger.info("Connected to repo")
    return repo


def get_repo_downloads(repo: Repository) -> int:
    downloads = 0
    for release in repo.get_releases():
        for a in release.get_assets():
            downloads += a.download_count
    return downloads


def collect_github_data(since, owner, name) -> dict:
    repo = get_repo(owner, name)

    data = {
        "since": since,
        "downloads": 0,
        "issues": [],
        "pulls": [],
    }

    for issue in repo.get_issues(since=since, state="all"):
        if issue.pull_request:
            data["pulls"].append(issue)
        else:
            data["issues"].append(issue)

    data["referrers"] = repo.get_top_referrers()

    data["traffic"] = repo.get_views_traffic(per="day")
    data["traffic"]["yesterday"] = data["traffic"]["views"][-2]
    data["traffic"]["two_days_ago"] = data["traffic"]["views"][-3]

    logger.info("Collected repo info")
    logger.info(pprint.pformat(data, indent=2))
    return data
