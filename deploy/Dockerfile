FROM python:3.13-alpine

# Install docker CLI for running compose commands
RUN apk add --no-cache docker-cli docker-cli-compose git

# Create docker group matching host GID for socket access
RUN addgroup -g 989 docker

# Create non-root user with docker group membership
RUN adduser -D -u 1000 webhook
RUN addgroup webhook docker

WORKDIR /app

COPY webhook-listener.py .
COPY deploy.sh .
COPY repos.json .
RUN chmod +x deploy.sh

EXPOSE 9000

USER webhook
ENV PYTHONUNBUFFERED=1
CMD ["python", "webhook-listener.py"]
