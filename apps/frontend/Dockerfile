# syntax=docker/dockerfile:1

# ── Stage 1: Build frontend ──
FROM node:22-alpine AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy dependency files (lockfile created from clean install)
COPY apps/frontend/package.json ./

# Install dependencies (clean install — pnpm 11 supply-chain check blocks frozen lockfile in Docker)
RUN pnpm install --ignore-scripts

# Copy source + build
COPY apps/frontend/ ./
RUN pnpm build

# ── Stage 2: Serve with Nginx ──
FROM nginx:alpine AS runtime

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
