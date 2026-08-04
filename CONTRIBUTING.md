# Contributing

## Real behavior only

Every method in this SDK wraps a real, live ForceDream API endpoint. Before
submitting a change:

- Confirm the endpoint you're wrapping actually exists and behaves as
  described, by testing against the real, live API — not by assuming from
  documentation alone.
- Do not add methods for endpoints that don't exist yet, or stub out
  behavior that looks real but isn't.
- If you're porting logic from another ForceDream SDK (JS, Go, etc.), verify
  byte-for-byte/hash-for-hash equivalence for anything involving
  cryptography or canonical serialization — a subtle formatting mismatch
  will silently break every signature check. See `verify.py` and
  `canonical.py` for the existing pattern.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Testing

There is currently no automated test suite in this repo. Test changes
manually against the live API before submitting:

```bash
python3 -c "
import asyncio
from forcedream import ForceDream

async def main():
    fd = ForceDream()
    result = await fd.search_agents(capability='summarization')
    print(result)

asyncio.run(main())
"
```

## Pull requests

Describe what you tested and against what real data. A PR that only compiles
but was never run against the live API will not be merged.
