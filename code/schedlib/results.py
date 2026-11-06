"""Save and load solver results, so that every console output and every
figure of an example come from the *same* solution.

Many scheduling problems have several optimal solutions, and a
multi-worker or time-limited solver may return a different one on each
run.  The example scripts therefore save what they print, and the
figure scripts draw what was saved.
"""
import json
from pathlib import Path

from .core import Task

RESULTS = Path(__file__).resolve().parents[2] / "results"


def save(name, data, overwrite=False):
    """Write `data` (JSON-compatible, Task lists allowed) to results/.

    An existing file is kept unless overwrite=True: it is the reference
    solution shown in the book, and the figures are drawn from it.
    Delete the file (or pass overwrite=True) to store a new solution.
    """
    def enc(x):
        if isinstance(x, Task):
            return {"__task__": [x.job, x.resource, x.start, x.end]}
        raise TypeError(type(x))
    path = RESULTS / f"{name}.json"
    if path.exists() and not overwrite:
        return
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{name}.json").write_text(json.dumps(data, default=enc,
                                                     indent=1))


def load(name):
    """Read results/<name>.json, or return None if it does not exist."""
    path = RESULTS / f"{name}.json"
    if not path.exists():
        return None

    def dec(d):
        return Task(*d["__task__"]) if "__task__" in d else d
    return json.loads(path.read_text(), object_hook=dec)
