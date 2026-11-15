"""Write the FastAPI openapi.json used by Hey API (`just gen-api`)."""

import json
import sys
from pathlib import Path

from app.main import app


def main(out: str) -> None:
    Path(out).write_text(json.dumps(app.openapi(), indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
