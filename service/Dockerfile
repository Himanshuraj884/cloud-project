# Build from the repository root:  docker build -f service/Dockerfile -t parser-service:local .
FROM python:3.11.9-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HUB_OFFLINE=1
WORKDIR /srv
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.4.1
COPY service/requirements.txt service/requirements.txt
RUN pip install -r service/requirements.txt
COPY service/ service/
RUN useradd -m app && chown -R app /srv
USER app
EXPOSE 8000
# No model weights in the image: they are downloaded from object storage at start-up.
CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
