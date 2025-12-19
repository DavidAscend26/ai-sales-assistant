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

## Arquitectura (alto nivel)
```
WhatsApp (Twilio)
        │
        ▼
 FastAPI (/twilio/whatsapp, /chat)
        │
        ▼
 ConversationService
        │
        ├─ Tool: Búsqueda de catálogo (Postgres)
        ├─ Tool: Calculadora financiera
        ├─ Tool: Normalización de Marca/Modelo
        └─ RAG:
             ├─ Embeddings (fastembed)
             ├─ Vector DB (Qdrant)
             └─ Chunks de conocimiento (Postgres)
        │
        ▼
     OpenAI LLM
```
Servicios:
* api: FastAPI (chat + tools + RAG)
* worker: tareas en background (si aplica)
* postgres: catálogo + chunks
* redis: memoria / colas
* qdrant: base de datos vectorial (RAG)

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

## 2) Clonar y levantar todo con Docker
```bash
git clone DavidAscend26/ai-sales-assistant
cd ai-sales-assistant

cp .env.example .env
# agrega tu OPENAI_API_KEY en .env

docker compose up -d --build
```

Verifica que la API esté viva:
```bash
curl http://localhost:8000/health
```

## 3) Pruebas (Unit tests)

Uso pytest con discovery estándar. Los unit tests validan lógica pura: normalización de texto, cálculo financiero y búsqueda en base de datos.
Los tests no dependen de OpenAI ni Twilio, por lo que son deterministas y rápidos.
Para el flujo completo uso smoke tests vía curl documentados más abajo.
```bash
docker compose exec api pytest -v
```

### Tests incluidos
- **test_normalize.py**: Normalización make/model (RapidFuzz)
- **test_financing.py**: Cálculo de financiamiento
- **test_catalog_search.py**: Búsqueda de catálogo

## 4) Inicializar base de datos y datos

Creat tablas
```bash
docker compose exec api python -m app.scripts.init_db
```

Sembrar catálogo (CSV)
```bash
docker compose exec api python -m app.scripts.init_db
```

Verificación manual:
```bash
docker compose exec postgres psql -U postgres -d kavak \
  -c "SELECT make, model, year, price_mxn FROM cars LIMIT 5;"
```

## 5) Ingesta de conocimiento (RAG)

Indexa conocimiento en:
* Postgres (texto)
* Qdrant (vectores)

```bash
docker compose exec api python -m app.scripts.ingest_kavak_knowledge --truncate
```

Verifica Qdrant:
```bash
curl http://localhost:6333/collections
```

## 6) Smoke tests (End-to-End sin WhatsApp)

Propuesta de valor (RAG)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","message":"¿Cuál es la propuesta de valor de Kavak?"}'
```

Búsqueda de autos (Catálogo)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","message":"Busco un Nissan Versa por menos de 300 mil"}'
```

Financiamiento
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","message":"El coche cuesta 280000 y tengo 60000 de enganche. Cotiza a 3,4,5 y 6 años"}'
```

Con esto se valida:
* API
* Catálogo
* RAG (Qdrant)
* Orquestación LLM
* Tools

## 7) WhatsApp Demo
### Exponer API con ngrok
```bash
ngrok http 8000
```

### Twilio Sandbox
En Twilio Console → WhatsApp Sandbox:
* WHEN A MESSAGE COMES IN:
   ```sh
   https://<ngrok-url>/twilio/whatsapp
   ```
* Method: POST

### Probar desde WhatsApp
Ejemplos:
* ¿Qué es Kavak?
* ¿Qué autos tienen disponibles en el catálogo modelo superior a 2020?
* ¿Cómo funciona el financiamiento para un carro de 280,000 con enganchde de 100,000 a 3 años?

## 8) Opción de demo rápida (One-command demo)
Para correr la demo completa (sin Whatsapp) de manera local: build, pruebas, sembrar catalógo, ingestar conocimiento de https://www.kavak.com/mx/blog/sedes-de-kavak-en-mexico a través de web scrapping para RAG, correr smoke tests, etc. usar el siguiente script.
```bash
./demo.sh
```

## Estructura del proyecto
```
app/
├── api/            # FastAPI routes
├── services/       # ConversationService
├── tools/          # catalog, financing, normalize, RAG
├── llm/            # orchestrator
├── db/             # models, session
├── scripts/        # init_db, seed_catalog, ingest_knowledge
├── tests/          # pytest unit tests
docker/
├── Dockerfile
docker-compose.yml
```