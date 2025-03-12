FROM python:3.12

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./fetcher-proxy.py /code/fetcher-proxy.py

CMD ["fastapi", "run", "fetcher-proxy.py", "--port", "8000", "--workers", "8"]