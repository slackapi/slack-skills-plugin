from deepeval.models import OllamaModel


class NoThinkOllamaModel(OllamaModel):
    """OllamaModel that disables thinking mode for reliable structured output."""

    def generate(self, prompt, schema=None):
        chat_model = self.load_model()
        messages = [{"role": "user", "content": prompt}]
        response = chat_model.chat(
            model=self.name,
            messages=messages,
            format=schema.model_json_schema() if schema else None,
            options={"temperature": self.temperature, "num_ctx": 32768},
            think=False,
        )
        return (
            (schema.model_validate_json(response.message.content) if schema else response.message.content),
            0,
        )

    async def a_generate(self, prompt, schema=None):
        chat_model = self.load_model(async_mode=True)
        messages = [{"role": "user", "content": prompt}]
        response = await chat_model.chat(
            model=self.name,
            messages=messages,
            format=schema.model_json_schema() if schema else None,
            options={"temperature": self.temperature, "num_ctx": 32768},
            think=False,
        )
        return (
            (schema.model_validate_json(response.message.content) if schema else response.message.content),
            0,
        )
