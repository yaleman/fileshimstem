# fileshimstem

This is pretty terrible, please don't use it.

## Configuration

Config file is `fileshimstem.json`, it can be where you run the script from, or in `~/.config/fileshimstem.json`.

| Option | Type | Default | Description |
| --- |  --- | --- | --- |
| `goodpaths` | `List[str]` | `None` | Needs to be set, is the list of allowed paths for requests. |
| `port` | `int` | 8000 | The port the server will listen on. |
| `host` | `str` | 127.0.0.1 | The host the server will listen on - 0.0.0.0 allows all IPv4 etc. |

## API Docs

Access `/docs` when running the server, but simply:

# GET /{path}

eg: `curl http://localhost:8000/e:/Downloads/filename.txt`

Gets the file contents.

# HEAD /{path} 

eg: `curl -X HEAD http://localhost:8000/e:/Downloads/filename.txt`

Does a stat and returns the details in the headers.

# OPTIONS /update

Does a `git pull` and updates the server configuration.
