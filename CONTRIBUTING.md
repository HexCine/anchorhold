# Contributing

Use Python 3.11 or newer. From this repository:

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pip install build
python -m build
```

Start with an issue containing a minimal synthetic input and expected behavior.
Add a regression test for a behavioral change. Keep output schema version 1
compatible or propose an explicit migration. No network access is needed at
runtime. Contributions are licensed under MIT. Maintainers review scope,
correctness, resource limits and documentation before merging.
