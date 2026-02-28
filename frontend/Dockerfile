FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build
ENV PORT 3000
EXPOSE 3000
CMD ["npm", "run", "start"]

