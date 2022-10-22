#!/usr/bin/env python3

""" just runs the cli """

import uvicorn

from fileshimstem import app

def run() -> None:
    """ just does the thing """

    config = app.load_config()

    if config is None:
        return

    uvicorn.run(
        "fileshimstem:app",
        host=config.host,
        port=config.port,
        log_level="debug",
        reload=True,
    )

if __name__ == "__main__":
    run()
