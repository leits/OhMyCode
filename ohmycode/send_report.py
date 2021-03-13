#!/usr/bin/env python
# coding: utf-8
import asyncio
from datetime import datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
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
from gh import collect_github_data
from plots import plot_header, plot_views

if ENV != "local":
    sentry_sdk.init(SENTRY_DSN, environment=ENV)


def render_mjml(data: dict) -> str:
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)

    template = templateEnv.get_template(TEMPLATE_FILE)
    mjml = template.render(data=data, now=datetime.now())

    print("Rendered mjml")
    return mjml


async def send_email(html: str, charts: dict):
    html_part = MIMEMultipart(_subtype="related")
    html_part["Subject"] = f"Daily updates of MeetingBar"
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
        print("Sent email")
        print(resp.text)


async def send_report(repo_id):
    repo = await Repository.get(id=repo_id)

    now = datetime.now()
    since = now - timedelta(days=1)

    data = collect_github_data(since, repo.owner, repo.name)

    today_stats = {
        "stars": data["stars"],
        "downloads": data["downloads"],
    }
    repo.stats.update(today_stats)
    repo.next_report_at += timedelta(days=1)
    repo.reported_at = now
    await repo.save()

    data["previous"] = repo.stats.get(since.strftime("%Y-%m-%d"), {})

    views_chart = plot_views(data["traffic"]["views"])
    header_chart = plot_header(data)

    data["views_image_src"] = f"cid:{VIEWS_CHART_NAME}"
    data["header_image_src"] = f"cid:{HEADER_CHART_NAME}"

    mjml = render_mjml(data)
    charts = {VIEWS_CHART_NAME: views_chart, HEADER_CHART_NAME: header_chart}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.mjml.io/v1/render",
            json={"mjml": mjml},
            auth=(MJML_APP_ID, MJML_SECRET_KEY),
        )
        resp_json = resp.json()
        print(resp_json)
        html = resp_json["html"]

    await send_email(html, charts)


async def main():
    await init_db()
    repos = await Repository.filter(next_report_at__lt=datetime.now()).all()
    if not repos:
        print("No repos to update")

    tasks = []
    for repo in repos:
        tasks.append(send_report(repo.id))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
