#!/usr/bin/env python
# coding: utf-8

# In[]:
import io
import os
from datetime import datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas
import requests
import matplotlib.pyplot as plt

from jinja2 import Template
from github import Github

# In[]:
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")

# In[]:
data = {}

now = datetime.now()
time_mark = now - timedelta(days=1)
data['time_mark'] = time_mark

g = Github(GITHUB_API_TOKEN)

repo = g.get_repo("leits/MeetingBar")

print("Connected to repo")

data['stars'] = repo.stargazers_count
data['open_issues'] = repo.open_issues_count
data['forks'] = repo.forks_count

data['issues'] = []
data['pulls'] = []

for issue in repo.get_issues(since=time_mark, state="all"):
    if issue.pull_request:
        data['pulls'].append(issue)
    else:
        data['issues'].append(issue)

releases = repo.get_releases()

downloads = 0
for release in releases:
    for a in release.get_assets():
        downloads += a.download_count

data['downloads'] = downloads

data['referrers'] = repo.get_top_referrers()

data['traffic'] = repo.get_views_traffic(per="day")

print("Collected repo info")

# g.get_rate_limit()

# In[]:

df = pandas.DataFrame(columns=['timestamp', 'count', 'uniques'])

for i, day in enumerate(data['traffic']['views']):
    df.loc[i] = [day.timestamp, day.count, day.uniques]

df.plot(x='timestamp', y=['count', 'uniques'], style='.-')

buf = io.BytesIO()
plt.savefig(buf, format='png', bbox_inches = 'tight')
buf.seek(0)
chart = buf.read()
buf.close()

data["views_image_src"] = "cid:views_chart"

print("Rendered views chart")

# In[]:
template = '''
<p>
⭐ Stars: {{ data.stars }}<br />
💬 Open Issues: {{ data.open_issues }}<br />
👀 Views (2 weeks): {{ data.traffic.count }} ({{ data.traffic.uniques }} uniques)<br />
📥 Downloads: {{ data.downloads }}<br />
</p>

<h3>💬 Issues</h3>
<p>
{% for issue in data.issues %}
    {{ "🟢" if issue.state == "open" else "🔴" }}
    <a href="{{ issue.html_url }}">#{{ issue.number }}</a> {{ issue.title }}
    {{ "🆕" if issue.created_at < data.time_mark else "" }}
    <br />
{% else %}
No updates
{% endfor %}
</p>

<h3>✏️ Pull Requests</h3>
<p>
{% for pull in data.pulls %}
    {{ "🟢" if pull.state == "open" else "🔴" }}
    <a href="{{ pull.html_url }}">#{{ pull.number }}</a> {{ pull.title }}
    {{ "🆕" if pull.created_at < data.time_mark else "" }}
    <br />
{% else %}
No updates
{% endfor %}
</p>

<h3>🔗 Referrers</h3>
<p>
{% for ref in data.referrers %}
    {{ ref.count }} ({{ ref.uniques }}) - {{ ref.referrer }} <br />
{% endfor %}
</p>

<h3>👀 Views</h3>
<p><img src="{{ data.views_image_src }}" alt="views" /></p>
'''

tm = Template(template)
html = tm.render(data=data)

print("Rendered html")

# from IPython.core.display import display, HTML
# display(HTML(html))

# In[]:

html_part = MIMEMultipart(_subtype='related')
html_part['Subject'] = f"Daily update of MeetingBar ({now.strftime('%d %b %Y')})"
html_part['From'] = "leits.dev@gmail.com"
html_part['To'] = "leits.dev@gmail.com"

body = MIMEText(html, _subtype='html')

html_part.attach(body)
img = MIMEImage(chart, 'png')
img.add_header('Content-Id', '<views_chart>')
img.add_header("Content-Disposition", "inline", filename="views_chart")

html_part.attach(img)

res = requests.post(
    f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages.mime",
    auth=("api", MAILGUN_API_KEY),
    data={"from": "leits <leits.dev@gmail.com>", "to": "leits.dev@gmail.com", "subject": "Hello"},
    files={"message": html_part.as_string()}
)

print("Sent email")
print(res.text)