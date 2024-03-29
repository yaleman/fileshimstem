""" testing fileshimstem """
import tempfile
import json
from pathlib import Path
# import pytest

# from fastapi import FastAPI
from fastapi.testclient import TestClient

import fileshimstem


def test_read_main() -> None:
    """ tests the basic home page, does it load etc """
    client = TestClient(fileshimstem.app)
    response = client.get("/")
    if not response.status_code == 200:
        print("CONTENT: ")
        print(response.content)
    assert response.status_code == 200
    assert "FastAPI - Swagger UI" in response.text

def test_read_banned() -> None:
    """ tests if it raises a 403 on accessing a banned dir """
    with tempfile.TemporaryDirectory(prefix="fss_banned") as bad_dir:
        app = fileshimstem.app
        app.config = fileshimstem.ConfigFile(goodpaths = [])
        client = TestClient(app)
        response = client.get(bad_dir)
        if not response.status_code == 403:
            print("CONTENT:")
            print(response.content)
        assert response.status_code == 403

def test_read_ok() -> None:
    """ tests an ok dir """
    app = fileshimstem.app

    client = TestClient(app)

    with tempfile.TemporaryDirectory(prefix="fss_ok") as ok_tempdir:
        tempdir_string = str(Path(ok_tempdir).resolve())
        app.config = fileshimstem.ConfigFile(goodpaths = [tempdir_string])
        print(json.dumps(app.config.goodpaths))
        testdir = f"{tempdir_string}/"
        print(f"Pulling from {testdir}")
        response = client.get(testdir)
        print("response content:")
        print(response.content)
        assert response.status_code == 200
