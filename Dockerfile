FROM python:latest
EXPOSE 5000

RUN pip3 install pipenv

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv lock -r > requirements.txt
RUN pip3 install -r requirements.txt

RUN rm requirements.txt
RUN rm Pipfile
RUN rm Pipfile.lock

COPY . /app

CMD ["uvicorn", "app:app", "--app-dir backend", "--reload", "--reload-dir backend" ]