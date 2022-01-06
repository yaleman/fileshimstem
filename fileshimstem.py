#!/usr/bin/env python3

import json

import os

from pathlib import PosixPath, WindowsPath

import uvicorn
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

if os.name == "posix":
    pathtype = PosixPath
    PATHPREFIX = "/"
elif os.name == "nt":
    pathtype = WindowsPath
    PATHPREFIX = ""
else:
    sys.exit("Couldn't work out what kind of path to use")

with open("config.json", encoding="utf8") as fh:
    config = json.load(fh)

@app.get("/")
async def root():
    return {"message" : "Hello world"}

def check_path_allowed(fullpath):
    """ checks if it's valid, returns True if it is, and guess what if not"""
    for path in config.get("goodpaths"):
        print(path, fullpath)
        if str(fullpath).startswith(path):
            return True
    return False

def build_headers(headers, stat):
    """ updates the headers """
    for attr in dir(stat):
        if attr.startswith("st_"):
            headers[attr.lstrip("st_")] = str(getattr(stat, attr))
    headers["type"] = "dir"


@app.head('/{subpath:path}')
async def head_show_subpath(subpath, response: Response):
    """ head method """
    fullpath = pathtype(f"{PATHPREFIX}{subpath.lstrip('/')}")

    if not check_path_allowed(fullpath):
        raise HTTPException(status_code=403, detail={"message": "Item not allowed"})
    if not fullpath.exists():
        raise HTTPException(status_code=404, detail={"message": "Item not found"})

    if fullpath.is_dir():
        stat = fullpath.stat()
        build_headers(response.headers, stat)
        response.headers["type"] = "dir"
    elif fullpath.is_file:
        stat = fullpath.stat()
        build_headers(response.headers, stat)
        response.headers["type"] = "file"
    return ""
    # raise HTTPException(status_code=500, detail={"message": "I can't even"})

@app.get('/{subpath:path}') #
async def get_show_subpath(subpath, response: Response):
    """ get method """
    fullpath = pathtype(f"{PATHPREFIX}{subpath.lstrip('/')}")

    if not check_path_allowed(fullpath):
        raise HTTPException(status_code=403, detail={"message": "Item not allowed"})
    if not fullpath.exists():
        raise HTTPException(status_code=404, detail={"message": "Item not found"})



    if fullpath.is_file:
        stat = fullpath.stat()
        build_headers(response.headers, stat)

        response.headers["type"] = "file"
        return FileResponse(fullpath)
    else:
        return FileNotFoundError


if __name__ == "__main__":
    uvicorn.run(
        "fileshimstem:app",
        host=config.get("host", "127.0.0.1"),
        port=config.get("port", 8000),
        log_level="debug",
    )
