# Can the Mandarin speech-in-noise tests be scored fast and the same way every time?

**What it is for, and for whom.** For the audiologists and researchers in Stanford's
STAR Lab who test how well people understand speech in noise, in English and now in
Mandarin. A listener hears a sentence in noise and repeats it; a person, or a speech
recognizer, scores each word right or wrong. That score is only as good as the list
of "words" behind it. In the lab's web app today, the MSPSEN lists show each Mandarin
sentence as one unbroken string (one button for the whole sentence) and the BKB-SIN
lists split it into single characters (one button per character), so the same
listener gets a different score depending on the list. Scoring is also all clicks,
and nobody has checked how well the recognizer scores Mandarin. This project fixes
the scoring units, makes manual scoring fast, and measures the recognizer, so that
the lab can compare L1 Chinese / L2 English listeners with L1 English / L2 Chinese
listeners on equal terms.

**Current state.**

- Keyboard scoring works on every test page and on the rater page: number keys flip
  words 1 to 12, `A`/`N` all/none, `Space` play, `Enter` next once every word is
  scored. 9 browser tests.
- `segment_mandarin.py` splits answers into scoring words. Against the hand-split
  AzBio Mandarin lists (40 sentences), word-boundary F1 is 0.935 (precision 0.944,
  recall 0.926); 50 % of sentences match exactly. The disagreements are of two kinds:
  the hand split is not consistent with itself (很高兴 is one word, but 不 规则的 is
  two), and the program makes real mistakes (期限得 加班了, where 得 means "must" and
  is not a particle; 这 周 轮 到 instead of 这周 轮到). So the tool proposes and a
  native speaker confirms, through a review CSV. 13 tests.
- Found and fixed a bug: choosing "Default" on the start page gave a 400 error on
  the Spanish and Mandarin tests (wrong language code). 5 tests.
- The test pages show where the listener is and how far scoring has got: under
  the test name, "List 1 · Sentence 3 of 20 · 10 dB SNR"; under All / None,
  "5 of 7 words scored · 4 correct", green when every word is scored. The total
  comes from a new `levels` field in the `/start` response; nothing new is
  stored. 14 browser tests and 6 API tests (`scoring_status_test.py`,
  `audio_levels_test.py`).
- Not done yet: the MSPSEN and BKB-SIN lists are not in the GitHub repository (only
  AzBio Mandarin is), so they cannot be re-split until we get them from the server.

EE292M capstone. The plan for the agent is in [PROMPT.md](PROMPT.md); this file is
for reviewers. Where it stands against the plan: [docs/check-in.md](../docs/check-in.md).

## Where things are

