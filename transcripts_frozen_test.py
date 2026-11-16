"""Existing test lists never change; a re-split list comes in as a new list.

Scores already in the lab's database were made against the words in these
files, so editing one would silently change what old results mean. This test
compares every metadata/*_transcript.csv with the checksums recorded in
metadata/transcripts.sha256.

- A changed file fails: put the change in a new transcript and a new project
  in projects.py instead.
- A new file fails until its checksum is added, so adding a list is a decision
  someone makes on purpose:

    cd metadata && sha256sum NEW_transcript.csv >> transcripts.sha256

Only for a deliberate correction agreed with the lab: re-record the line for
that file in the same commit, and say why in the commit message.
"""
import hashlib
import pathlib

import pytest

from storage import relpath

METADATA = pathlib.Path(relpath("metadata"))


def recorded():
    lines = (METADATA / "transcripts.sha256").read_text().splitlines()
    return {name: digest for digest, name in
            (line.split(maxsplit=1) for line in lines if line.strip())}


def on_disk():
    return sorted(p.name for p in METADATA.glob("*_transcript.csv"))


@pytest.mark.parametrize("name", on_disk())
def test_transcript_is_unchanged(name):
    expected = recorded()
    assert name in expected, (
        f"{name} is new: add its checksum to metadata/transcripts.sha256")
    digest = hashlib.sha256((METADATA / name).read_bytes()).hexdigest()
    assert digest == expected[name], (
        f"{name} changed. Old scores were made against it: add the new "
        "version as a new transcript and project instead.")


def test_every_recorded_transcript_still_exists():
    missing = set(recorded()) - set(on_disk())
    assert not missing, f"removed from metadata/: {sorted(missing)}"
