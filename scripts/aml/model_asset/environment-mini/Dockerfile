# Base image: CPU-only, minimal Ubuntu 20.04 + Python + AML inference support
FROM mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04

WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY requirements.txt /app/

# Install CPU-only Torch and other dependencies
RUN pip install --upgrade pip && \
    pip install torch==2.1.2+cpu -f https://download.pytorch.org/whl/torch_stable.html && \
    pip install -r requirements.txt --no-cache-dir && \
    find /root/.cache -type d -exec rm -rf {} + || true && \
    find /opt/miniconda/lib/python*/site-packages -name '*.pyc' -delete || true

# Optional environment variables and port config
ENV SVDIR=/var/runit
ENV WORKER_TIMEOUT=400
EXPOSE 5001 8883 8888

RUN apt-get clean && rm -rf /var/lib/apt/lists/*