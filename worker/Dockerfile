# Build from the repository root:  docker build -f worker/Dockerfile -t parser-worker:local .
FROM python:3.11.9-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv
RUN pip install boto3==1.35.30
COPY worker/ worker/
COPY prompts/ prompts/
CMD ["python", "worker/worker.py"]
