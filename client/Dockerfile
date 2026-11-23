FROM node:24-alpine AS build
RUN npm install -g pnpm@12.10.1
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
# Vite inlines these at build time; the browser calls the services directly.
ARG VITE_SIM_URL=http://localhost:8000
ARG VITE_VISION_URL=http://localhost:8001
ENV VITE_SIM_URL=$VITE_SIM_URL \
    VITE_VISION_URL=$VITE_VISION_URL
RUN pnpm build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
