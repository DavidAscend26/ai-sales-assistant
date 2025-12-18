# Kavak Sales Bot (WhatsApp + Twilio Sandbox + OpenAI)

Este repo implementa un bot estilo *agente comercial* (Kavak) con:

- **FastAPI** webhook Twilio WhatsApp (responde rápido y encola mensajes)
- **Async queue** con **Redis Streams** (webhook no bloquea)
- **Worker async** que procesa: contexto (Redis) → RAG (Postgres) → LLM (OpenAI tools) → catálogo (Postgres) → financiamiento (determinista)
- **Postgres (SQLAlchemy async)** para catálogo + knowledge base
- **RapidFuzz** para normalización de marca/modelo (sin regex)
- **Tests** (pytest + pytest-asyncio)
- **Docker + docker compose**

## 0) Requisitos
- Docker + Docker Compose
- Cuenta Twilio con **WhatsApp Sandbox**
- OpenAI API Key

## 1) Variables de entorno
Copia `.env.example` a `.env` y llena:
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (ej: `gpt-4o-mini`)
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM` (sandbox, ej: `whatsapp:+14155238886`)

## 2) Levantar todo con Docker
```bash
docker compose up --build