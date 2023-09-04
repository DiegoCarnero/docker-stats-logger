FROM python:slim-bullseye

RUN pip3 install docker pyyaml
COPY app/ /usr/src/app

WORKDIR /usr/src/app

ENV LOGGING_DIRECTORY=stats_logs
ENV LOGGING_INTERVAL=1
ENV LOGGING_MODE=full
ENV DOCKER_PROJECT=
ENV LOGGING_ONE_SHOT=true

CMD [ "python", "/usr/src/app/main.py", "-e"]
