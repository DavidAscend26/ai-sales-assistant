import json
from decimal import Decimal
from typing import Any
import structlog

from app.core.config import settings
from app.llm.client import get_openai_client
from app.llm.prompts import SYSTEM_PROMPT
from app.llm.schemas import ToolCatalogArgs, ToolFinancingArgs, ToolRagArgs, ToolNormalizeArgs
from app.tools.catalog import CatalogQuery, search_catalog, known_make_model_pairs
from app.tools.financing import calc_financing
from app.tools.normalize import normalize_make_model
from app.tools.rag import retrieve_kavak_knowledge
from sqlalchemy.ext.asyncio import AsyncSession

log = structlog.get_logger()

def _tool_defs() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_catalog",
                "description": "Busca autos disponibles en el catálogo usando filtros estructurados.",
                "parameters": ToolCatalogArgs.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calc_financing",
                "description": "Calcula opciones de financiamiento con tasa anual fija y plazos 3 a 6 años.",
                "parameters": ToolFinancingArgs.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "retrieve_kavak_knowledge",
                "description": "Recupera información oficial para responder sobre Kavak (propuesta de valor, sedes, políticas).",
                "parameters": ToolRagArgs.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "normalize_make_model",
                "description": "Normaliza marca/modelo con fuzzy matching para tolerar errores del usuario.",
                "parameters": ToolNormalizeArgs.model_json_schema(),
            },
        },
    ]

async def run_agent(session: AsyncSession, history: list[dict[str, str]], user_message: str) -> str:
    client = get_openai_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-(settings.HISTORY_MAX_TURNS * 2):]:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})

    tools = _tool_defs()

    for step in range(6):  # tool loop acotado
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
        )
        choice = resp.choices[0]
        msg = choice.message

        if not getattr(msg, "tool_calls", None):
            return (msg.content or "").strip()

        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls})

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")
            out: Any

            if name == "search_catalog":
                parsed = ToolCatalogArgs(**args)
                q = CatalogQuery(**parsed.model_dump())
                out = await search_catalog(session, q)

            elif name == "calc_financing":
                parsed = ToolFinancingArgs(**args)
                options = calc_financing(
                    price_mxn=Decimal(str(parsed.price_mxn)),
                    down_payment=Decimal(str(parsed.down_payment)),
                    annual_rate=Decimal(str(parsed.annual_rate)),
                )
                out = [
                    {
                        "years": o.years,
                        "months": o.months,
                        "monthly_payment": str(o.monthly_payment),
                        "total_paid": str(o.total_paid),
                        "total_interest": str(o.total_interest),
                    }
                    for o in options
                ]

            elif name == "retrieve_kavak_knowledge":
                parsed = ToolRagArgs(**args)
                out = await retrieve_kavak_knowledge(session, parsed.query, parsed.top_k)

            elif name == "normalize_make_model":
                parsed = ToolNormalizeArgs(**args)
                pairs = await known_make_model_pairs(session)
                norm = normalize_make_model(parsed.make, parsed.model, pairs)
                out = {
                    "make": norm.make,
                    "model": norm.model,
                    "confidence": norm.confidence,
                    "candidates": norm.candidates,
                }
            else:
                out = {"error": "unknown_tool"}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(out, ensure_ascii=False),
                }
            )

        log.info("agent_tool_step", step=step, tool_calls=[t.function.name for t in msg.tool_calls])

    return "Lo siento, tuve un problema procesando tu solicitud. ¿Podrías reformularla en una frase?"