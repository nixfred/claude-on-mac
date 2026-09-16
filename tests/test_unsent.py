#!/usr/bin/env python3
"""Regression: on macOS 26 an Undo Send never sets date_retracted. It stamps
date_edited, clears the body, and lists the withdrawn parts as `rp` in
message_summary_info. Read only the dates and every unsend since January 2026
is an empty bubble tagged "Edited"; the tombstone never shows."""
from __future__ import annotations

import plistlib
import sys
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

IMSG = Path(__file__).resolve().parents[1] / "bin" / "imsg"


def load_imsg():
    loader = SourceFileLoader("blip_imsg", str(IMSG))
    spec = spec_from_loader(loader.name, loader)
    assert spec is not None
    mod = module_from_spec(spec)
    sys.modules[loader.name] = mod
    loader.exec_module(mod)
    return mod


# The two shapes seen on a real macOS 26 chat.db, keys as Apple writes them.
UNSENT = plistlib.dumps({"amc": 1, "ust": False, "otr": {"0": b"\x00"}, "rp": [0]}, fmt=plistlib.FMT_BINARY)
EDITED = plistlib.dumps({"amc": 1, "ust": False, "otr": {"0": b"\x00"}, "ec": {"0": [{"d": 1.0, "t": b"\x00"}]}, "ep": [0]},
                        fmt=plistlib.FMT_BINARY)
STAMP = 800_000_000_000_000_000   # a date_edited value (ns since 2001); any non-zero will do


class Unsent(unittest.TestCase):
    def setUp(self) -> None:
        self.unsent = load_imsg()._unsent

    def test_rp_means_unsent(self) -> None:
        self.assertTrue(self.unsent(UNSENT))

    def test_a_real_edit_is_not_unsent(self) -> None:
        self.assertFalse(self.unsent(EDITED))

    def test_missing_or_broken_blobs_are_not_unsent(self) -> None:
        for blob in (None, b"", b"not a plist", plistlib.dumps({"rp": []}), plistlib.dumps(["rp"])):
            self.assertFalse(self.unsent(blob), repr(blob)[:24])


class EditFlags(unittest.TestCase):
    def setUp(self) -> None:
        self.flags = load_imsg()._edit_flags

    def test_macos_26_unsend_is_retracted_not_edited(self) -> None:
        # date_edited stamped, date_retracted 0, rp in the summary: what Undo Send writes now
        self.assertEqual(self.flags(STAMP, 0, UNSENT), {"retracted": True})

    def test_older_macos_unsend_still_works(self) -> None:
        self.assertEqual(self.flags(0, STAMP, None), {"retracted": True})
        self.assertEqual(self.flags(STAMP, STAMP, None), {"retracted": True})

    def test_a_real_edit_is_edited(self) -> None:
        self.assertEqual(self.flags(STAMP, 0, EDITED), {"edited": True})
        self.assertEqual(self.flags(STAMP, 0, None), {"edited": True})

    def test_an_untouched_message_has_no_flags(self) -> None:
        self.assertEqual(self.flags(0, 0, None), {})
        self.assertEqual(self.flags(None, None, b""), {})


if __name__ == "__main__":
    unittest.main()
