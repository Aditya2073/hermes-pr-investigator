# Sample Source Files for Demo

This directory contains a minimal Python Flask app for demonstrating the PR Investigator.

## Structure

```
sample-repo/
├── src/
│   ├── app.py          # Flask app factory
│   ├── middleware/     # Auth middleware (added in PR)
│   ├── models/         # Database models
│   └── routes/         # API routes
├── tests/              # Test suite
└── requirements.txt    # Dependencies
```

## Running the Demo

```bash
cd demo/sample-repo
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
```

## Simulating a PR Review

1. The `sample-diff.patch` in the parent directory shows a realistic PR adding auth
2. Run the investigator scripts against this patch:
   ```bash
   python3 ../../skills/devops/pr-investigator/scripts/analyze_diff.py --plan ../sample-diff.patch
   python3 ../../skills/devops/pr-investigator/scripts/generate_report.py --pr-data ../pr_42.json --findings ../findings.json
   ```
