FROM python:3.14
LABEL maintainer="Vizzart"

RUN apt-get update
RUN apt-get -y install gcc make cmake g++
RUN apt-get -y install libevent-dev
RUN apt-get install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools

RUN pip install wheel
RUN pip install gunicorn flask

WORKDIR /app
COPY app app
RUN mkdir -p logs

RUN pip install -r app/requirements.txt

CMD ["python3", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "16", "--max-requests", "0" , "--keep-alive", "60", "--timeout", "0", "--log-level", "info", "--error-logfile", "logs/gunicorn_error.log", "--access-logfile", "logs/gunicorn_access.log", "app.flasky:app"]

