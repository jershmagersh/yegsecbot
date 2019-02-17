FROM python:latest

RUN pip install slackclient
WORKDIR /app/ 
ADD yegsecbot.py /app/
ADD config.json /app/
ADD yegsecbot.db /app/
