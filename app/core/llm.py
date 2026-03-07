import os
from dotenv import load_dotenv
from groq import Groq
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not found in environment variables")
    raise ValueError("GROQ_API_KEY not found")
else:
    logger.debug("GROQ_API_KEY loaded successfully")


class GroqLLM:
    def __init__(self):
        logger.debug("Initializing Groq LLM client")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"
        logger.info(f"Groq LLM initialized with model: {self.model}")

    def invoke(self, prompt: str):
        logger.debug(f"Invoking LLM with prompt length: {len(prompt)} characters")
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # lower for better SQL
                max_completion_tokens=1500,
                top_p=1,
                stream=False  # IMPORTANT: disable streaming for agents
            )

            content = completion.choices[0].message.content
            logger.debug(f"LLM response received, length: {len(content)} characters")

            class LLMResponse:
                def __init__(self, content):
                    self.content = content

            return LLMResponse(content)
            
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise


def get_llm():
    logger.debug("Creating new LLM instance")
    return GroqLLM()