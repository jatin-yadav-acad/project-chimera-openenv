# Stage 1: Build the Next.js Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json ./
# Provide a minimal package.json if it doesn't exist to ensure npm install succeeds
# We will create this in the codebase so it gets copied properly.
RUN npm install --legacy-peer-deps

COPY frontend/ ./
RUN npm run build

# Stage 2: Final Backend Image
FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./backend/
COPY openenv.yaml ./openenv.yaml

# Copy frontend static build into /app/static
COPY --from=frontend-builder /app/frontend/out ./static

# Expose port 8000 for Hugging Face Spaces / Docker
EXPOSE 7860

# Start Uvicorn pointing to the backend module
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
