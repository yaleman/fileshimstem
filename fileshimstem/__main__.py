#!/usr/bin/env python3

""" just runs the cli """

import uvicorn # type: ignore

from fileshimstem import app

def run():
    """ just does the thing """

    config = app.load_config()

    uvicorn.run(
        "fileshimstem:app",
        host=config.get("host", "127.0.0.1"),
        port=config.get("port", 8000),
        log_level="debug",
        reload=True,
    )

if __name__ == "__main__":
    run()
