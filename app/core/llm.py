import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found")


class GroqLLM:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    def invoke(self, prompt: str):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # lower for better SQL
            max_completion_tokens=1500,
            top_p=1,
            stream=False  # IMPORTANT: disable streaming for agents
        )

        content = completion.choices[0].message.content

        class LLMResponse:
            def __init__(self, content):
                self.content = content

        return LLMResponse(content)


def get_llm():
    return GroqLLM()