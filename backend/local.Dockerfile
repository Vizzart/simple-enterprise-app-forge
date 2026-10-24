FROM python:3.14

EXPOSE 5000

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .