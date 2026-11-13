import asyncio
import json
import logging

from chain import process_text
from schemas import ResponseSchema

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("test_pipeline")

CASES = {
    "architecture": (
        "Our API is built with FastAPI and uses Redis for caching and PostgreSQL "
        "for persistence. Under load, the connection pool is exhausted and "
        "requests start timing out, which blocks the checkout flow."
    ),
    "error_log": (
        "2026-11-13 10:42:11 ERROR [worker-3] java.lang.OutOfMemoryError: Java heap "
        "space at com.acme.OrderService.process(OrderService.java:88). "
        "Kafka consumer lag is growing on topic orders-events."
    ),
    # Stress cases: ambiguous or incomplete input that may trigger validation failures.
    "ambiguous": "The system is slow sometimes and some users complained about it.",
    "minimal": "Something broke.",
}


async def run_case(name: str, text: str) -> bool:
    logger.info("=== Case: %s ===", name)
    try:
        result = await process_text(text)
    except Exception as exc:
        logger.error("Case '%s' failed after retries: %r", name, exc)
        return False

    if not isinstance(result, ResponseSchema):
        logger.error("Case '%s' returned %s, expected ResponseSchema", name, type(result))
        return False

    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return True


async def main() -> None:
    outcomes = {}
    for name, text in CASES.items():
        outcomes[name] = await run_case(name, text)

    print("\n--- Summary ---")
    for name, ok in outcomes.items():
        print(f"{name}: {'OK' if ok else 'FAILED'}")


if __name__ == "__main__":
    asyncio.run(main())
