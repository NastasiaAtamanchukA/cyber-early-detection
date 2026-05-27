FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./

# npm 10.8.x иногда нестабильно завершает npm ci в Docker Desktop на Windows.
# Фиксируем более свежую патч-версию npm и используем публичный registry.
RUN npm install -g npm@10.9.2 \
    && npm config set registry https://registry.npmjs.org/ \
    && npm ci --no-audit --no-fund --loglevel=warn \
    && test -f node_modules/typescript/lib/tsc.js

COPY frontend/ ./

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
