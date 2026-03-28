FROM python:3.13-alpine

# Install docker CLI for running compose commands
RUN apk add --no-cache docker-cli docker-cli-compose git

WORKDIR /app

COPY webhook-listener.py .
COPY deploy.sh .
RUN chmod +x deploy.sh

EXPOSE 9000

CMD ["python", "webhook-listener.py"]
