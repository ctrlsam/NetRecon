FROM node:21-alpine

WORKDIR /app

COPY . .

RUN npm ci
RUN npm run build

USER node:node
CMD ["node","build/index.js"]
