FROM python:3.13-alpine

# Install docker CLI for running compose commands
RUN apk add --no-cache docker-cli docker-cli-compose git

# Create non-root user
RUN adduser -D -u 1000 webhook

WORKDIR /app

COPY webhook-listener.py .
COPY deploy.sh .
COPY repos.json .
RUN chmod +x deploy.sh

EXPOSE 9000

USER webhook
CMD ["python", "webhook-listener.py"]
