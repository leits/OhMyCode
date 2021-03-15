import os

ENV = os.getenv("ENV", "local")

if ENV == "local":
    from dotenv import load_dotenv

    load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
SENTRY_DSN = os.getenv("SENTRY_DSN")
MJML_APP_ID = os.getenv("MJML_APP_ID")
MJML_SECRET_KEY = os.getenv("MJML_SECRET_KEY")
PORT = os.environ.get("PORT", 5000)

TEMPLATE_FILE = "./ohmycode/letter.mjml.j2"
VIEWS_CHART_NAME = "views_chart"
HEADER_CHART_NAME = "header_chart"
