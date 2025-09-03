FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV WEB_URL=http://52.0.216.22:7080
ENV MONGODB_URI=mongodb://etl_user:etl_pass123@52.0.216.22:27017/etl_tracker
ENV API_BASE_URL=http://52.0.216.22:7300
ENV LOG_LEVEL=info
ENV RETRY_ATTEMPTS=3
ENV PROCESO_DESCRIPCION="Extracción contactos empresariales - Empresas Tech"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create non-root user for security
RUN useradd -m -u 1000 etluser && chown -R etluser:etluser /app
USER etluser

# Command to run the application
CMD ["python", "main.py"]