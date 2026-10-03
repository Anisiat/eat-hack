# Synthetic Watch Humans data

Requires Python 3.10 or newer. From a fresh checkout (including a GitHub Actions runner):

```sh
python -m pip install -r requirements-watchhumans.txt
python scripts/generate_watchhumans_synthetic.py
python -m unittest discover -s tests -p 'test_watchhumans.py'
```

The generator needs only NumPy and pandas, no API token, network calls, or real consumer data. The dedicated requirements file avoids installing the full notebook environment in the root requirements file.

The default output is `data/watch_humans_synthetic.csv` relative to the repository, even when launched from another working directory. The script creates the folder and atomically replaces the output after a successful write. It produces 5,000 synthetic consumers with 35 columns and no extra CSV index column.

Optional arguments: `--rows 100`, `--seed 42`, `--output /path/to/consumers.csv`. A relative custom output path is relative to the working directory. For the same seed and dependency versions, generation is repeatable. Importing the module does not generate or save anything; call `generate_watch_humans_dataset()` to obtain a DataFrame and `save_watch_humans_dataset(df)` to save it explicitly.

All population proportions, traits, and affinities are synthetic modelling assumptions, not verified Watch Humans customer measurements. GitHub runners discard local files after a job; retain the CSV as a workflow artifact if it is needed after the run. No GitHub workflow is configured by this script.

The separate `generate_watchhumans_data.py` script generates users, reviews, and boroughs for the main application pipeline; see the root README for that workflow.
