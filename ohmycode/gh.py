from github import Github

from constants import GITHUB_API_TOKEN

def collect_github_data(since) -> dict:
    g = Github(GITHUB_API_TOKEN)

    rate_limit = g.get_rate_limit()
    print(f"Rate limit: {rate_limit}")

    repo = g.get_repo("leits/MeetingBar")

    print("Connected to repo")

    data = {
        "since": since,
        "stars": repo.stargazers_count,
        "downloads": 0,
        "issues": [],
        "pulls": [],
    }

    for issue in repo.get_issues(since=since, state="all"):
        if issue.pull_request:
            data["pulls"].append(issue)
        else:
            data["issues"].append(issue)

    for release in repo.get_releases():
        for a in release.get_assets():
            data["downloads"] += a.download_count

    data["referrers"] = repo.get_top_referrers()

    data["traffic"] = repo.get_views_traffic(per="day")
    data["traffic"]["yesterday"] = data["traffic"]["views"][-2]
    data["traffic"]["two_days_ago"] = data["traffic"]["views"][-3]

    print("Collected repo info")
    return data
