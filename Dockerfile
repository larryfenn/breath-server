FROM python:3.9.7

LABEL maintainer="https://github.com/larryfenn/breath-server/"

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD uwsgi --http 0.0.0.0:80 --master -p 8 --file app.py --callable app --disable-logging --log-4xx --log-5xx
