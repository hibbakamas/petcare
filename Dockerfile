# Base image
FROM python:3.12-slim

# Prevent Python from buffering stdout/stderr (important for logs)
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose Flask default port
EXPOSE 5000

# Set Flask environment variables
ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV FLASK_ENV=production

# Run DB migrations on container startup, then start the app
CMD ["sh", "-c", "flask db upgrade && flask run"]