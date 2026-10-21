# Contributing

Run tests before pushing:

```bash
python -m unittest discover -s tests -p "test_*.py"
node --test tests/utils.test.mjs
```

Never commit tokens. `HF_TOKEN` belongs in GitHub Actions secrets only.
