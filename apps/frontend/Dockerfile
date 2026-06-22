# syntax=docker/dockerfile:1

# Simple Nginx serve — frontend pre-built locally with `pnpm build`
FROM nginx:alpine

COPY apps/frontend/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
