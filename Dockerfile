FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose webhook port
EXPOSE 5000

# Run the bot
CMD ["python", "main.py"]
