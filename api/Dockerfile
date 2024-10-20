FROM python:3.12-slim as base

RUN apt-get update && \ 
    apt-get install -y \
    git \
    libgeos-dev \
    ssh \
    --no-install-recommends \
    &&  pip3 install --upgrade pip \
    &&  rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# CMD ["python", "-m", "uvicorn", "app:app", \
#     "--host", "0.0.0.0", \
#     "--port", "80" ]

CMD ["python", "app.py"]
