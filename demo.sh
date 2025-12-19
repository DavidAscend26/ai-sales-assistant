#!/usr/bin/env bash
set -e

echo "============================================================"
echo " Agente comercial de IA - Demo Script"
echo "============================================================"

# ----------- Helpers -----------
check_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Comando requerido '$1' no encontrado."
    exit 1
  fi
}

wait_for_service() {
  local name=$1
  local cmd=$2
  local retries=30

  echo "⏳ Esperando $name..."
  until eval "$cmd" >/dev/null 2>&1; do
    retries=$((retries - 1))
    if [ $retries -le 0 ]; then
      echo "❌ $name no estuvo listo a tiempo."
      exit 1
    fi
    sleep 2
  done
  echo "¡✅ $name está listo!"
}

# ----------- Checks -----------
check_command docker
check_command docker-compose || check_command docker

if [ ! -f ".env" ]; then
  echo "❌ .env archivo no encontrado. Por favor copia .env.example a .env y configura OPENAI_API_KEY, DATABASE_URL, REDIS_URL, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, PUBLIC_BASE_URL"
  exit 1
fi

# ----------- Startup -----------
echo "🚀 Construyendo e iniciando servicios..."
docker compose up -d --build

# ----------- Wait for services -----------
wait_for_service "Postgres" \
  "docker compose exec -T postgres pg_isready -U postgres"

wait_for_service "API" \
  "curl -sf http://localhost:8000/health || curl -sf http://localhost:8000"

# ----------- Unit Tests -----------
echo "🧪 Corriendo tests unitarios..."
docker compose exec api pytest -q
echo "✅ Pasaron los tests unitarios."

# ----------- DB Init -----------
echo "🗄️ Inicializando base de datos..."
docker compose exec api python -m app.scripts.init_db

# ----------- Seed Catalog -----------
if [ ! -f "app/catalog.csv" ] && [ ! -f "catalog.csv" ]; then
  echo "❌ catalog.csv not found (expected at ./app/catalog.csv or ./catalog.csv)"
  exit 1
fi

CSV_PATH="/app/catalog.csv"
echo "📥 Sembrando catálogo..."
docker compose exec api python -m app.scripts.seed_catalog \
  --csv "$CSV_PATH" \
  --truncate

# ----------- Ingest Knowledge (RAG) -----------
echo "📚 Consumiendo conocimiento Kavak (RAG) desde https://www.kavak.com/mx/blog/sedes-de-kavak-en-mexico a través de web scrapping ..."
docker compose exec api python -m app.scripts.ingest_kavak_knowledge --truncate

# ----------- Smoke Tests -----------
echo "🔥 Corriendo smoke tests..."

echo "➡️ Prueba 1: Propuesta de valor"
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","message":"¿Cuál es la propuesta de valor de Kavak? Sé específico."}' \
  | jq . || true

echo "➡️ Prueba 2: Búsqueda de catálogo"
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","message":"Busco un Nissan Versa por menos de 300 mil"}' \
  | jq . || true

echo "➡️ Test 3: Financiamiento"
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","message":"El coche cuesta 280000 y tengo 60000 de enganche. Cotiza a 3 años"}' \
  | jq . || true

echo "============================================================"
echo " ✅ Demo completado exitosamente"
echo "============================================================"
echo ""
echo "ℹ️ Optional WhatsApp demo:"
echo "  1. Corre: ngrok http 8000"
echo "  2. Configura Twilio Sandbox webhook -> /twilio/whatsapp"
echo "  3. Envía mensajes directamente desde tu WhatsApp"
echo ""
