"""Local interpreter workarounds for repo tooling.

Pytest imports ``readline`` very early during startup as part of its capture
initialization on macOS/libedit environments. In this workspace, importing the
native ``readline`` extension from the active Python 3.12.9 build segfaults.

To keep local test execution usable, install a minimal stub before pytest tries
to import ``readline``. The benchmark code does not depend on readline APIs.
"""

from __future__ import annotations

import os
import sys
import types


if sys.platform == "darwin" and os.environ.get("RECSYS_GEN_STUB_READLINE", "1") == "1":
    sys.modules.setdefault("readline", types.ModuleType("readline"))
