FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (leverage Docker cache)
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the backend and frontend code
# Note: The backend/app/main.py expects the frontend folder to be at the same level as backend
COPY backend /app/backend
COPY frontend /app/frontend

# Set the working directory to the backend so uvicorn can find "app.main:app"
WORKDIR /app/backend

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application in production (no reload, multiple workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
