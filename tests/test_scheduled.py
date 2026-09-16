#!/usr/bin/env python3
"""Regression: a Send Later message is written to chat.db the moment it is
scheduled, dated at the FUTURE send time (schedule_type 2, schedule_state 2 while
waiting, 3 once sent; macOS 27, 2026-09-16). Unflagged it showed as already sent,
became its conversation's newest message, and would have set a read mark a day
ahead, hiding every reply until then."""
from __future__ import annotations

import sqlite3
import sys
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

IMSG = Path(__file__).resolve().parents[1] / "bin" / "imsg"


def load_imsg():
    loader = SourceFileLoader("blip_imsg_sched", str(IMSG))
    spec = spec_from_loader(loader.name, loader)
    assert spec is not None
    mod = module_from_spec(spec)
    sys.modules[loader.name] = mod
    loader.exec_module(mod)
    return mod


class Scheduled(unittest.TestCase):
    def setUp(self) -> None:
        self.imsg = load_imsg()

    def test_only_a_waiting_send_later_is_pending(self) -> None:
        pending = self.imsg._is_pending_schedule
        self.assertTrue(pending(2, 2))
        self.assertFalse(pending(2, 3))      # already sent
        self.assertFalse(pending(0, 0))      # an ordinary message

    def test_sql_predicate_follows_the_schema(self) -> None:
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        self.imsg._COLS = None
        con.execute("CREATE TABLE message (ROWID INTEGER PRIMARY KEY, date INTEGER)")
        self.assertEqual(self.imsg.pending_schedule_sql(con), "(0 = 1)")
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        self.imsg._COLS = None
        con.execute("CREATE TABLE message (ROWID INTEGER PRIMARY KEY, schedule_type INTEGER, schedule_state INTEGER)")
        con.execute("INSERT INTO message VALUES (1, 2, 2), (2, 2, 3), (3, 0, 0)")
        sql = self.imsg.pending_schedule_sql(con)
        rows = [r[0] for r in con.execute(f"SELECT ROWID FROM message m WHERE {sql}")]
        self.assertEqual(rows, [1])


if __name__ == "__main__":
    unittest.main()
