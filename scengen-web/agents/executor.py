import json
import re
import demjson3
from playwright.sync_api import Page
import time

class Executor:
    def __init__(self, page: Page):
        self.page = page

    def perform(self, action_json: str, widgets=None):
        action = self._extract_json(action_json)

        action_type = action.get("action")
        label = action.get("target_widget_label", "").lower()
        input_text = action.get("input_text")
        bounding_box = None
        if widgets and label:
            for w in widgets:
                if w.get("label", "").lower() == label:
                    bounding_box = w.get("bounding_box")
                    break

        print(f"\n🚀 Executing Action: {action_type} → {label}")

        if action_type == "click":
            self._click_widget(label, bounding_box, widgets)

        elif action_type in ["input", "type"]:
            self._input_text(label, input_text, bounding_box, widgets)

        elif action_type == "scroll":
            self.page.mouse.wheel(0, 500)

        elif action_type == "back":
            self.page.go_back()

    def _click_widget(self, label, bounding_box, widgets):
        # Try by label
        try:
            print(f"Trying to click by label: {label}")
            self.page.locator(f"text={label}").first.click(timeout=5000)
            return
        except Exception as e:
            print(f"⚠️ Failed to click by label '{label}': {e}")
        # Try by bounding box
        if bounding_box:
            try:
                print(f"Trying to click by bounding box: {bounding_box}")
                x = (bounding_box[0] + bounding_box[2]) // 2
                y = (bounding_box[1] + bounding_box[3]) // 2
                self.page.mouse.click(x, y)
                return
            except Exception as e:
                print(f"⚠️ Failed to click by bounding box: {e}")
        # Try by type (first button)
        try:
            print("Trying to click first button on page")
            self.page.locator("button").first.click(timeout=5000)
            return
        except Exception as e:
            print(f"⚠️ Failed to click first button: {e}")
        print("❌ Could not click any widget.")

    def _input_text(self, label, text, bounding_box, widgets):
        # Try by label
        try:
            print(f"Trying to input by label: {label}")
            input_field = self.page.locator(f"text={label}").locator("..")\
                .locator("input").first
            input_field.click()
            input_field.fill("")  # Clear field
            time.sleep(0.2)
            input_field.type(text, delay=50)
            return
        except Exception as e:
            print(f"⚠️ Failed to input by label '{label}': {e}")
        # Try by common field names
        if label in ["username", "user name", "user"]:
            try:
                print("Trying to input in input[name='user-name']")
                input_field = self.page.locator("input[name='user-name']").first
                input_field.click()
                input_field.fill("")
                time.sleep(0.2)
                input_field.type(text, delay=50)
                return
            except Exception as e:
                print(f"⚠️ Failed to input in input[name='user-name']: {e}")
        if label in ["password", "pass"]:
            try:
                print("Trying to input in input[name='password']")
                input_field = self.page.locator("input[name='password']").first
                input_field.click()
                input_field.fill("")
                time.sleep(0.2)
                input_field.type(text, delay=50)
                return
            except Exception as e:
                print(f"⚠️ Failed to input in input[name='password']: {e}")
        # Try by bounding box
        if bounding_box:
            try:
                print(f"Trying to input by bounding box: {bounding_box}")
                x = (bounding_box[0] + bounding_box[2]) // 2
                y = (bounding_box[1] + bounding_box[3]) // 2
                self.page.mouse.click(x, y)
                time.sleep(0.2)
                self.page.keyboard.type(text, delay=50)
                return
            except Exception as e:
                print(f"⚠️ Failed to input by bounding box: {e}")
        # Try all input fields
        try:
            print("Trying to input in first visible input field")
            input_field = self.page.locator("input").first
            input_field.click()
            input_field.fill("")
            time.sleep(0.2)
            input_field.type(text, delay=50)
            return
        except Exception as e:
            print(f"⚠️ Failed to input in first input: {e}")
        print("❌ Could not input text in any widget.")

    def _extract_json(self, text):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            json_str = match.group(0)
            print("----- Extracted JSON string from Decider -----")
            print(json_str)
            print("------------------------------------------------")
            try:
                return json.loads(json_str)
            except Exception:
                try:
                    return demjson3.decode(json_str)
                except Exception as e:
                    print("demjson3 failed to parse. Error:", e)
                    print("\n❌ Could not parse Decider output as JSON. Here is the raw output for debugging:")
                    print(text)
                    exit(1)
        print("\n❌ No valid JSON object found in Decider output. Here is the raw output for debugging:")
        print(text)
        exit(1) 