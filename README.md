# Continuous Large-Prime Search

A Python program that hunts for large prime numbers, running on GitHub
Actions for 12 hours every day and committing its results back to the
repository so each session continues exactly where the last one stopped.

## How it works

- `prime_finder.py` tests odd numbers one by one with the Miller-Rabin
  primality test (40 rounds, error odds below 2^-80 per number).
- Every prime found is appended to `primes.txt`; a log line goes to
  `search.log`.
- Progress is saved to `progress.json` every 30 seconds and when the
  session ends. The workflow commits all three files, so the next
  session resumes at the same number — the search is continuous across
  days, weeks and months.
- The workflow runs twice a day (06:00-12:00 and 12:00-18:00 IST),
  because GitHub limits a single job to 6 hours. Total: 12 hours/day.

## Setup

1. Create a new **public** repository on GitHub (public repos get free,
   unlimited Actions minutes; private repos use your monthly quota of
   2,000 free minutes — 12 h/day would exceed that).
2. Upload these files, keeping the folder structure:
   - `prime_finder.py`
   - `README.md`
   - `.github/workflows/prime-search.yml`
3. Done. The first run starts at 06:00 IST the next day, or go to the
   **Actions** tab, select "Prime Search" and click **Run workflow** to
   start immediately.

## Results

- `primes.txt` — one prime per line, newest at the bottom.
- `search.log` — timestamps of each discovery.
- `progress.json` — current position of the search.

Fresh searches begin at 100-digit numbers. To start somewhere else,
delete `progress.json` (and the result files) and either:
- change the default in `prime_finder.py`: `DEFAULT_DIGITS = 100`, or
- run manually: `python prime_finder.py --start 10**60 --hours 1`.

## Things to know

- GitHub disables scheduled workflows in a repository after 60 days of
  no activity. Any commit (the workflow's own progress commits count)
  keeps it alive.
- Scheduled jobs can start a few minutes late at busy times.
- Rough speed: a 100-digit prime is found every few seconds; expect
  tens of thousands of primes over a month of 12-hour days.

## Run locally

```bash
python prime_finder.py --hours 0.1        # 6-minute test run
python prime_finder.py --digits 200       # 200-digit numbers
```
