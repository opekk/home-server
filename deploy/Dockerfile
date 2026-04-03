FROM python:3.13-alpine

# Install docker CLI for running compose commands
RUN apk add --no-cache docker-cli docker-cli-compose git su-exec

# Create docker group matching host GID for socket access
RUN addgroup -g 989 docker

# Create non-root user with docker group membership
RUN adduser -D -u 1000 webhook
RUN addgroup webhook docker

WORKDIR /app

COPY webhook-listener.py .
COPY deploy.sh .
COPY repos.json .
COPY entrypoint.sh .
RUN chmod +x deploy.sh entrypoint.sh

EXPOSE 9000

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["./entrypoint.sh"]
