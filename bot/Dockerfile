FROM python:3.8-alpine

RUN mkdir /app
WORKDIR /app

ADD requirements.txt /app/
RUN pip install -r requirements.txt

ADD . /app/

ENTRYPOINT ["python", "main.py"]