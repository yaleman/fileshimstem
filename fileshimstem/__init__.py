""" fileshimstem - a terrible way to expose a filesystem over the network

    still better than using SMB for my macbook, I guess.

"""

import json
from json.decoder import JSONDecodeError

import os
from pathlib import Path#, WindowsPath
import sys
from typing import Any, Dict, Optional, List, Union
import urllib.parse

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.datastructures import MutableHeaders
from starlette.responses import RedirectResponse

from git import Repo # type: ignore


class ConfigFile(BaseModel):
    """pydantic-based config file def"""
    goodpaths: List[str]
    host: str="127.0.0.1"
    port: int=8080

class FileShimStem(FastAPI):
    """ A silly shim between my filesystem and HTTP """

    def __init__(
        self,
        config: Optional[ConfigFile] = None):
        """ overloaded init """
        super().__init__()

        if not config:
            self.load_config()
        else:
            self.config = config


        if os.name == "posix":
            self.pathprefix = "/"
        elif os.name == "nt":
            self.pathprefix = ""
        else:
            sys.exit("Couldn't work out what kind of path to use")

    def load_config(self, config_file: Optional[List[str]]=None) -> Optional[ConfigFile]:
        """ loads the config"""
        if config_file:
            configpaths = config_file
        else:
            configpaths = [
                "~/.config/fileshimstem.json",
                "./fileshimstem.json",
            ]
        for filepath in configpaths:
            config_path = Path(filepath).expanduser().resolve()
            if config_path.exists():
                try:
                    config = ConfigFile.parse_file(config_path)
                    self.config = config
                    return config
                except JSONDecodeError as json_error:
                    print(f"Failed to load config: {json_error}", file=sys.stderr)
        return None

    def check_path_allowed(self, fullpath: Path) -> bool:
        """ checks if it's valid, returns True if it is, and guess what if not"""
        if not self.config.goodpaths:
            print("Can't possibly work, no goodpaths set", file=sys.stderr)
            return False
        fullpath_path = fullpath.resolve()
        for path in self.config.goodpaths:
            # print(json.dumps({
            #     "function" : "check_path_allowed",
            #     "test_case" : fullpath_path,
            #     "test_conf" : path,
            #     }, indent=4, default=str
            #     ), file=sys.stderr)
            if str(fullpath_path).startswith(path):
                return True
        return False
app = FileShimStem()




def build_headers(headers: MutableHeaders, stat: os.stat_result) -> None:
    """ updates the headers """
    for attr in dir(stat):
        if attr.startswith("st_"):
            headers[attr.lstrip("st_")] = str(getattr(stat, attr))
    headers["type"] = "dir"

@app.get("/", response_model=None)
async def root() -> RedirectResponse:
    """ redirects root to docs """
    return RedirectResponse("/docs")


def parse_path(path: str) -> Path:
    """ unfucks urlencoded paths """
    unquoted = urllib.parse.unquote_plus(f"{app.pathprefix}{path.lstrip('/')}")
    with_pluses = unquoted.replace("&#43;", "+")
    return Path(with_pluses)

@app.head('/{subpath:path}', response_model=None)
async def head_show_subpath(
    subpath: str,
    response: Response,
    ) -> Response:
    """ head method """
    fullpath = parse_path(subpath)

    if not app.check_path_allowed(fullpath):
        raise HTTPException(status_code=403, detail={"message": "Item not allowed"})
    if not fullpath.exists():
        print(f"File not found: {fullpath}", file=sys.stderr)
        raise HTTPException(status_code=404, detail={"message": f"File not found: {fullpath}"})

    if fullpath.is_dir():
        stat = fullpath.stat()
        build_headers(response.headers, stat)
        response.headers["type"] = "dir"
    elif fullpath.is_file():
        stat = fullpath.stat()
        build_headers(response.headers, stat)
        response.headers["type"] = "file"
    return Response("")
    # raise HTTPException(status_code=500, detail={"message": "I can't even"})

class FileList(BaseModel):
    """ list of files """
    files: List[str]

@app.get('/{subpath:path}', response_model=None) #
async def get_show_subpath(
    subpath: str,
    response: Response,
    ) -> Union[FileList, FileResponse]:
    """ get method """
    fullpath = parse_path(subpath)
    # print(fullpath, file=sys.stderr)
    if not app.check_path_allowed(fullpath):
        raise HTTPException(status_code=403, detail={"message": "Item not allowed"})
    if not fullpath.exists():
        print(f"File not found: {fullpath}", file=sys.stderr)
        raise HTTPException(status_code=404, detail={"message": f"File not found: {fullpath}"})

    if fullpath.is_dir():
        response.headers["type"] = "dir"
        return FileList(files=os.listdir(fullpath.resolve()))
    if fullpath.is_file():
        stat = fullpath.stat()
        build_headers(response.headers, stat)
        response.headers["type"] = "file"
        return FileResponse(fullpath)
    raise HTTPException(status_code=403, detail={"message": f"File type not supported: {fullpath}"})

class UpdateResponse(BaseModel):
    """ update response """
    message: str
    result: Dict[str, Any]

@app.options("/update")
async def update() -> UpdateResponse:
    """ does a git pull to update the code, which makes uvicorn do the thing """
    repo = Repo(".")
    print("Running update")
    config = app.load_config()

    pull = repo.remotes.origin.pull()[0]
    result = { "config" : config }

    for field in ("ref", "flags", "note", "old_commit"):
        if hasattr(pull, field):
            result[field] = getattr(pull, field)

    return UpdateResponse(message="done!", result=result)
