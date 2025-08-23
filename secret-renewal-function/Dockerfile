FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY main.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the port that the functions framework uses
EXPOSE 8080

# Run the functions framework
CMD ["functions-framework", "--target=handle_secret_expiration", "--port=8080"]