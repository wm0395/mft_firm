from __future__ import annotations

import collections
import collections.abc


if not hasattr(collections, "Hashable"):
    collections.Hashable = collections.abc.Hashable
