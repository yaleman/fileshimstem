""" testing fileshimstem """
import tempfile
import json
from pathlib import Path
# import pytest

# from fastapi import FastAPI
from fastapi.testclient import TestClient

import fileshimstem


def test_read_main():
    """ tests the basic home page, does it load etc """
    client = TestClient(fileshimstem.app)
    response = client.get("/")
    if not response.status_code == 200:
        print(f"CONTENT: {response.content}")
    assert response.status_code == 200
    assert "FastAPI - Swagger UI" in response.text

def test_read_banned():
    """ tests if it raises a 403 on accessing a banned dir """
    with tempfile.TemporaryDirectory(prefix="fss_banned") as bad_dir:
        client = TestClient(fileshimstem.app)
        response = client.get(bad_dir.name)

        if not response.status_code == 403:
            print(f"CONTENT: {response.content}")
        assert response.status_code == 403

def test_read_ok():
    """ tests an ok dir """
    app = fileshimstem.app
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
