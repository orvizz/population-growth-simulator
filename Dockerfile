FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run the API. Override in docker-compose for other services.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
