import os
import json
import re
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import base64
from playwright.sync_api import sync_playwright
from memory.context import ShortTermMemory

load_dotenv(dotenv_path="/Users/krkaushikkumar/Desktop/kwest-ai/scengen-web/.env")
print("Loaded HF token:", os.getenv("HUGGINGFACE_TOKEN"))
hf_token = os.getenv("HUGGINGFACE_TOKEN")

client = InferenceClient(
    provider="auto",
    api_key=hf_token,
)

def image_to_data_url(image: Image.Image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_b64}"

class Observer:
    def __init__(self):
        self.memory = ShortTermMemory()

    def capture_gui_state(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state("networkidle")

            screenshot_bytes = page.screenshot(full_page=True)
            image = Image.open(BytesIO(screenshot_bytes))
            image.save("ui_snapshots/latest.png")

            self.memory.store_screenshot(image)
            browser.close()
            return image

    def analyze_gui(self, image):
        import re
        prompt = open("prompts/observer_prompt.txt").read()
        data_url = image_to_data_url(image)
        completion = client.chat.completions.create(
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ],
        )
        # Clean up LLM output
        result = completion.choices[0].message.content if hasattr(completion.choices[0].message, 'content') else str(completion)
        # Remove markdown code fences and leading explanations
        result = re.sub(r"^```[a-zA-Z]*\n?|```$", "", result.strip(), flags=re.MULTILINE)
        # Find the first JSON object in the string
        match = re.search(r"\{.*\}", result, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                parsed = json.loads(json_str)
            except Exception:
                import demjson3
                parsed = demjson3.decode(json_str)
            self.memory.store_widgets(json.dumps(parsed["widgets"]))
            return parsed["widgets"], parsed["info_texts"]
        else:
            print("❌ No valid JSON object found in Observer output. Here is the raw output for debugging:")
            print(result)
            raise ValueError("No valid JSON object found in Observer output.") 