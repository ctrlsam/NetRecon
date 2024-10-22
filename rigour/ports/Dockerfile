# ==============================================
# Stage 1: Build ZMap and ZTee from source
# ==============================================
FROM ubuntu:24.04 as builder

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install build dependencies
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    cmake \
    libgmp3-dev \
    gengetopt \
    libpcap-dev \
    flex \
    byacc \
    libjson-c-dev \
    libjudy-dev \
    pkg-config \
    libunistring-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/src

# Clone the ZMap repository
RUN git clone https://github.com/zmap/zmap.git

WORKDIR /usr/local/src/zmap

# Build and install ZMap and ZTee
RUN mkdir -p /opt/zmap \
    && cmake . -DRESPECT_INSTALL_PREFIX_CONFIG=ON \
    && cmake --build . --parallel "$(nproc)" \
    && cmake --install . --prefix "/opt/zmap"

# ===========================================================
# Stage 2: Create the final image with runtime dependencies
# ===========================================================
FROM ubuntu:24.04

LABEL org.opencontainers.image.source="https://github.com/zmap/zmap"

# Install runtime dependencies and Python
RUN apt-get update \
    && apt-get install -y \
    libpcap0.8 \
    libjson-c5 \
    libjudydebian1 \
    libgmp10 \
    dumb-init \
    python3 \
    python3-pip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy ZMap and ZTee binaries from the builder stage
COPY --from=builder /opt/zmap /opt/zmap

# Set the PATH environment variable
ENV PATH="/opt/zmap/sbin:${PATH}"

WORKDIR /app

ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install the common module
COPY rigour/common/ /app/lib/common/
RUN pip install --no-cache-dir -e /app/lib/common/

# Install ports dependencies
COPY rigour/ports /app/
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

# Download GEO IP database
RUN chmod +x ./download_geodb.sh && ./download_geodb.sh

# Set the entry point to run the Python script using dumb-init
ENTRYPOINT ["dumb-init", "python3", "main.py"]
