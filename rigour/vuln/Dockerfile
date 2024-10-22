FROM python:3.12-alpine3.20

WORKDIR /app

# Install the common module
COPY rigour/common/ /app/lib/common/
RUN pip install --no-cache-dir -e /app/lib/common/

# Install ports dependencies
COPY rigour/vuln /app/
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

# Download vulnerability databases
RUN chmod +x ./download_vuln_dbs.sh && ./download_vuln_dbs.sh

ENTRYPOINT ["python3", "main.py"]
