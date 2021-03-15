import plotly.graph_objects as go
from loguru import logger


def plot_header(data: dict) -> bytes:
    fig = go.Figure()

    mode = "number+delta" if data["two_days_ago"] else "number"

    fig.add_trace(
        go.Indicator(
            title={"text": "Stars"},
            mode=mode,
            value=data["yesterday"]["stars"],
            domain={"x": [0, 0.25], "y": [0, 1]},
            delta={"reference": data["two_days_ago"].get("stars")},
        )
    )

    fig.add_trace(
        go.Indicator(
            title={"text": "Downloads"},
            mode=mode,
            value=data["yesterday"]["downloads"],
            domain={"x": [0.25, 0.5], "y": [0, 1]},
            delta={"reference": data["two_days_ago"].get("downloads")},
        )
    )

    fig.add_trace(
        go.Indicator(
            title={"text": "Views"},
            mode="number+delta",
            value=data["traffic"]["yesterday"]["count"],
            domain={"x": [0.5, 0.75], "y": [0, 1]},
            delta={
                "reference": data["traffic"]["two_days_ago"]["count"],
                "relative": True,
            },
        )
    )

    fig.add_trace(
        go.Indicator(
            title={"text": "Uniques visitors"},
            mode="number+delta",
            value=data["traffic"]["yesterday"]["uniques"],
            domain={"x": [0.75, 1], "y": [0, 1]},
            delta={
                "reference": data["traffic"]["two_days_ago"]["uniques"],
                "relative": True,
            },
        )
    )

    fig.update_layout(width=1200, height=300)

    fig.update_layout(margin=dict(l=5, r=5, t=5, b=5))

    logger.info("Rendered header chart")
    # fig.show()
    return fig.to_image(format="png")


def plot_views(views: list) -> bytes:
    x = []
    y1 = []
    y2 = []

    for day in views:
        x.append(day["timestamp"])
        y1.append(day["count"])
        y2.append(day["uniques"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y1, mode="lines+markers", name="count"))
    fig.add_trace(go.Scatter(x=x, y=y2, mode="lines+markers", name="uniques"))

    fig.update_layout(margin=dict(l=5, r=5, t=5, b=5))
    fig.update_layout(height=300)

    logger.info("Rendered views chart")
    # fig.show()
    return fig.to_image(format="png")
