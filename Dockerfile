FROM python:3.11.4-alpine3.18
LABEL maintainer="erickesc21@hotmail.com"


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY ./scripts /scripts

RUN python -m venv /venv
RUN adduser --disabled-password --no-create-home duser
RUN mkdir -p /data/
RUN chown -R duser:duser /data
RUN chmod -R +x /scripts



COPY ./app .

EXPOSE 8000



RUN /venv/bin/pip install --upgrade pip
RUN /venv/bin/pip install -r /app/requirements.txt


USER duser

ENV PATH="/scripts:/venv/bin:$PATH"



CMD [ "commands.sh" ]