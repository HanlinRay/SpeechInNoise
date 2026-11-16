"""The /start response tells the page how many audios the list has.

Runs the real API on a fresh database in a temporary folder, through Flask's
test client, so it checks the route the test pages call, not only a helper.
"""
import json
import warnings

import pytest
from flask import Flask

from api import APIBlueprint


@pytest.fixture
def client(tmp_path):
    app = Flask(__name__)
    app.secret_key = "test"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # audio files are not in the repo
        app.register_blueprint(APIBlueprint(db_path=str(tmp_path / "e.db")))
    return app.test_client()


def start(client, project, requested):
    client.get(f"/set-username?v=test-levels&project={project}"
               f"&list={requested}")
    response = client.get(f"/{project}/start")
    assert response.status_code == 200
    return json.loads(response.data)


@pytest.mark.parametrize("project, requested, levels", [
    ("azbio_mandarin", "zh-1", 20),
    ("azbio", "en-6", 20),
    ("cnc", "en-1", 50),
    ("quick", "en-1", 6),
])
def test_start_gives_the_number_of_audios_in_the_list(
        client, project, requested, levels):
    assert start(client, project, requested)["levels"] == levels


def test_reloading_the_page_gives_it_again(client):
    first = start(client, "azbio_mandarin", "zh-1")
    again = json.loads(client.get("/azbio_mandarin/start").data)
    assert again["cur"] == first["cur"]
    assert again["levels"] == 20


def test_start_keeps_every_field_it_had(client):
    data = start(client, "azbio_mandarin", "zh-1")
    assert {"cur", "next", "name", "has_results", "answer"} <= set(data)
