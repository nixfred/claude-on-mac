#!/usr/bin/env python3
"""iMessage-app cards (Ask to Buy, Fitness sharing, Find My, …) store U+FFFD
as their text and an MSMessage archive as payload. message_text() returns the
archive's `ldtext` — the sentence Messages shows when the app cannot render —
then the caption, then the app name. Link cards and everything else are
untouched."""
from __future__ import annotations

import plistlib
import sqlite3
import sys
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

IMSG = Path(__file__).resolve().parents[1] / "bin" / "imsg"
APP = "com.apple.messages.MSMessageExtensionBalloonPlugin:0000000000:com.apple.PeopleMessageService.AskToBuy"
LINK = "com.apple.messages.URLBalloonProvider"


def load_imsg():
    loader = SourceFileLoader("blip_imsg", str(IMSG))
    spec = spec_from_loader(loader.name, loader)
    assert spec is not None
    mod = module_from_spec(spec)
    sys.modules[loader.name] = mod
    loader.exec_module(mod)
    return mod


def archive(root: dict) -> bytes:
    """A minimal NSKeyedArchiver plist: strings inline, dicts as NSDictionary,
    exactly the shape Messages writes for an MSMessage payload."""
    objs: list = ["$null"]

    def put(v):
        if isinstance(v, dict):
            node = {"NS.keys": [], "NS.objects": []}
            objs.append(node)
            uid = plistlib.UID(len(objs) - 1)
            for k, o in v.items():
                node["NS.keys"].append(put(k))
                node["NS.objects"].append(put(o))
            return uid
        objs.append(v)
        return plistlib.UID(len(objs) - 1)

    top = put(root)
    return plistlib.dumps({"$version": 100000, "$archiver": "NSKeyedArchiver", "$top": {"root": top}, "$objects": objs},
                          fmt=plistlib.FMT_BINARY)


def row(text: str | None, balloon: str | None, payload: bytes | None) -> sqlite3.Row:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE m (text TEXT, attributedBody BLOB, balloon_bundle_id TEXT, payload_data BLOB)")
    con.execute("INSERT INTO m VALUES (?, NULL, ?, ?)", (text, balloon, payload))
    return con.execute("SELECT * FROM m").fetchone()


class AppCards(unittest.TestCase):
    def setUp(self) -> None:
        self.text = load_imsg().message_text

    def test_ldtext_is_the_message(self) -> None:
        payload = archive({"an": "Ask to Buy", "ldtext": "Sam would like to buy Trail Maps", "userInfo": {"caption": "ignored"}})
        self.assertEqual(self.text(row("�", APP, payload)), "Sam would like to buy Trail Maps")

    def test_html_entities_are_decoded_and_a_raw_ampersand_survives(self) -> None:
        # Apple escapes some sentences ("Photo &amp; Video Editor") and leaves others raw.
        self.assertEqual(self.text(row("�", APP, archive({"ldtext": "asked for Photo &amp; Video Editor"}))), "asked for Photo & Video Editor")
        self.assertEqual(self.text(row("�", APP, archive({"ldtext": "Trail & Ridge"}))), "Trail & Ridge")

    def test_caption_when_there_is_no_ldtext(self) -> None:
        payload = archive({"an": "Ask to Buy", "userInfo": {"caption": "Sam would like to buy Trail Maps", "subcaption": ""}})
        self.assertEqual(self.text(row("�", APP, payload)), "Sam would like to buy Trail Maps")

    def test_app_name_when_the_card_has_no_words(self) -> None:
        payload = archive({"an": "Ask to Buy", "userInfo": {"caption": ""}})
        self.assertEqual(self.text(row(None, APP, payload)), "Ask to Buy")

    def test_a_link_card_keeps_its_url(self) -> None:
        payload = archive({"an": "not an app", "ldtext": "never shown"})
        self.assertEqual(self.text(row("https://oatlug.org", LINK, payload)), "https://oatlug.org")

    def test_no_payload_or_garbage_leaves_the_text_alone(self) -> None:
        self.assertEqual(self.text(row("�", APP, None)), "�")
        self.assertEqual(self.text(row("�", APP, b"not a plist")), "�")
        self.assertEqual(self.text(row("�", APP, plistlib.dumps(["not", "an", "archive"]))), "�")

    def test_an_ordinary_message_is_untouched(self) -> None:
        self.assertEqual(self.text(row("hello", None, None)), "hello")

    def test_rows_without_the_columns_still_work(self) -> None:
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE m (text TEXT, attributedBody BLOB)")
        con.execute("INSERT INTO m VALUES ('snippet', NULL)")
        self.assertEqual(self.text(con.execute("SELECT * FROM m").fetchone()), "snippet")


if __name__ == "__main__":
    unittest.main()
