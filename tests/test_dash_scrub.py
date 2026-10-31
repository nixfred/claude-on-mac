#!/usr/bin/env python3
"""The no-dashes scrub removes dashes and nothing else.

`scrub_dashes` lives in both send helpers (`imsg-send` and `mail-send`) and the
two copies must behave the same, so one table of cases runs against both.
Reported in issue #8: the first version rewrote `--` inside flags and URLs,
turned the `-- ` signature separator into `, `, and (because `\\s` matches a
newline) swallowed the line breaks around any dash. It also collapsed commas the
author had typed, across blank lines.
"""
from __future__ import annotations

import sys
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "bin"

EM = chr(0x2014)
EN = chr(0x2013)
BAR = chr(0x2015)


def load(tool: str):
    name = "dashscrub_" + tool.replace("-", "_")
    loader = SourceFileLoader(name, str(HERE / tool))
    spec = spec_from_loader(loader.name, loader)
    assert spec is not None
    mod = module_from_spec(spec)
    sys.modules[name] = mod
    loader.exec_module(mod)
    return mod


# (label, input, expected output, expected count)
CASES = [
    # --- things that are not dashes: left exactly as typed ---
    ("command flag", "run git log --oneline now", "run git log --oneline now", 0),
    ("flag at line start", "--verbose is on", "--verbose is on", 0),
    ("url slug", "see https://example.com/a--b ok", "see https://example.com/a--b ok", 0),
    ("glued word--word", "a--b", "a--b", 0),
    ("signature separator", "Thanks\n\n-- \nFred", "Thanks\n\n-- \nFred", 0),
    ("signature separator, no space", "Thanks\n--\nFred", "Thanks\n--\nFred", 0),
    ("signature separator, CRLF", "Thanks\r\n-- \r\nFred", "Thanks\r\n-- \r\nFred", 0),
    ("typed commas", "a,,b", "a,,b", 0),
    ("commas across blank lines", "ok,\n\n,next", "ok,\n\n,next", 0),
    ("plain hyphen", "well-known x-ray", "well-known x-ray", 0),
    # --- real dashes: scrubbed ---
    ("em dash", "wait " + EM + " what", "wait, what", 1),
    ("em dash, no spaces", "wait" + EM + "what", "wait, what", 1),
    ("en dash", "wait " + EN + " what", "wait, what", 1),
    ("horizontal bar", "wait " + BAR + " what", "wait, what", 1),
    ("spaced double hyphen", "wait -- what", "wait, what", 1),
    ("two dashes in a line", "a " + EM + " b " + EM + " c", "a, b, c", 2),
    ("dash after a comma", "wait, " + EM + " what", "wait, what", 1),
    ("dash ends the line", "tail " + EM, "tail,", 1),
    ("dash ends the line, then more text", "foo " + EM + "\nbar", "foo,\nbar", 1),
    ("double hyphen ends the line", "ok --", "ok,", 1),
    # --- line breaks around a dash survive ---
    ("blank line before a dash line", "a\n\n" + EM + " b", "a\n\n- b", 1),
    # --- a dash that opens a line keeps a list a list ---
    ("em dash list", "Agenda:\n" + EM + " one\n" + EM + " two", "Agenda:\n- one\n- two", 2),
    ("em dash list, glued", "Agenda:\n" + EM + "one", "Agenda:\n- one", 1),
    ("indented list", "  " + EM + " item", "  - item", 1),
    ("double hyphen list item", "-- note", "- note", 1),
    # --- a mixed message: only the real dash goes ---
    (
        "mixed",
        "Use git log --oneline " + EM + " see https://example.com/a--b\n\n-- \nFred",
        "Use git log --oneline, see https://example.com/a--b\n\n-- \nFred",
        1,
    ),
    ("typed commas next to a real dash", "a,,b " + EM + " c", "a,,b, c", 1),
]


class DashScrubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = {t: load(t) for t in ("imsg-send", "mail-send")}

    def test_cases_on_both_copies(self):
        for tool, mod in self.tools.items():
            for label, given, want, want_n in CASES:
                with self.subTest(tool=tool, case=label):
                    got, n = mod.scrub_dashes(given)
                    self.assertEqual(got, want)
                    self.assertEqual(n, want_n)

    def test_the_two_copies_agree(self):
        a, b = (m.scrub_dashes for m in self.tools.values())
        for label, given, _, _ in CASES:
            with self.subTest(case=label):
                self.assertEqual(a(given), b(given))

    def test_clean_text_is_returned_unchanged(self):
        for tool, mod in self.tools.items():
            with self.subTest(tool=tool):
                text = "Line one.\n\nLine two, with commas,, and\ttabs.\n"
                self.assertEqual(mod.scrub_dashes(text), (text, 0))


if __name__ == "__main__":
    unittest.main()
