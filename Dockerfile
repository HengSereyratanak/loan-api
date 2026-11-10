FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
# Dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Train inside the image
COPY train.py .
RUN python train.py
COPY . .
EXPOSE 8000
CMD ["fastapi", "run", "main.py", "--port", "8000"]
