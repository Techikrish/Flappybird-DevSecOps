# build stage
FROM node:18-alpine as build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

# production stage - nginx
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# remove default nginx config to allow client-side routing (not critical here)
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
