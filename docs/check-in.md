# Capstone check-in

**Plan:** [capstone/PROMPT.md](../capstone/PROMPT.md) (milestones M1–M4) and
[capstone/README.md](../capstone/README.md), branch `capstone` of
https://github.com/yunqilu/SpeechInNoise. The plan of 12 October was the Kunqu
project; I switched to this one in 5b (plan at commit `0796293`), with the
instructor's agreement. This check-in describes commit `1cae81b`.

## What works

All commands run from the repository root at `1cae81b`. The ASR tests (`asr_test.py`,
`offline_asr_test.py`, `offline_asr_whisper_test.py`) need Whisper and are left out.

- **Whole suite:** `pytest --ignore=asr_test.py --ignore=offline_asr_test.py
  --ignore=offline_asr_whisper_test.py` → `112 passed`.
- **Keyboard scoring (M1):** `pytest scoring_keys_test.py` → `9 passed` (headless
  Chrome on the real `azbio_mandarin.html`; needs Playwright).
- **List position and words scored on the test pages (new):**
  `pytest scoring_status_test.py audio_levels_test.py` → `20 passed`. The header shows
  "List 1 · Sentence 3 of 20 · 10 dB SNR"; under All / None, "2 of 7 words scored ·
  1 correct". Figure: [docs/scoring-page.png](scoring-page.png) (taken in headless
  Chrome without the server, so the icon font shows as the text "mic_off").
- **Splitting Mandarin answers into scoring words (M1):**
  `python3 segment_mandarin.py --input metadata/azbio_mandarin_transcript.csv --evaluate`
  → `40 sentences, boundary precision 0.944, recall 0.926, F1 0.935, exactly the same
  50.0%`; `pytest segment_mandarin_test.py` → `15 passed`.
- **"Default" list fix for Spanish and Mandarin:** `pytest api_language_test.py` →
  `5 passed`.
- **Old lists cannot change (from the 7a review):** `pytest transcripts_frozen_test.py`
  → `12 passed`. Appending one line to `metadata/cnc_transcript.csv` makes
  `test_transcript_is_unchanged[cnc_transcript.csv]` fail.
- **Re-split MSPSEN and BKB-SIN (M2), in progress:** I got both lists from the lab and
  split them: 232 sentences, of which 203 change. They are the lab's data and are not
  in the repository yet; the native-speaker review has not started (0 of 232 checked).

## What failed, and what I learned

I expected the splitter to reproduce the hand-split AzBio Mandarin lists, so that a
high F1 would mean "correct". It does not: F1 is 0.935, but only 50 % of the sentences
match exactly (output above). Reading the 20 disagreements, some are the hand split
disagreeing with itself (很高兴 is one word, 不 规则的 is two), and some are real
mistakes of the program (期限得 加班了, where 得 means "must"; 这 周 轮 到 instead of
这周 轮到). So F1 against the hand split partly measures the reference's own noise, and
no number can tell me the split is right. What I changed: the splitter only proposes;
a native speaker confirms every changed sentence, and the fixes go into
`metadata/mandarin_overrides.csv` in git. Because 203 of 232 MSPSEN/BKB-SIN sentences
change, that review is the slow step, so the review CSV now lists the rows to check
first.

## What I am cutting, and why

- **M4 (one CSV per subject, L1 Chinese vs L1 English):** cut. No subject has been
  tested on the Mandarin lists yet; the lab's priority now is recruiting at least two
  normal-hearing listeners in each group, so there is no data to summarise by
  30 November.
- **M3 (how well the recognizer scores Mandarin):** only if the lab can export the
  recognizer's Mandarin transcripts by 23 November; the output is on the server, not
  in the repository. Otherwise it is cut too.
- The draft will still claim: *a Mandarin sentence gets the same scoring words in every
  list, checked by a native speaker, and a rater can score it from the keyboard and see
  where they are in the list, without any existing list or score changing.*

## Built to throw away, and built to last

- **Throw away:** the test `test_matches_the_hand_split_azbio_lists`, which passes
  when F1 ≥ 0.9. It is fine for now because it catches a broken jieba install, but
  today's F1 is 0.935, so a change that makes 3 % of the boundaries worse would still
  pass. Before the write-up I will replace it with a golden file of today's 40 splits
  that fails on any difference.
- **Keep:** the word lists themselves: the existing transcripts in `metadata/` and the
  native speaker's fixes in `metadata/mandarin_overrides.csv`. Tested by
  `transcripts_frozen_test.py` (any change to an existing list, or a new list without
  its checksum, fails) and `test_committed_overrides_file_is_read`. Documented in
  [capstone/README.md](../capstone/README.md), "What cannot be rebuilt".
