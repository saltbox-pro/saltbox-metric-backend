# Salt.Box Metric

This is Salt.Box metric backend repository.

## Development

This project uses the following tools.

- [pytest](https://docs.pytest.org/) for writing tests
- [ruff](https://astral.sh/ruff) for Python source linting and formatting
- [mypy](https://mypy.readthedocs.io/en/stable/) for static type checking
- [pre-commit](https://pre-commit.com/) for Git hooks

### Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip3 install -e .[dev]  # pip install -e .\[dev\]  in some cases
```

After deploying dev environment install pre-commit hooks with
`pre-commit install` command.

### Verifying your setup

To verify that your setup is working, run the following commands:

```bash
ruff check
mypy .
pre-commit run --all-files
```

If any of the above processes fail, please reach out to the project maintainers for support!
```

### Run

Use [Salt.Box Compose](https://gitlab.com/saltbox/saltbox-compose) repo to run
whole system.
