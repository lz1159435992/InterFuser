FROM python:3.7-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY offline_eval.py /app/offline_eval.py
COPY batch_eval.py /app/batch_eval.py

ENV KERAS_BACKEND=tensorflow

ENTRYPOINT ["python"]
CMD ["/app/offline_eval.py"]
