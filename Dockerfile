FROM python:latest
EXPOSE 5000

COPY . .

RUN pip3 install pipenv
RUN pipenv lock -r > requirements.txt
RUN pip3 install -r requirements.txt


CMD ["python3", "app.py" ]