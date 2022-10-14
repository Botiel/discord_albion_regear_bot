FROM python:latest
FROM gorialis/discord.py

RUN mkdir -p /app
WORKDIR /app

COPY ./regearbot_package ./regearbot_package
COPY main.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["python3", "-u", "./main.py"]