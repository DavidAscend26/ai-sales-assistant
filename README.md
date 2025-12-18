# Kavak Sales Bot (WhatsApp + Twilio Sandbox + OpenAI)

Este repo implementa un bot estilo *agente comercial* (Kavak) con:

- **FastAPI** webhook Twilio WhatsApp (responde rápido y encola mensajes)
- **Async queue** con **Redis Streams** (webhook no bloquea)
- **Worker async** que procesa: contexto (Redis) → RAG (Postgres) → LLM (OpenAI tools) → catálogo (Postgres) → financiamiento (determinista)
- **Tools** búsqueda, financiamiento, normalización
- **Postgres (SQLAlchemy async)** para catálogo + knowledge base
- **RapidFuzz** para normalización de marca/modelo (sin regex)
- **Tests** (pytest + pytest-asyncio)
- **Docker + docker compose**

flowchart TD
    WA[WhatsApp (Twilio)]
    API[FastAPI<br/>(/twilio/whatsapp, /chat)]
    CS[ConversationService]

    TOOL1[Catalog Search<br/>(Postgres)]
    TOOL2[Financing Calculator]
    TOOL3[Normalize Make/Model]

    RAG[RAG]
    EMB[Embeddings<br/>(fastembed)]
    VDB[Vector DB<br/>(Qdrant)]
    CHUNKS[Knowledge Chunks<br/>(Postgres)]

    LLM[OpenAI LLM]

    WA --> API
    API --> CS

    CS --> TOOL1
    CS --> TOOL2
    CS --> TOOL3
    CS --> RAG

    RAG --> EMB
    RAG --> VDB
    RAG --> CHUNKS

    CS --> LLM


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