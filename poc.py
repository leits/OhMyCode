#!/usr/bin/env python
# coding: utf-8
import io
import os
from datetime import datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas
import requests
import jinja2
import matplotlib.pyplot as plt

from github import Github

from dotenv import load_dotenv

load_dotenv()

from db import Repository, init_db_session


GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")

TEMPLATE_FILE = "letter.j2"
CHART_NAME = "views_chart"

TIME_MARK = datetime.now() - timedelta(days=1)


def collect_github_data(since: timedelta) -> dict:
    g = Github(GITHUB_API_TOKEN)
    repo = g.get_repo("leits/MeetingBar")

    print("Connected to repo")

    data = {
        "since": since,
        "stars": repo.stargazers_count,
        "open_issues": repo.open_issues_count,
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

    print("Collected repo info")

    rate_limit = g.get_rate_limit()
    print(f"Rate limit: {rate_limit}")

    return data


def plot_views(views) -> bytes:
    df = pandas.DataFrame(columns=["timestamp", "count", "uniques"])

    for i, day in enumerate(views):
        df.loc[i] = [day.timestamp, day.count, day.uniques]

    df.plot(x="timestamp", y=["count", "uniques"], style=".-")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    chart = buf.read()
    buf.close()

    print("Rendered views chart")

    return chart


def render_html(data: dict) -> str:
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)

    template = templateEnv.get_template(TEMPLATE_FILE)
    html = template.render(data=data)

    print("Rendered html")

    return html


def send_email(html, chart):
    now = datetime.now()
    html_part = MIMEMultipart(_subtype="related")
    html_part["Subject"] = f"Daily update of MeetingBar ({now.strftime('%d %b %Y')})"
    html_part["From"] = "leits.dev@gmail.com"
    html_part["To"] = "leits.dev@gmail.com"

    body = MIMEText(html, _subtype="html")

    html_part.attach(body)
    img = MIMEImage(chart, "png")
    img.add_header("Content-Id", f"<{CHART_NAME}>")
    img.add_header("Content-Disposition", "inline", filename=CHART_NAME)

    html_part.attach(img)

    res = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages.mime",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": html_part["From"],
            "to": html_part["To"],
            "subject": html_part["Subject"],
        },
        files={"message": html_part.as_string()},
    )
    print("Sent email")
    print(res.text)


def main():
    data = collect_github_data(TIME_MARK)

    today_stats = {
        "stars": data["stars"],
        "downloads": data["downloads"],
        "open_issues": data["open_issues"],
    }
    session = init_db_session()
    Repository.add_today_stats(session, "leits", "MeetingBar", today_stats)
    stats = Repository.get_stats(session, "leits", "MeetingBar")

    data["previous"] = stats.get(TIME_MARK.strftime("%Y-%m-%d"))

    chart = plot_views(data["traffic"]["views"])

    data["views_image_src"] = f"cid:{CHART_NAME}"
    html = render_html(data)

    send_email(html, chart)


if __name__ == "__main__":
    main()
