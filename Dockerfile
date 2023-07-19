# Pulled July 19, 2023
FROM --platform=linux/amd64 python:3.8@sha256:2ee706fa11ec6907a27f1c5116e9749ad1267336b3b0d53fc35cfba936fae32e
RUN pip install --upgrade pip
WORKDIR /srv
COPY gunicorn_conf.py ./
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY setup.py ./
COPY ckangpt ./ckangpt
RUN pip install -e .
ARG VERSION=local-docker
RUN echo "VERSION = '${VERSION}'" > ckangpt/version.py
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["gunicorn", "-k", "ckangpt.custom_uvicorn_worker.CustomUvicornWorker", "-c", "gunicorn_conf.py", "ckangpt.frontend.api.main:app"]
