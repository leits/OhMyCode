#!/usr/bin/env python
# coding: utf-8
import asyncio
from datetime import datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
from aiofile import async_open
import jinja2
import sentry_sdk
from constants import (
    ENV,
    HEADER_CHART_NAME,
    MAILGUN_API_KEY,
    MAILGUN_DOMAIN,
    MJML_APP_ID,
    MJML_SECRET_KEY,
    SENTRY_DSN,
    TEMPLATE_FILE,
    VIEWS_CHART_NAME,
)
from db import Repository, init_db
from gh import collect_repo_data, collect_repo_stats
from loguru import logger
from plots import plot_header, plot_views

if ENV != "local":
    sentry_sdk.init(SENTRY_DSN, environment=ENV)


async def render_mjml(data: dict) -> str:
    async with async_open(TEMPLATE_FILE, 'r') as afp:
        template_str = await afp.read()

    template = jinja2.Template(template_str)
    mjml = template.render(data=data, now=datetime.now())

    logger.info("Rendered mjml")
    return mjml


async def send_email(html: str, name: str, charts: dict):
    html_part = MIMEMultipart(_subtype="related")
    html_part["Subject"] = f"Daily updates of {name}"
    html_part["From"] = "leits.dev@gmail.com"
    html_part["To"] = "leits.dev@gmail.com"

    body = MIMEText(html, _subtype="html")

    html_part.attach(body)
    for name, chart in charts.items():
        img = MIMEImage(chart, "png")
        img.add_header("Content-Id", f"<{name}>")
        img.add_header("Content-Disposition", "inline", filename=name)
        html_part.attach(img)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages.mime",
            data={
                "from": html_part["From"],
                "to": html_part["To"],
                "subject": html_part["Subject"],
            },
            files={"message": html_part.as_string()},
            auth=("api", MAILGUN_API_KEY),
        )
        logger.info("Sent email")
        logger.info(resp.text)


async def save_yesterday_stats(repo_id):
    logger.info(f"Saving yesterdays stats for {repo_id}")
    repo = await Repository.get(id=repo_id)

    yesterday_stats = await collect_repo_stats(repo.owner, repo.name)

    yesterday = datetime.now() - timedelta(days=1)
    repo.stats[yesterday.strftime("%Y-%m-%d")] = yesterday_stats
    logger.info(f"Saved yesterdays stats for {repo_id}: {yesterday_stats}")
    await repo.save()


async def send_report(repo_id):
    repo = await Repository.get(id=repo_id)

    today = datetime.now().replace(hour=0, minute=0)
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    data = await collect_repo_data(repo.owner, repo.name, yesterday)
    data["yesterday"] = repo.stats[yesterday.strftime("%Y-%m-%d")]
    data["two_days_ago"] = repo.stats.get(two_days_ago.strftime("%Y-%m-%d"), {})
    logger.info(f"Got yesterdays stats for {repo_id}: {data['yesterday']}")

    views_chart = plot_views(data["traffic"]["views"])
    header_chart = plot_header(data)

    data["views_image_src"] = f"cid:{VIEWS_CHART_NAME}"
    data["header_image_src"] = f"cid:{HEADER_CHART_NAME}"

    mjml = await render_mjml(data)
    charts = {VIEWS_CHART_NAME: views_chart, HEADER_CHART_NAME: header_chart}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.mjml.io/v1/render",
            json={"mjml": mjml},
            auth=(MJML_APP_ID, MJML_SECRET_KEY),
        )
        resp_json = resp.json()
        html = resp_json["html"]

    await send_email(html, repo.name, charts)

    repo.next_report_at += timedelta(days=1)
    repo.reported_at = datetime.now()
    await repo.save()


async def main():
    await init_db()
    repos = await Repository.all()
    if not repos:
        logger.info("No repos to update")

    for repo in repos:
        await save_yesterday_stats(repo.id)
        await send_report(repo.id)


if __name__ == "__main__":
    asyncio.run(main())
