# ==============================================
# Stage 1: Build ZGrab from source
# ==============================================
ARG GO_VERSION=1.20
ARG PYTHON_VERSION=3.12
FROM golang:${GO_VERSION}-alpine3.16 as build

# System dependencies
RUN apk add --no-cache make git

WORKDIR /usr/src/zgrab2

# Clone the ZMap repository
RUN git clone https://github.com/zmap/zgrab2.git .

# Copy and cache deps
RUN go mod download && go mod verify

# Build the actual app
RUN make all

# ===========================================================
# Stage 2: Create the final image with runtime dependencies
# ===========================================================
FROM python:${PYTHON_VERSION}-alpine3.20 as run

COPY --from=build /usr/src/zgrab2/cmd/zgrab2/zgrab2 /usr/bin/zgrab2
ENV PATH="/usr/bin/zgrab2:${PATH}"

COPY process.py .
COPY requirements.txt .

RUN pip install -r requirements.txt && \
    rm requirements.txt

ENTRYPOINT ["python3", "process.py"]