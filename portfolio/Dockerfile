FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM alpine:3.20
# Copy built static files to a volume mount point
# Caddy serves these directly — no runtime needed
COPY --from=build /app/dist /dist
# Container exits after copying; this is a build-only container
CMD ["echo", "Portfolio built successfully"]
