# Technical Entity Extraction Pipeline

Asynchronous, resilient pipeline built with LangChain (LCEL) and Pydantic. It receives raw technical text (an architecture description or an error log) and returns a validated object with the extracted technologies, a criticality level, and a technical summary.

## Project structure

```
.
├── schemas.py         # Pydantic output schema (ResponseSchema, NivelCriticidad)
├── chain.py           # Prompt, LLM with structured output, retry logic, process_text()
├── test_pipeline.py   # Async test script with clear and ambiguous inputs
├── requirements.txt   # Dependencies
└── README.md
```

## How it works

1. **Schema** (`schemas.py`): `ResponseSchema` defines the contract.
   - `tecnologias`: `list[str]`, at least one element.
   - `nivel_de_criticidad`: enum `baja`, `media` or `alta`.
   - `resumen_tecnico`: non-empty `str`.
2. **Prompt**: a modular `ChatPromptTemplate` with a system instruction and the input text as the `{text}` variable.
3. **Chain**: `prompt | ChatOpenAI(...).with_structured_output(ResponseSchema)`.
4. **Resilience**: the structured LLM is wrapped with `.with_retry()` (up to 3 attempts, exponential backoff with jitter). It retries on parsing and validation failures (`OutputParserException`, `ValidationError`) and on transient OpenAI errors (connection, timeout, rate limit, server error).
5. **Async execution**: `process_text(text)` runs the chain with `.ainvoke()` and returns the validated `ResponseSchema` object. It logs the start, each retry attempt, failures, and the validated result.

## Setup

Requirements: Python 3.11 or later (the schema uses `StrEnum`) and an OpenAI API key.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your-api-key
```

## Usage

Run the test script, which executes the pipeline asynchronously against several example inputs:

```bash
python test_pipeline.py
```

Or call the pipeline from your own code:

```python
import asyncio
from chain import process_text

result = asyncio.run(process_text("Our API uses FastAPI with Redis caching and PostgreSQL..."))
print(result.model_dump(mode="json"))
```

## Example output

For an input such as:

> Our API is built with FastAPI and uses Redis for caching and PostgreSQL for persistence. Under load, the connection pool is exhausted and requests start timing out.

the pipeline returns an object like:

```json
{
  "tecnologias": [
    "FastAPI",
    "Redis",
    "PostgreSQL"
  ],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "API with Redis caching and PostgreSQL persistence; bottleneck identified in concurrent connections."
}
```

Note: this example illustrates the output format. Actual values depend on the model's response.

## Retry behavior and limitations

- `.with_retry()` only retries failures that surface as exceptions. Semantically weak but schema-valid output is not retried, which is why the schema enforces `min_length=1` on the list and the summary: an empty value becomes a `ValidationError` and triggers another attempt.
- A retry re-runs the same request. A small non-zero temperature helps a new attempt differ from the failed one.
- Truncated responses (token limit reached) depend on how the model integration reports `finish_reason` and should be tested separately.
