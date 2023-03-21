FROM python:3.9.7

LABEL maintainer="https://github.com/larryfenn/breath-server/"

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD waitress-serve --port=80 --threads=32 --call app:create_app
