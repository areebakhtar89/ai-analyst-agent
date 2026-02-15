import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

HF_TOKEN = os.environ.get("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found")


class LlamaLLM:
    def __init__(self):
        self.client = InferenceClient(
            model="meta-llama/Llama-3.1-8B-Instruct",#"meta-llama/Llama-3.3-70B-Instruct",
            token=HF_TOKEN,
            provider="auto",
        )

    def invoke(self, prompt: str):
        response = self.client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
        )

        class LLMResponse:
            def __init__(self, content):
                self.content = content

        return LLMResponse(response.choices[0].message.content)


def get_llm():
    return LlamaLLM()