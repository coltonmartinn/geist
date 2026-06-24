FROM python:3.12-slim

WORKDIR /app
COPY backend ./backend
COPY web ./web
COPY data ./data

ENV GEIST_HOST=0.0.0.0
ENV GEIST_PORT=8000
ENV GEIST_DATA_PATH=/app/data/game.json

EXPOSE 8000
CMD ["python", "-m", "backend.server"]
