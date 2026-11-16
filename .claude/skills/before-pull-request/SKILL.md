---
name: before-pull-request
description: Use before opening a pull request to the lab's SpeechInNoise repository, or before handing in a capstone version: checks the branch, runs every test without skips, and updates the test counts.
---

# Before a pull request

1. **Branch.** `git fetch upstream`. The branch must start from `upstream/main` and
   hold one change. `git diff --name-only upstream/main...HEAD` lists the files it
   touches; anything outside the change (other branches' files, `capstone/`, `docs/`,
   `CLAUDE.md`) means the branch is wrong. Stop and say so.
2. **Install.** `pip install jieba playwright && playwright install chromium`.
3. **Run.** `pytest -rs --ignore=asr_test.py --ignore=offline_asr_test.py --ignore=offline_asr_whisper_test.py`.
   Any failure, or any "skipped", stops here: report it, do not open the pull request.
4. **Guards.** `transcripts_frozen_test.py` passed and `metadata/transcripts.sha256` is
   not in the diff (unless Yunqi asked for that change). New `.csv` / `.txt` / `.png`
   files are in `git status` as added, not left out by `.gitignore`.
5. **Counts.** On `capstone`, update the test numbers in `capstone/README.md` to this
   run's output; never copy them from an older run. `docs/check-in.md` describes one
   commit and keeps its numbers.
6. **Report** the branch, the commit, the files touched, and the test summary line.
   Opening the pull request is Yunqi's decision.
