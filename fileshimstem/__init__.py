""" fileshimstem - a terrible way to expose a filesystem over the network

    still better than using SMB for my macbook, I guess.

"""


__version__ = "0.1.0"



import json
from json.decoder import JSONDecodeError

import os
import sys

from pathlib import Path#, WindowsPath

from typing import Union
from starlette.responses import RedirectResponse

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import FileResponse
from git import Repo


app = FastAPI()

if os.name == "posix":
    PATHPREFIX = "/"
elif os.name == "nt":
    PATHPREFIX = ""
else:
    sys.exit("Couldn't work out what kind of path to use")


def load_config(oldconfig: dict = Union[None,dict]) -> dict:
    """ loads the config"""
    for filepath in [
        "~/.config/fileshimstem.json",
        "./fileshimstem.json",
    ]:
        if os.path.exists(os.path.expanduser(filepath)):
            with open(os.path.expanduser(filepath), encoding="utf8") as config_file:
                try:
                    config = json.load(config_file)
                    return config
                except JSONDecodeError as json_error:
                    print(f"Failed to load config: {json_error}")
                    return oldconfig
    return oldconfig

CONFIG = load_config()

def check_path_allowed(fullpath: os.PathLike, config=CONFIG) -> bool:
    """ checks if it's valid, returns True if it is, and guess what if not"""
    if not config.get("goodpaths"):
        print("Can't possibly work, no goodpaths set", file=sys.stderr)
        return False
    fullpath_path = fullpath.resolve()
    for path in config.get("goodpaths"):
        # print(fullpath_path, path, file=sys.stderr)
        if str(fullpath_path).startswith(path):
            return True
    return False

def build_headers(headers, stat):
    """ updates the headers """
    for attr in dir(stat):
        if attr.startswith("st_"):
            headers[attr.lstrip("st_")] = str(getattr(stat, attr))
    headers["type"] = "dir"

@app.get("/")
async def root():
    """ redirects root to docs """
    return RedirectResponse("/docs")


@app.head('/{subpath:path}')
async def head_show_subpath(subpath, response: Response):
    """ head method """
    fullpath = Path(f"{PATHPREFIX}{subpath.lstrip('/')}")

    if not check_path_allowed(fullpath):
        raise HTTPException(status_code=403, detail={"message": "Item not allowed"})
    if not fullpath.exists():
        raise HTTPException(status_code=404, detail={"message": "Item not found"})

    if fullpath.is_dir():
        stat = fullpath.stat()
        build_headers(response.headers, stat)
        response.headers["type"] = "dir"
    elif fullpath.is_file():
        stat = fullpath.stat()
        build_headers(response.headers, stat)
        response.headers["type"] = "file"
    return ""
    # raise HTTPException(status_code=500, detail={"message": "I can't even"})

@app.get('/{subpath:path}') #
async def get_show_subpath(subpath, response: Response):
    """ get method """
    fullpath = Path(f"{PATHPREFIX}{subpath.lstrip('/')}")
    print(fullpath, file=sys.stderr)
    if not check_path_allowed(fullpath):
        raise HTTPException(status_code=403, detail={"message": "Item not allowed"})
    if not fullpath.exists():
        raise FileNotFoundError

    if fullpath.is_dir():
        response.headers["type"] = "dir"
        return {
            "files" : os.listdir(fullpath.resolve())
        }
    if fullpath.is_file():
        stat = fullpath.stat()
        build_headers(response.headers, stat)
        response.headers["type"] = "file"
        return FileResponse(fullpath)
    return FileNotFoundError

@app.options("/update")
async def update(config=CONFIG):
    """ does a git pull to update the code, which makes uvicorn do the thing """
    repo = Repo(".")
    print("Running update")
    config = load_config()
    pull = repo.remotes.origin.pull()[0]
    result = { "config" : dict(config) }

    for field in ("ref", "flags", "note", "old_commit"):
        if hasattr(pull, field):
            result[field] = str(getattr(pull, field))

    return {
        "message" : "done!",
        "result" : result,
    }
