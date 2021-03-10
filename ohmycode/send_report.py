#!/usr/bin/env python
# coding: utf-8
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import plotly.graph_objects as go
import requests
from requests.auth import HTTPBasicAuth
import jinja2
import sentry_sdk

from db import Repository, init_db_session
from gh import collect_github_data
from constants import (
    MAILGUN_API_KEY,
    MAILGUN_DOMAIN,
    SENTRY_DSN,
    MJML_APP_ID,
    MJML_SECRET_KEY,
    TEMPLATE_FILE,
    VIEWS_CHART_NAME,
    HEADER_CHART_NAME,
    TIME_MARK,
    ENV,
)

if ENV != "local":
    sentry_sdk.init(SENTRY_DSN, environment=ENV)



def plot_header(data: dict) -> bytes:
    fig = go.Figure()

    mode = "number+delta" if data["previous"] else "number"

    fig.add_trace(
        go.Indicator(
            title={"text": "Stars"},
            mode=mode,
            value=data["stars"],
            domain={"x": [0, 0.25], "y": [0, 1]},
            delta={"reference": data["previous"].get("start")},
        )
    )

    fig.add_trace(
        go.Indicator(
            title={"text": "Downloads"},
            mode=mode,
            value=data["downloads"],
            domain={"x": [0.25, 0.5], "y": [0, 1]},
            delta={"reference": data["previous"].get("downloads")},
        )
    )

    fig.add_trace(
        go.Indicator(
            title={"text": "Views"},
            mode="number+delta",
            value=data["traffic"]["yesterday"].count,
            domain={"x": [0.5, 0.75], "y": [0, 1]},
            delta={
                "reference": data["traffic"]["two_days_ago"].count,
                "relative": True,
            },
        )
    )

    fig.add_trace(
        go.Indicator(
            title={"text": "Uniques visitors"},
            mode="number+delta",
            value=data["traffic"]["yesterday"].uniques,
            domain={"x": [0.75, 1], "y": [0, 1]},
            delta={
                "reference": data["traffic"]["two_days_ago"].uniques,
                "relative": True,
            },
        )
    )

    fig.update_layout(width=1200, height=300)

    fig.update_layout(margin=dict(l=5, r=5, t=5, b=5))

    # fig.show()
    return fig.to_image(format="png")


def plot_views(views: list) -> bytes:
    x = []
    y1 = []
    y2 = []

    for day in views:
        x.append(day.timestamp)
        y1.append(day.count)
        y2.append(day.uniques)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y1, mode="lines+markers", name="count"))
    fig.add_trace(go.Scatter(x=x, y=y2, mode="lines+markers", name="uniques"))

    fig.update_layout(margin=dict(l=5, r=5, t=5, b=5))
    fig.update_layout(height=300)


    print("Rendered views chart")

    # fig.show()
    return fig.to_image(format="png")


def render_mjml(data: dict) -> str:
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)

    template = templateEnv.get_template(TEMPLATE_FILE)
    mjml = template.render(data=data, now=datetime.now())

    print("Rendered mjml")
    return mjml


def send_email(html: str, charts: dict):
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
    }
    Session = init_db_session()
    session = Session()
    Repository.add_today_stats(session, "leits", "MeetingBar", today_stats)
    stats = Repository.get_stats(session, "leits", "MeetingBar")

    data["previous"] = stats.get(TIME_MARK.strftime("%Y-%m-%d"), {})

    views_chart = plot_views(data["traffic"]["views"])
    header_chart = plot_header(data)

    data["views_image_src"] = f"cid:{VIEWS_CHART_NAME}"
    data["header_image_src"] = f"cid:{HEADER_CHART_NAME}"

    mjml = render_mjml(data)
    charts = {VIEWS_CHART_NAME: views_chart, HEADER_CHART_NAME: header_chart}

    resp = requests.post(
        "https://api.mjml.io/v1/render",
        json={"mjml": mjml},
        auth=HTTPBasicAuth(MJML_APP_ID, MJML_SECRET_KEY),
    )

    resp_json = resp.json()
    print(resp_json)
    html = resp_json["html"]

    send_email(html, charts)

if __name__ == "__main__":
    main()
