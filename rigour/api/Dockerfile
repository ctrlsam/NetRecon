FROM python:3.12-alpine3.20

WORKDIR /app

# Install the common module
COPY rigour/common/ /app/common/
RUN pip install --no-cache-dir -e ./common

# Install ports dependencies
COPY rigour/api /app/
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

CMD ["python", "-m", "uvicorn", "main:app", \
    "--host", "0.0.0.0", \
    "--port", "1234"]
