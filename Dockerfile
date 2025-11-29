# Use Python 3.11 slim (stable)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Upgrade pip, setuptools, wheel and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy the rest of your app
COPY . .

# Expose the port Cloud Run uses
ENV PORT 8080
EXPOSE 8080

# Start your app with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
