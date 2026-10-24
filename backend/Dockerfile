FROM python:3.14
LABEL maintainer="Vizzart"

WORKDIR /backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .. /backend/

