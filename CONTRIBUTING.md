# Contributing

Thank you for helping test Lysnav for KDE Plasma.

1. Search existing issues before opening a new report.
2. Include your distribution, Plasma version, Qt/PySide6 version, Python version,
   and the app's **About** version. Provide steps to reproduce and a redacted log.
3. Never paste access tokens, private hub credentials, copied `config.json`,
   resident names, precise device identifiers, or addresses.
4. For code changes, run `python3 -m unittest discover -p 'test_*.py' -v`.
5. Keep commands limited to approved device IDs. Any feature that can expand the
   control surface must be reviewed carefully and tested to fail closed.
6. Submit a pull request explaining the behavior changed, how it was tested,
   and whether a live Plasma+DIRIGERA test was performed.

This project uses an unofficial local API and is not supported by IKEA.
