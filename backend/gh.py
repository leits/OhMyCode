import asyncio
import pprint
from datetime import datetime

from constants import GITHUB_API_TOKEN
from httpx import AsyncClient
from loguru import logger

GH_URL = "https://api.github.com"


async def get_rate_limit(client: AsyncClient) -> int:
    resp = await client.get(f"{GH_URL}/rate_limit")
    rate_limit = resp.json()
    remaining = rate_limit["resources"]["core"]["remaining"]

    logger.info(f"Rate limit remaining: {remaining}")
    return remaining


async def get_repo_info(client: AsyncClient, owner: str, name: str) -> dict:
    resp = await client.get(f"{GH_URL}/repos/{owner}/{name}")
    repo = resp.json()

    logger.info(f"Got repo {owner}/{name} info")
    return repo


async def get_repo_downloads(client: AsyncClient, owner: str, name: str) -> dict:
    resp = await client.get(f"{GH_URL}/repos/{owner}/{name}/releases")
    releases = resp.json()

    downloads = 0
    for release in releases:
        for a in release["assets"]:
            downloads += a["download_count"]

    logger.info(f"Got repo {owner}/{name} downloads: {downloads}")
    return {"downloads": downloads}


async def get_repo_pulls(
    client: AsyncClient, owner: str, name: str, since: datetime
) -> dict:
    logger.info(f"Get repo {owner}/{name} issues")
    pulls = []
    check_next_page = True
    page = 1
    while check_next_page:
        params = {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100,
            "page": page,
        }
        resp = await client.get(f"{GH_URL}/repos/{owner}/{name}/pulls", params=params)
        responce = resp.json()
        if len(responce) == 0:
            break
        for pull in responce:
            if pull["updated_at"] > since.isoformat():
                pulls.append(pull)
            else:
                check_next_page = False
                break

    logger.info(f"Get repo {owner}/{name} issues")
    return {"pulls": pulls}


async def get_repo_issues(
    client: AsyncClient, owner: str, name: str, since: datetime
) -> dict:
    resp = await client.get(
        f"{GH_URL}/repos/{owner}/{name}/issues", params={"state": "all", "since": since}
    )
    issues = resp.json()

    data = {"issues": [i for i in issues if i.get("pull_request") is None]}
    logger.info(f"Get repo {owner}/{name} issues")
    return data


async def get_repo_top_referrers(client: AsyncClient, owner: str, name: str) -> dict:
    resp = await client.get(f"{GH_URL}/repos/{owner}/{name}/traffic/popular/referrers")
    logger.info(f"Get repo {owner}/{name} referrers")
    return {"referrers": resp.json()}


async def get_repo_traffic(client: AsyncClient, owner: str, name: str) -> dict:
    resp = await client.get(f"{GH_URL}/repos/{owner}/{name}/traffic/views")
    logger.info(f"Get repo {owner}/{name} traffic")
    return {"traffic": resp.json()}


async def collect_repo_stats(owner: str, name: str) -> dict:
    async with AsyncClient() as client:
        client.headers["Authorization"] = f"token {GITHUB_API_TOKEN}"

        repo = await get_repo_info(client, owner, name)
        downloads = await get_repo_downloads(client, owner, name)

    stats = {
        "stars": repo["stargazers_count"],
        "downloads": downloads["downloads"],
    }
    return stats


async def collect_repo_data(owner: str, name: str, since) -> dict:
    async with AsyncClient() as client:
        client.headers["Authorization"] = f"token {GITHUB_API_TOKEN}"
        await get_rate_limit(client)
        tasks = [
            get_repo_info(client, owner, name),
            get_repo_downloads(client, owner, name),
            get_repo_issues(client, owner, name, since),
            get_repo_pulls(client, owner, name, since),
            get_repo_top_referrers(client, owner, name),
            get_repo_traffic(client, owner, name),
        ]
        outputs = await asyncio.gather(*tasks)

    result = {}
    for output in outputs:
        result.update(output)

    data = {
        "since": since.isoformat(),
        "downloads": result["downloads"],
        "issues": result["issues"],
        "pulls": result["pulls"],
        "referrers": result["referrers"],
        "traffic": result["traffic"],
    }
    data["traffic"].update(
        {
            "yesterday": result["traffic"]["views"][-2],
            "two_days_ago": result["traffic"]["views"][-3],
        }
    )

    logger.info("Collected repo info")
    logger.info(pprint.pformat(data, indent=2))
    return data


async def get_user_info(token: str) -> dict:
    async with AsyncClient() as client:
        client.headers["Authorization"] = f"token {token}"
        resp = await client.get(f"{GH_URL}/user")
        return resp.json()
