FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app
COPY ./main.py /app/main.py

# Copy helper scripts
COPY ./create_strava_user.py /app/
COPY ./create_first_strava_user.py /app/
COPY ./create_user_with_token.py /app/
COPY ./refresh_strava_token.py /app/
COPY ./update_username.py /app/
COPY ./example_fetch_strava_activities.py /app/
COPY ./quick_strava_demo.py /app/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

