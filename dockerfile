# FROM python:3.10-slim

# # Set environment variables
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# # Set the working directory
# WORKDIR /app

# # Install dependencies
# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the application code
# COPY . /app/

# # Expose the application port
# EXPOSE 5000

# # Run the Flask application
# CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]



# Base Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files into container
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Start the app
CMD ["python", "app.py"]
