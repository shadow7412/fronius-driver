FROM python:3.11

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y firefox-esr && rm -rf /var/lib/apt/lists/*

COPY main.py .

ENTRYPOINT ["python", "main.py"]
