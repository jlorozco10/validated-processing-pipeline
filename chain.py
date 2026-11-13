import asyncio
import logging
from dotenv import load_dotenv
from openai import (APIConnectionError, APITimeoutError,
                    RateLimitError, InternalServerError)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.exceptions import OutputParserException
from langchain_core.callbacks import BaseCallbackHandler
from pydantic import ValidationError
from schemas import ResponseSchema

load_dotenv()
logger = logging.getLogger(__name__)
RETRY_ERRORS = (OutputParserException, ValidationError, APIConnectionError, APITimeoutError,
                    RateLimitError, InternalServerError)
class RetryLogger(BaseCallbackHandler):
    def on_retry(self, retry_state, **kwargs):
        logger.warning("Retry attempt %s after: %r",
                       retry_state.attempt_number,
                       retry_state.outcome.exception())
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a technical analyst. Extract technologies, "
    "criticality (baja, media, alta) and a concise technical summary. "
    "The technologies list must not be empty."),
    ("human", "{text}"),
])  
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5, max_retries=0)
structured_llm = llm.with_structured_output(ResponseSchema)
resilient_llm = structured_llm.with_retry(
        retry_if_exception_type=RETRY_ERRORS,
        wait_exponential_jitter=True,
        stop_after_attempt=3
    )   

chain = prompt | resilient_llm

async def process_text(text: str):
    logger.info("Processing text (%d chars)", len(text))
    try:
        result = await chain.ainvoke({"text": text}, config={"callbacks": [RetryLogger()]})
    except Exception:
        logger.exception("Pipeline failed after retries")
        raise
    logger.info("Validated result: %s", result.model_dump_json(indent=2))
    return result
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_text = """
        The system architecture is based on a modular, layered design that separates presentation, business logic, and data management responsibilities. 
        The presentation layer is responsible for handling user interactions and communicating with backend services through RESTful APIs. 
        The application layer implements the core business logic, processes incoming requests, 
        enforces business rules, and coordinates interactions between internal components and external services. 
        The data layer manages data persistence and retrieval through a centralized relational database. 
        Communication between system components is performed over secure HTTPS connections, 
        while authentication and authorization mechanisms ensure controlled access to system resources.
        The architecture promotes scalability, maintainability, reusability,
        and extensibility by minimizing dependencies between components and supporting independent modifications as system requirements evolve.
    """
    asyncio.run(process_text(sample_text))

