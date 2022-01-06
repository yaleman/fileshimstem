#!/usr/bin/env python3

import json

import os

from pathlib import PosixPath, WindowsPath

from flask import Flask, abort, request, send_file, Response
# from markupsafe import escape


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

@app.route('/<path:subpath>', methods=["GET", "HEAD"])
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
        if request.method == "HEAD":
            stat = fullpath.stat()
            response = Response("")
            for attr in dir(stat):
                if attr.startswith("st_"):
                    response.headers[attr.lstrip("st_")] = getattr(stat, attr)

            response.headers["File-Type"] = "file"
            return response

        elif request.method == "GET":
            return send_file(fullpath)
    abort(500)

app.run(host=config.get("host", "127.0.0.1"), port=config.get("port", 5000))