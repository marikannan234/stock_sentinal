FROM node:20-alpine AS deps

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package*.json ./
RUN rm -rf .next node_modules && npm install

FROM node:20-alpine AS builder

WORKDIR /app
# Public, build-time values: Next.js inlines NEXT_PUBLIC_* into the bundle, so
# they must be passed with --build-arg (setting them at runtime has no effect).
# Origins only, e.g. https://api.example.com and wss://api.example.com.
# The build fails if NEXT_PUBLIC_API_URL is empty.
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN rm -rf .next && npm run build

FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

COPY --from=builder /app ./
RUN rm -rf .next/cache

EXPOSE 3000

CMD ["npm", "run", "start", "--", "-H", "0.0.0.0", "-p", "3000"]
