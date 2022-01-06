#!/usr/bin/env python3

import json

import os

from pathlib import Path, PosixPath, WindowsPath

from flask import Flask, abort
from markupsafe import escape


app = Flask(__name__)

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

@app.route('/<path:subpath>')
def show_subpath(subpath):
    # show the subpath after /path/
    fullpath = pathtype(f"{PATHPREFIX}{subpath}")
    app.logger.info(fullpath)
    print(fullpath)

    if not fullpath.exists():
        return 404

    good = False
    for path in config.get("goodpaths"):
        if str(fullpath).startswith(path):
            good = True
    if not good:
        abort(403)


    if fullpath.is_file:
        # return json.dumps(, default=str)
        stat = fullpath.stat()
        data = {
            "type" : "file",
        }
        for attr in dir(stat):
            if attr.startswith("st_"):
                data[attr.lstrip("st_")] = getattr(stat, attr)
        return json.dumps(data, default=str, indent=4)


app.run()