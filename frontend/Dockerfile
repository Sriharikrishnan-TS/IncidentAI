FROM node:20-alpine AS builder

WORKDIR /app

ARG BACKEND_URL=http://localhost:8080
ARG NEXT_PUBLIC_USE_MOCK=false

ENV BACKEND_URL=$BACKEND_URL
ENV NEXT_PUBLIC_BACKEND_URL=$BACKEND_URL
ENV NEXT_PUBLIC_USE_MOCK=$NEXT_PUBLIC_USE_MOCK

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ARG BACKEND_URL=http://localhost:8080
ARG NEXT_PUBLIC_USE_MOCK=false

ENV NODE_ENV=production
ENV BACKEND_URL=$BACKEND_URL
ENV NEXT_PUBLIC_BACKEND_URL=$BACKEND_URL
ENV NEXT_PUBLIC_USE_MOCK=$NEXT_PUBLIC_USE_MOCK

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/app ./app
COPY --from=builder /app/components ./components
COPY --from=builder /app/hooks ./hooks
COPY --from=builder /app/lib ./lib
COPY --from=builder /app/services ./services
COPY --from=builder /app/types ./types
COPY --from=builder /app/next.config.mjs ./next.config.mjs
COPY --from=builder /app/postcss.config.mjs ./postcss.config.mjs
COPY --from=builder /app/tailwind.config.ts ./tailwind.config.ts
COPY --from=builder /app/tsconfig.json ./tsconfig.json
COPY --from=builder /app/components.json ./components.json
COPY --from=builder /app/next-env.d.ts ./next-env.d.ts

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]