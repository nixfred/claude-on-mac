#!/usr/bin/env python3
"""chat.is_filtered: 0 inbox, 1 unknown senders, 2 Spam.

The iPhone badge ignores 1 and 2. Blip counted them until --hide-spam /
--hide-unknown. The predicate is the whole feature; the queries AND it in.
"""
from __future__ import annotations

import sys
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import SimpleNamespace

IMSG = Path(__file__).resolve().parents[1] / "bin" / "imsg"


def load_imsg():
    loader = SourceFileLoader("blip_imsg_filtered", str(IMSG))
    spec = spec_from_loader(loader.name, loader)
    assert spec is not None
    mod = module_from_spec(spec)
    sys.modules[loader.name] = mod
    loader.exec_module(mod)
    return mod


class Predicate(unittest.TestCase):
    def setUp(self) -> None:
        self.fn = load_imsg().filtered_chat_predicate

    def test_off_is_empty(self) -> None:
        self.assertEqual(self.fn(False, False, True), "")

    def test_no_column_is_empty_even_when_asked(self) -> None:
        self.assertEqual(self.fn(True, True, False), "")

    def test_spam_skips_2(self) -> None:
        sql = self.fn(True, False, True)
        self.assertIn("NOT IN (2)", sql)
        self.assertNotIn("1", sql)
        self.assertIn("c.ROWID IS NULL", sql)

    def test_unknown_skips_1(self) -> None:
        sql = self.fn(False, True, True)
        self.assertIn("NOT IN (1)", sql)
        self.assertNotIn("2", sql)

    def test_both_skip_1_and_2(self) -> None:
        sql = self.fn(True, True, True)
        self.assertIn("NOT IN (1, 2)", sql)


class ClauseGlue(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_imsg()

    def test_no_flags_no_sql(self) -> None:
        args = SimpleNamespace(hide_spam=False, hide_unknown=False)
        self.mod._CHAT_COLS = {"guid"}  # schema without is_filtered
        self.assertEqual(self.mod.chat_filter_sql(None, args, already_where=False), "")

    def test_where_vs_and(self) -> None:
        args = SimpleNamespace(hide_spam=True, hide_unknown=False)
        self.mod._CHAT_COLS = {"is_filtered"}
        where = self.mod.chat_filter_sql(None, args, already_where=False)
        anda = self.mod.chat_filter_sql(None, args, already_where=True)
        self.assertTrue(where.startswith(" WHERE "))
        self.assertTrue(anda.startswith(" AND "))
        self.assertIn("NOT IN (2)", where)


if __name__ == "__main__":
    unittest.main()