The repository is a fork of the lab's
[SpeechInNoise](https://github.com/MalcolmSlaney/SpeechInNoise). The lab is writing a
paper from this code and needs `main` to stay traceable, so every change is a
separate branch that becomes one pull request to the lab:

| Branch | What it changes |
| --- | --- |
| `scoring-keyboard-shortcuts` | `static/scoring_keys.js`, one `<script>` line per page, `scoring_keys_test.py` |
| `mandarin-word-segmentation` | `segment_mandarin.py`, `segment_mandarin_test.py`, `jieba` in requirements |
| `mandarin-default-language` | `api.py` (`PROJECT_LANGUAGES`), `api_language_test.py` |
| `scoring-progress` | `static/scoring_status.js`, `levels` in `/start` (`audio.py`), a few lines of `audio.css`, one `<script>` line per page, `scoring_status_test.py`, `audio_levels_test.py` |
| `capstone` | all of the above merged, plus this folder |

## Running it

```bash
pip install -r requirements.txt          # jieba is the only new package
pytest --ignore=asr_test.py --ignore=offline_asr_test.py \
       --ignore=offline_asr_whisper_test.py   # the ASR tests need torch/whisper

# Keyboard tests run in a real browser; they skip themselves without Playwright.
pip install playwright && playwright install chromium
pytest scoring_keys_test.py scoring_status_test.py

# How close is automatic splitting to the hand-split AzBio lists?
python3 segment_mandarin.py --input metadata/azbio_mandarin_transcript.csv --evaluate

# Split a new list; read the review CSV before it replaces anything.
python3 segment_mandarin.py --input mspsen_transcript.csv \
    --output mspsen_split.csv --review mspsen_review.csv
```

To try the shortcuts by hand without the server: `python3 -m http.server -d static`,
open `azbio_mandarin.html`, and in the browser console run
`audio.options("我 知道 一家 很棒的 小店")`.

## The system: where each part runs

```text
 Google Drive "Web_Audio" ──copy──► static/audio/*.wav  (not in git)
                                          │
 Browser (subject, rater) ◄───────────────┤   test pages + scoring_keys.js
   one <script> line per page             │   + scoring_status.js
                                          │
 Lab server /var/www/jnd ─────────────────┘
   Flask under uwsgi (nohup sh server.sh), api.py, audio.py
   experiments.db (SQLite): users, trials, replies, scores
   nightly.sh: offline_asr.py, then a dated copy of experiments.db to the lab drive

 Anyone's laptop (never touches the server)
   segment_mandarin.py ─► review CSV ─► native speaker ─► metadata/mandarin_overrides.csv
                      └─► new transcript CSV ─► metadata/ + projects.py (a NEW project)
```

- **In the browser:** `scoring_keys.js`, `scoring_status.js`. They reach users only
  when the lab deploys `static/`.
- **On the server, in every request:** the "Default" language fix (`api.py`) and the
  `levels` field of `/start` (`audio.py`).
- **Offline:** `segment_mandarin.py`. Its output goes live only as a new transcript
  and a new project.
- **How code gets to the server:** through pull requests to the lab's `main`; the lab
  (Malcolm) pulls and restarts the server. Nothing in this fork runs on the live
  site until a pull request is merged (open: #18).

## What cannot be rebuilt

- **The subjects' recordings and every score in `experiments.db`.** They belong to
  the lab; the only copy is the nightly database file on the lab drive. Nothing in
  this project writes to them, and no existing list may change under them:
  `transcripts_frozen_test.py` fails if any `metadata/*_transcript.csv` differs from
  `metadata/transcripts.sha256`.
- **Decisions people make:** which particles join the word before them (today
  `--attach`, default `DEFAULT_ATTACH`), the native speaker's fixes, and the
  hand-split AzBio Mandarin lists used as a reference. The fixes go in git, in
  `metadata/mandarin_overrides.csv` (`sentence,words,checked_by,date`), so GitHub is
  the backup and every change has a history.
- Everything else (code, splits, review CSVs) is rebuilt from git with one command.

## Review findings (7a) and what I did

| Finding | Done, or answer and reason |
| --- | --- |
| R1: the splitter takes 0.38 s; the time goes to people | Agreed. Timing one session by mouse and by keys needs a rater and real audio; I will do it with the first subjects (M2), not now. |
| R1: no drawing of the system | Built: "The system" above. |
| R1: how code reaches the server is not written down | Built: last line of "The system". |
| R1: the audio comes from Google Drive, not git | Built: in the drawing. |
| R1: the database and recordings cannot be rebuilt | Built: "What cannot be rebuilt". |
| R1: a boundary: re-split lists only as new projects | Built: `transcripts_frozen_test.py` + `metadata/transcripts.sha256` (12 tests; a changed or new transcript fails). |
| R2: sort the review CSV, checks first | Built: `write_review` puts `check` rows first, then changed, then unchanged; nothing is dropped. Test added. |
| R2: say where each part runs | Built: the list under the drawing. |
| R2: keep the native speaker's fixes in git, with who and when | Built: `metadata/mandarin_overrides.csv` (header only until the review starts); a test reads it. |
| R2: one settings file for the word convention | Partly: `--attach` stays a flag until the lab agrees on the convention; then the particle list moves into the overrides file and the flag only reads it. |

## Top risks

1. **The MSPSEN and BKB-SIN lists live only on the server**, not in GitHub. Asked the
   lab where they are; until then the splitter is tested on AzBio Mandarin.
2. **What counts as one word is a lab decision**, not a program's. The splitter
   follows the AzBio convention (particles such as 的/了/吧 stay with the word before
   them); the lab has to agree before any list is changed, and a native speaker
   checks every changed sentence.
3. **Changing a list changes the scores.** Re-split lists should be uploaded as new
   lists, with old results kept as they were, so the paper's numbers stay traceable.
