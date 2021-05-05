import argparse
import asyncio
from datetime import datetime

from db import Repository, init_db
from loguru import logger
from send_report import save_yesterday_stats, send_report


async def gather_stats():
    logger.info("Check repos to save stats")
    await init_db()
    repos = await Repository.filter().all()
    if not repos:
        logger.info("No repos to save stats")

    tasks = []
    for repo in repos:
        logger.info(f"Saving stats for {repo.id}")
        tasks.append(save_yesterday_stats(repo.id))

    await asyncio.gather(*tasks)


async def send_reports():
    logger.info("Check repos to send report")
    await init_db()
    repos = await Repository.filter(next_report_at__lt=datetime.now()).all()
    if not repos:
        logger.info("No repos to report")

    tasks = []
    for repo in repos:
        logger.info(f"Preparing report for {repo.id}")
        tasks.append(send_report(repo.id))

    await asyncio.gather(*tasks)


async def send_instant_report(repo_id):
    logger.info("Check repos to send report")
    if repo_id is None:
        logger.error("repo_id is required for send_instant_report command")
        return
    await init_db()
    await send_report(repo_id)


async def main():
    parser = argparse.ArgumentParser(description="OhMyCode CLI")
    parser.add_argument(
        "command", choices=["send_reports", "gather_stats", "send_instant_report"]
    )
    parser.add_argument("repo_id", nargs="?", default=None)
    args = parser.parse_args()
    if args.command == "send_reports":
        await send_reports()
    elif args.command == "gather_stats":
        await gather_stats()
    elif args.command == "send_instant_report":
        await send_instant_report(args.repo_id)


if __name__ == "__main__":
    asyncio.run(main())
