
import tempfile
import json
from pathlib import Path
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import fileshimstem


@pytest.fixture
def app():
    """ app fixture for testing """
    return fileshimstem.app


@pytest.fixture(scope="module")
def bad_dir():
    """ bad dir to grab"""
    return tempfile.TemporaryDirectory(prefix="fss_banned")

def test_read_main(app):
    client = TestClient(app)
    response = client.get("/")
    if not response.status_code == 200:
        print(f"CONTENT: {response.content}")
    assert response.status_code == 200
    assert "FastAPI - Swagger UI" in response.text

def test_read_banned(app, bad_dir):
    client = TestClient(app)
    response = client.get(bad_dir.name)

    if not response.status_code == 403:
        print(f"CONTENT: {response.content}")
    assert response.status_code == 403

def test_read_ok(app):
    """ tests an ok dir """
    client = TestClient(app)

    with tempfile.TemporaryDirectory(prefix="fss_ok") as ok_tempdir:
        tempdir_string = str(Path(ok_tempdir).resolve())
        app.config["goodpaths"] = [
            tempdir_string
        ]
        print(json.dumps(app.config.get('goodpaths')))
        testdir = f"{tempdir_string}/"
        print(f"Pulling from {testdir}")
        response = client.get(testdir)
        print(f"response content: {response.content}")
        assert response.status_code == 200
