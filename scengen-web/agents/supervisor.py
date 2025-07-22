import os
import base64
from io import BytesIO
from PIL import Image
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv(dotenv_path="/Users/krkaushikkumar/Desktop/kwest-ai/scengen-web/.env")
hf_token = os.getenv("HUGGINGFACE_TOKEN")

client = InferenceClient(
    provider="auto",
    api_key=hf_token,
)

class Supervisor:
    def __init__(self):
        pass

    def verify_transition(self, prev_image: Image.Image, curr_image: Image.Image, scenario: str, last_action: str):
        prompt_template = open("prompts/supervisor_prompt.txt").read()
        prompt = prompt_template.format(scenario=scenario, action=last_action)

        def img_to_data_url(img):
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_b64}"

        prev_data_url = img_to_data_url(prev_image)
        curr_data_url = img_to_data_url(curr_image)

        # Compose messages for the vision model
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": prev_data_url}},
                    {"type": "image_url", "image_url": {"url": curr_data_url}}
                ]
            }
        ]
        completion = client.chat.completions.create(
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            messages=messages,
        )
        return completion.choices[0].message.content.strip() if hasattr(completion.choices[0].message, 'content') else str(completion) 