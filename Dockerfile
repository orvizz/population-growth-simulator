FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh && sed -i 's/\r//' entrypoint.sh

# entrypoint: runs migrations + conditional seed, then exec CMD
ENTRYPOINT ["./entrypoint.sh"]

# Default command: API. Override in docker-compose for the frontend service.
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
