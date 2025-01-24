# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the application code to the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the default port Cloud Run uses
EXPOSE 8080

# Use functions-framework
CMD exec functions-framework --target=compare_faces_and_copy --port=$PORT --source=main_CF.py