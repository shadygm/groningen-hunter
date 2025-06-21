FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary packages (including Chromium and its driver)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl wget gnupg unzip \
        chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*


# Copy requirements file
COPY requirements.txt .

# Install requirements
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code
COPY src src

# Forward stdout
ENV PYTHONUNBUFFERED=1

# Run hunter
CMD ["python", "src/main.py"]
