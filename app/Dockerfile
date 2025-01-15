# Step 1: Use an official Python runtime as the base image
FROM python:3.12-slim

# Step 2: Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Step 3: Set the working directory in the container
WORKDIR /app

# Step 4: Copy requirements.txt into the container
# First copy just the requirements to leverage Docker caching for dependencies
COPY requirements.txt .

# Step 5: Install dependencies
RUN pip install --quiet --no-cache-dir -r requirements.txt

# Step 6: Copy the rest of the application code into the container
COPY . .

# Step 7: Expose the port the app runs on
EXPOSE 8080

# Step 8: Default command to run the application
CMD ["python", "app.py"]

# docker build -t  ww .
# docker run -p 5555:8080 --env-file .env ww

# http://127.0.0.1:5555/vectorsearch?prompt=example