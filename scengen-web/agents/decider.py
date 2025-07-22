import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path="/Users/krkaushikkumar/Desktop/kwest-ai/scengen-web/.env")

class Decider:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def decide_next_action(self, widgets_json: str, info_texts: list, scenario: str, history: list = []):
        prompt_template = open("prompts/decider_prompt.txt").read()

        system_msg = {
            "role": "system",
            "content": "You are the Decider agent in a GUI test automation system. Your job is to suggest the next action to perform."
        }

        user_msg = {
            "role": "user",
            "content": prompt_template.format(
                widgets=widgets_json,
                info_texts="\n".join(info_texts),
                scenario=scenario,
                history=json.dumps(history)
            )
        }

        response = self.client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",  # Or groq-llama3-70b if you prefer
            messages=[system_msg, user_msg],
            temperature=0,
        )

        return response.choices[0].message.content 