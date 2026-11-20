# Contributing

## Setup
```
git clone https://github.com/ayush-s-tomar/ai-data-analyst.git
cd ai-data-analyst
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Before opening a pull request
```
python -m pytest -q
python -m flake8 streamlit_app tests benchmark --count --statistics
```
Both must pass. CI runs them on Linux and Windows.

## Guidelines
- One logical change per commit, with a message such as `feat:`, `fix:`, `test:`, `docs:` or `ci:`
- New behaviour needs a test. Anything that touches the sandbox needs an attack-style regression test
- Tests must not call the Groq API. Use the fake client pattern in `tests/test_analyst.py`
- Never commit `secrets.toml`, API keys or uploaded data

## Benchmarks
`python -m benchmark.run_benchmark` and `python -m benchmark.run_hard` call the real model and use your API quota.
If you change the prompt, run both and include the numbers in the pull request.
