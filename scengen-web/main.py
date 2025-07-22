from agents.observer import Observer
from agents.decider import Decider
from agents.executor import Executor
from agents.supervisor import Supervisor
from agents.recorder import Recorder
from agents.excel_logger import TestCaseExcelLogger
from bugs.reporter import BugReporter
import uuid
from playwright.sync_api import sync_playwright
import sys
import json
import time
from PIL import Image
from io import BytesIO
import os

LOG_DIR = "scengen-logs"
os.makedirs(LOG_DIR, exist_ok=True)

SUCCESS_KEYWORDS = ["logout", "dashboard", "welcome", "success"]

if __name__ == "__main__":
    excel_logger = TestCaseExcelLogger()
    while True:
        url = input("Enter the URL to test (or 'q' to quit): ")
        if url.strip().lower() == 'q':
            break
        scenario = input("Enter the test scenario: ")
        test_case_id = str(uuid.uuid4())[:8]
        print(f"\n--- Running Test Case {test_case_id} ---")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(record_video_dir=f"{LOG_DIR}/videos_{test_case_id}")
            page = context.new_page()
            page.goto(url)
            page.wait_for_load_state("networkidle")

            observer = Observer()
            decider = Decider()
            executor = Executor(page)
            supervisor = Supervisor()
            recorder = Recorder()
            bug_reporter = BugReporter()
            history = []
            log_steps = []
            success = False
            passed = 0
            failed = 0
            bug_count = 0

            for step in range(20):  # Max steps to avoid infinite loops
                print(f"\n--- Step {step+1} ---")
                before_screenshot = page.screenshot(full_page=True)
                before_img = observer.memory.save_image_from_bytes(before_screenshot)
                widgets, info_texts = observer.analyze_gui(before_img)

                action_json = decider.decide_next_action(json.dumps(widgets), info_texts, scenario, history)
                print("Decider output:", action_json)
                # Try to parse action
                try:
                    import re
                    import demjson3
                    match = re.search(r"\{.*\}", action_json, re.DOTALL)
                    if match:
                        action = demjson3.decode(match.group(0))
                    else:
                        print("No valid JSON found in Decider output. Stopping.")
                        break
                except Exception as e:
                    print("Failed to parse Decider output:", e)
                    break

                # Stopping condition: action is "stop" or empty
                if not action or action.get("action") in ["stop", None, ""]:
                    print("Stopping condition met. Exiting loop.")
                    break

                executor.perform(json.dumps(action), widgets)
                history.append(action)
                time.sleep(1)  # Optional: wait a bit between steps

                # Supervisor step: capture after screenshot and verify
                after_screenshot = page.screenshot(full_page=True)
                after_img = observer.memory.save_image_from_bytes(after_screenshot)
                verdict = supervisor.verify_transition(before_img, after_img, scenario, json.dumps(action))
                print("\n🧾 Supervisor Verdict:\n", verdict)

                # Save logs for this step
                step_log = {
                    "step": step+1,
                    "action": action,
                    "verdict": verdict,
                    "widgets": widgets,
                    "info_texts": info_texts,
                    "before_screenshot": f"{LOG_DIR}/before_{test_case_id}_{step+1}.png",
                    "after_screenshot": f"{LOG_DIR}/after_{test_case_id}_{step+1}.png"
                }
                log_steps.append(step_log)
                with open(f"{LOG_DIR}/before_{test_case_id}_{step+1}.png", "wb") as f:
                    f.write(before_screenshot)
                with open(f"{LOG_DIR}/after_{test_case_id}_{step+1}.png", "wb") as f:
                    f.write(after_screenshot)
                with open(f"{LOG_DIR}/step_{test_case_id}_{step+1}.json", "w") as f:
                    json.dump(step_log, f, indent=2)

                # RECORD
                recorder.record(step+1, json.dumps(action), verdict)

                # BUG REPORTING & EXCEL LOGGING
                bug_id = str(uuid.uuid4())[:8]
                before_path = f"ui_snapshots/step{test_case_id}_{step+1}_{bug_id}_before.png"
                after_path = f"ui_snapshots/step{test_case_id}_{step+1}_{bug_id}_after.png"
                before_img.save(before_path)
                after_img.save(after_path)
                result = "Pass" if ("yes" in verdict.lower() or "success" in verdict.lower()) else "Fail"
                excel_logger.log_step(
                    test_case_id=test_case_id,
                    scenario=scenario,
                    step=step+1,
                    action=json.dumps(action),
                    verdict=verdict,
                    result=result,
                    before_path=before_path,
                    after_path=after_path,
                    bug_id=bug_id if result == "Fail" else None
                )
                if result == "Fail":
                    print("❗ Bug detected. Logging...")
                    bug_reporter.report_bug(
                        step_number=step+1,
                        action_json=json.dumps(action),
                        verdict=verdict,
                        before_img_path=before_path,
                        after_img_path=after_path
                    )
                    failed += 1
                    bug_count += 1
                else:
                    passed += 1

                # Optional: retry once if supervisor says failed or no change
                if any(word in verdict.lower() for word in ["fail", "no change", "not effective"]):
                    print("Supervisor indicated failure or no change. Retrying action once...")
                    executor.perform(json.dumps(action), widgets)
                    time.sleep(1)
                    # Re-verify
                    after_screenshot = page.screenshot(full_page=True)
                    after_img = observer.memory.save_image_from_bytes(after_screenshot)
                    verdict = supervisor.verify_transition(before_img, after_img, scenario, json.dumps(action))
                    print("\n🧾 Supervisor Verdict (after retry):\n", verdict)
                    recorder.record(step+1, json.dumps(action), verdict)
                    after_img.save(after_path)
                    result = "Pass" if ("yes" in verdict.lower() or "success" in verdict.lower()) else "Fail"
                    excel_logger.log_step(
                        test_case_id=test_case_id,
                        scenario=scenario,
                        step=step+1,
                        action=json.dumps(action),
                        verdict=verdict,
                        result=result,
                        before_path=before_path,
                        after_path=after_path,
                        bug_id=bug_id if result == "Fail" else None
                    )
                    if result == "Fail":
                        print("❗ Bug detected. Logging...")
                        bug_reporter.report_bug(
                            step_number=step+1,
                            action_json=json.dumps(action),
                            verdict=verdict,
                            before_img_path=before_path,
                            after_img_path=after_path
                        )
                        failed += 1
                        bug_count += 1
                    else:
                        passed += 1

                # Custom success condition: check for keywords in widgets or info_texts
                found_success = any(
                    any(kw in (w.get("label", "") or "").lower() for kw in SUCCESS_KEYWORDS) for w in widgets
                ) or any(
                    any(kw in t.lower() for kw in SUCCESS_KEYWORDS) for t in info_texts
                )
                if found_success:
                    print("✅ Custom success condition met! Exiting loop.")
                    success = True
                    break

            # Save summary log
            summary = {
                "test_case_id": test_case_id,
                "url": url,
                "scenario": scenario,
                "steps": log_steps,
                "success": success,
                "history": history,
                "passed": passed,
                "failed": failed,
                "bugs": bug_count
            }
            with open(f"{LOG_DIR}/summary_{test_case_id}.json", "w") as f:
                json.dump(summary, f, indent=2)
            print(f"\nSummary log saved to {LOG_DIR}/summary_{test_case_id}.json")
            excel_logger.log_summary(
                test_case_id=test_case_id,
                scenario=scenario,
                total_steps=step+1,
                passed=passed,
                failed=failed,
                bug_count=bug_count
            )
            excel_logger.close()
            context.close()
            browser.close()
    print("All test cases complete. QA Excel log is in qa/test_results.xlsx") 