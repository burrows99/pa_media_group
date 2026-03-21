# ── base: node + pnpm ────────────────────────────────────────────────────────
FROM node:20-slim AS base

RUN npm install -g pnpm
WORKDIR /app
COPY . .
RUN pnpm install

# ── dev: install at runtime then hot-reload via Next.js HMR ─────────────────
FROM base AS dev

CMD ["sh", "-c", "pnpm install && pnpm dev"]

# ── prod: build then serve ────────────────────────────────────────────────────
FROM base AS prod

RUN pnpm build
CMD ["pnpm", "start"]
