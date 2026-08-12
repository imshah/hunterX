# HunterX

Optimize your resume for any job posting. Scrape a job description from any URL, then let Kimi rewrite your resume to maximize ATS compatibility.

## Installation

Requires Python 3.11+ installed on your machine.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Create a `.env` file with your Kimi (Moonshot AI) token:

```env
KIMI_API_TOKEN=sk-your-kimi-token
# Optional overrides (these are the defaults):
KIMI_BASE_URL=https://api.moonshot.ai/anthropic
KIMI_MODEL=kimi-k2.6
```

Get a token from the [Moonshot AI platform](https://platform.moonshot.ai/). HunterX talks to Kimi through its Anthropic-compatible Messages API, so no extra SDK is required.

## Project Structure

```
hunterX/
  orig/
    resume3.md          # Your base resume (default for optimize)
  output/
    jds/                # Scraped job descriptions
    *_optimized.md      # Optimized resumes
    *_score.json        # Score breakdowns
    *_eval.json         # Standalone evaluations
  src/hunterx/          # Source code
  tests/                # Test suite
  .env                  # Configuration
```

Place your base resume at `orig/resume3.md`. All commands use this file by default.

## Usage

### `hunterx dump` — Scrape a job description

```bash
hunterx dump <job-posting-url>
```

Works with LinkedIn, Indeed, Greenhouse, Lever, or any job board. Saves the extracted text to `output/jds/`.

```bash
hunterx dump https://www.linkedin.com/jobs/view/3945271082
# => output/jds/jobs_view_3945271082.txt

hunterx dump https://www.indeed.com/viewjob?jk=abc123 -o my_job.txt
```

### `hunterx optimize` — Optimize your resume

```bash
# Uses orig/resume3.md by default
hunterx optimize --jd output/jds/jobs_view_3945271082.txt

# Or specify a different resume
hunterx optimize my_resume.md --jd output/jds/jobs_view_3945271082.txt
```

Runs 5 rounds of optimization by default. Each round refines the resume, scores it across 6 ATS dimensions, and produces feedback for the next round. The output is constrained to fit within 2 pages. Picks the best-scoring round as the final output.

Output goes to `./output/`:
- `jobs_view_3945271082_optimized.md`
- `jobs_view_3945271082_score.json`

Options: `--rounds 7`, `--target 98`, `--output-dir ./results`, `--model kimi-k2.5`

### `hunterx cover` — Generate a cover letter

```bash
# Uses orig/resume3.md by default
hunterx cover --jd output/jds/jobs_view_3945271082.txt

# Or specify a different resume
hunterx cover --jd output/jds/jobs_view_3945271082.txt --rs my_resume.md
```

Generates a tailored cover letter based on your resume and the job description. Saves to `output/<jd-name>_cover_letter.md` and prints it to the console.

### `hunterx eval` — Evaluate ATS readiness (no JD needed)

```bash
hunterx eval resume.md
```

Scores your resume on general ATS best practices — formatting, keyword density, quantified metrics, section structure — without comparing against a specific job description. Saves the score to `output/<name>_eval.json`.

### `hunterx score` — Score against a specific JD

```bash
hunterx score resume.md --jd output/jds/jobs_view_3945271082.txt
```

Shows a score breakdown without modifying anything.

### ATS Scoring Dimensions

| Dimension | Weight |
|-----------|--------|
| Keyword Coverage | 30% |
| Parsing Compliance | 25% |
| Section Completeness | 20% |
| Content Quality | 15% |
| Timeline Consistency | 5% |
| Relevance Alignment | 5% |

## Resume Format

Write your resume in markdown and place it at `orig/resume3.md`:

```markdown
# Your Name
email@example.com | (555) 123-4567 | City, State

## Professional Summary
2-3 sentences about your experience.

## Work Experience

### Job Title
**Company Name** | City, State | Jan 2022 - Present
- Improved X by 40%
- Built Y serving Z users

## Technical Skills
Python, JavaScript, FastAPI, React

## Education
**B.S. Computer Science**, University Name | 2020
```

## Using a Different AI Provider

HunterX uses Kimi (Moonshot AI) by default, via Kimi's Anthropic-compatible Messages API. Both the model and token are configurable in `.env` (`KIMI_MODEL`, `KIMI_API_TOKEN`, `KIMI_BASE_URL`). Here's what to change if you want a different provider.

### Option A: Claude (Anthropic or Vertex)

The simplest swap — the same `anthropic` SDK and `client.messages.create(...)` API. No changes to prompts or scoring logic.

**1. `.env`** — for the direct Anthropic API:

```env
KIMI_API_TOKEN=sk-ant-your-key-here
KIMI_BASE_URL=https://api.anthropic.com
KIMI_MODEL=claude-sonnet-4-6
```

That's it — the default base URL is the only Kimi-specific setting, and pointing it at Anthropic (or dropping the `base_url=` argument in `create_llm_client()`) is enough. For Vertex, swap `anthropic.Anthropic(...)` for `anthropic.AnthropicVertex(project_id=..., region=...)` in `src/hunterx/config.py`.

### Option B: Gemini

Requires changes across multiple files since Gemini has a different SDK and API shape.

**1. Install the SDK:**

```bash
pip install google-genai
```

**2. `.env`:**

```env
GOOGLE_API_KEY=your-gemini-api-key
```

**3. `src/hunterx/config.py`** — new client factory:

```python
from pydantic import Field, SecretStr

# Replace kimi_api_token/kimi_base_url with:
google_api_key: SecretStr = Field(default=SecretStr(""), description="Google AI API key")

# Change default model:
kimi_model: str = Field(default="gemini-2.5-flash")

# Replace create_llm_client():
def create_llm_client(self):
    from google import genai
    return genai.Client(api_key=self.google_api_key.get_secret_value())
```

**4. `src/hunterx/optimizer/engine.py` and `critic.py`** — replace all `client.messages.create(...)` calls:

```python
# Before (Claude):
response = self._client.messages.create(
    model=self._model,
    max_tokens=8192,
    messages=[{"role": "user", "content": prompt}],
)
text = response.content[0].text

# After (Gemini):
response = self._client.models.generate_content(
    model=self._model,
    contents=prompt,
    config={"max_output_tokens": 8192},
)
text = response.text
```

**5. `src/hunterx/optimizer/scorer.py`** — this is the hardest part. The scorer uses Claude's `tool_use` to get structured JSON output. For Gemini, switch to JSON mode:

```python
# Before (Claude tool_use):
response = self._client.messages.create(
    model=self._model,
    max_tokens=4096,
    system=SCORING_SYSTEM_PROMPT,
    messages=[{"role": "user", "content": user_prompt}],
    tools=[SCORE_TOOL],
    tool_choice={"type": "tool", "name": "submit_ats_score"},
)
for block in response.content:
    if block.type == "tool_use":
        return ATSScore.model_validate(block.input)

# After (Gemini JSON mode):
import json
from google.genai import types

response = self._client.models.generate_content(
    model=self._model,
    contents=f"{SCORING_SYSTEM_PROMPT}\n\n{user_prompt}",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ATSScore.model_json_schema(),
        max_output_tokens=4096,
    ),
)
return ATSScore.model_validate(json.loads(response.text))
```
