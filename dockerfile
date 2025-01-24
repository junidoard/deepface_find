FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-opencv-dev \
    libglib2.0-0 \
    build-essential \
    cmake

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 8080

# Use functions-framework
CMD exec functions-framework --target=compare_faces_and_copy --port=$PORT