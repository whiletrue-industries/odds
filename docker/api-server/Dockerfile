FROM --platform=linux/amd64 python:3.12
RUN apt-get update && apt-get install -y libleveldb-dev ca-certificates && apt-get clean
RUN pip install --upgrade pip
WORKDIR /srv
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY odds ./odds
COPY assistant ./assistant
COPY setup.py ./
RUN pip install -e .
COPY utils ./utils
ENV PYTHONUNBUFFERED=1
RUN mkdir /temp-cache/ && chmod 777 /temp-cache/
ENV RESOURCE_PROCESSOR_CACHE_DIR=/temp-cache
ENTRYPOINT ["/bin/bash", "-c"]
