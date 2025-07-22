# SCENGEN: Autonomous LLM-Powered QA Testing System

SCENGEN is a fully autonomous, LLM-driven QA testing framework for web applications. It leverages vision-language models, Playwright, and advanced logging/reporting to behave like a smart QA engineer—planning, executing, validating, and logging test cases step by step.

## Features

- **LLM-Driven Test Planning:** Uses large language models to understand the UI, plan actions, and adapt to any scenario.
- **Autonomous Execution:** Observer, Decider, Executor, Supervisor, and Recorder agents work together to test, validate, and log every step.
- **Multi-Scenario Support:** Run multiple test cases in a single session, each with its own logs, screenshots, and video.
- **Comprehensive Logging:**
  - Step-by-step logs in `scengen-logs/` (screenshots, JSON, videos)
  - Excel log in `qa/test_results.xlsx` (grouped by test case, with summary rows)
  - Bug log in `bugs/bugs.json` (with before/after screenshots)
- **Playwright Video Recording:** Each test case is recorded for full replay and auditability.
- **Smart Bug Detection:** Supervisor agent validates every action; bugs are logged with context and screenshots.
- **Custom Success Conditions:** Detects scenario completion based on UI state or keywords.
- **Replayable and Auditable:** All actions, bugs, and results are saved for future review or replay.

## Setup

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   pip install openpyxl
   ```
2. **Configure environment:**
   - Add your Hugging Face and Groq API keys to `.env`.
3. **Run the system:**
   ```sh
   python3 main.py
   ```

## Usage

- **Interactive Mode:**
  - Enter the URL and scenario in the terminal for each test case.
  - The system will run the full QA loop, log all results, and prompt for the next scenario.
- **Logs and Reports:**
  - **Excel:** `qa/test_results.xlsx` (all steps, bugs, and summaries)
  - **Screenshots & Videos:** `scengen-logs/`
  - **Bug Log:** `bugs/bugs.json`
  - **Step/Run Summaries:** `scengen-logs/summary_<test_case_id>.json`

## Agents

- **Observer:** Extracts widgets and info from screenshots using a vision-language model.
- **Decider:** Plans the next action using LLM reasoning.
- **Executor:** Performs actions in the browser, with robust widget matching.
- **Supervisor:** Validates if the last action was effective, using before/after screenshots.
- **Recorder:** Logs all actions and results for replay and audit.
- **BugReporter:** Logs bugs with screenshots and context.
- **ExcelLogger:** Logs all steps and summaries in a professional QA Excel format.

## Extending
- Add new scenarios, custom success conditions, or batch input as needed.
- Integrate with CI/CD or issue trackers for full automation.

## License
MIT 