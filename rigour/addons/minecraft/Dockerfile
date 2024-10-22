FROM python:3.12-alpine3.20

WORKDIR /app

# Install the common module
COPY rigour/common/ /app/common/
RUN pip install --no-cache-dir -e ./common

# Install ports dependencies
COPY rigour/addons/minecraft /app/
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

ENTRYPOINT ["python3", "main.py"]
