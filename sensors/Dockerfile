FROM python:3.13-alpine

RUN addgroup -g 20 dialout || true
RUN adduser -D -u 1000 -G dialout sensors

RUN pip install --no-cache-dir pyserial

WORKDIR /app

COPY server.py .

RUN mkdir /data && chown sensors:sensors /data

EXPOSE 8000

USER sensors
CMD ["python", "server.py"]
