FROM docker.io/library/node:lts-bookworm-slim AS build

WORKDIR /app

COPY frontend/ask/ /app/
RUN apt-get update
RUN apt-get install -y ca-certificates
RUN npm install
RUN npm run -- ng build

FROM docker.io/library/node:lts-bookworm-slim AS frontend

WORKDIR /app
RUN apt-get update
RUN apt-get install -y ca-certificates
COPY --from=build /app/dist/ask/ /app/
CMD ["node", "server/server.mjs"]
EXPOSE 4000