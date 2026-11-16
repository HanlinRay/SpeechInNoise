# CLAUDE.md

Fork of the STAR Lab's SpeechInNoise web app. The lab is writing a paper from this
code, so its `main` must stay traceable. Task plan: `capstone/PROMPT.md`.

## Tests

- Install first, or whole test files skip and a run looks green:
  `pip install jieba playwright && playwright install chromium`.
- Run: `pytest --ignore=asr_test.py --ignore=offline_asr_test.py --ignore=offline_asr_whisper_test.py`
  (the three need Whisper/torch). A result with "skipped" is not a pass.
- After a change, update the test counts in `capstone/README.md` from the actual run.
  `docs/check-in.md` is a snapshot of one commit; leave its numbers alone.

## Never

- Commit to `main`, or push to the lab's repository (`upstream`). One branch per change,
  started from `upstream/main`; `capstone` only merges them.
- Edit an existing `metadata/*_transcript.csv`. A re-split list is a new file and a new
  project in `projects.py`.
- Add or change a line of `metadata/transcripts.sha256` unless Yunqi asks. It is the
  guard that old lists did not change.
- Commit audio, databases, subject data, or the lab's MSPSEN / BKB-SIN lists.

## Not visible in the code

- `.gitignore` ignores `*.csv`, `*.txt` and `*.png`: a new file of these types needs
  `git add -f`, or it is silently left out of the commit.
- The original data is `experiments.db` and the recordings on the lab server, and the
  lab's MSPSEN / BKB-SIN lists. Nothing here may write to them.
