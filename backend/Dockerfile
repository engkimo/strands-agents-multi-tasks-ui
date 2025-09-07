FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ソースはボリュームでマウント（開発用）

ENV DB_PATH=/app/var/data/app.db \
    DATA_DIR=/app/var/data

EXPOSE 8000

CMD ["uvicorn", "app.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

