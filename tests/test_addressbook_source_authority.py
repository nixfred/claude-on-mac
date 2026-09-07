from __future__ import annotations

import importlib.machinery
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Sequence
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]


def load_script(name: str):
    loader = importlib.machinery.SourceFileLoader(name, str(REPO / "bin" / name))
    spec = importlib.util.spec_from_loader(name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def make_addressbook(path: Path, records: Sequence[tuple[str, str | None]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE ZABCDRECORD (
          Z_PK INTEGER PRIMARY KEY,
          ZFIRSTNAME TEXT,
          ZLASTNAME TEXT,
          ZORGANIZATION TEXT,
          ZNICKNAME TEXT
        );
        CREATE TABLE ZABCDPHONENUMBER (ZOWNER INTEGER, ZFULLNUMBER TEXT);
        CREATE TABLE ZABCDEMAILADDRESS (ZOWNER INTEGER, ZADDRESS TEXT);
        """
    )
    for index, (name, phone) in enumerate(records, start=1):
        first, *rest = name.split(" ", 1)
        last = rest[0] if rest else None
        con.execute(
            "INSERT INTO ZABCDRECORD (Z_PK, ZFIRSTNAME, ZLASTNAME) VALUES (?, ?, ?)",
            (index, first, last),
        )
        if phone:
            con.execute(
                "INSERT INTO ZABCDPHONENUMBER (ZOWNER, ZFULLNUMBER) VALUES (?, ?)",
                (index, phone),
            )
    con.commit()
    con.close()


class AddressBookSourceAuthorityTest(unittest.TestCase):
    def test_imsg_prefers_name_from_larger_source(self):
        imsg = load_script("imsg")
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            small = directory / "a-small.abcddb"
            other_small = directory / "b-small.abcddb"
            primary = directory / "z-primary.abcddb"
            make_addressbook(small, [("Family Label", "+15555550100")])
            make_addressbook(other_small, [("Family Label", "+15555550100")])
            make_addressbook(
                primary,
                [("Correct Name", "+15555550100")]
                + [(f"Contact {i}", None) for i in range(100)],
            )

            setattr(imsg, "_NAME_INDEX", None)
            with patch.object(imsg, "glob", return_value=[str(small), str(other_small), str(primary)]):
                self.assertEqual(imsg.name_for("+15555550100"), "Correct Name")

    def test_many_small_sources_cannot_outweigh_one_larger_source(self):
        """Largest source wins outright: small sources never sum together.

        Five 10-record sources agreeing on a stale label total 50 records
        against a 40-record primary. A vote-accumulating policy would hand
        the win to the strays; ranking sources must not.
        """
        imsg = load_script("imsg")
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            paths = []
            for n in range(5):
                small = directory / f"small-{n}.abcddb"
                make_addressbook(
                    small,
                    [("Stale Label", "+15555550100")]
                    + [(f"Filler {i}", None) for i in range(9)],
                )
                paths.append(str(small))
            primary = directory / "primary.abcddb"
            make_addressbook(
                primary,
                [("Correct Name", "+15555550100")]
                + [(f"Contact {i}", None) for i in range(39)],
            )
            paths.append(str(primary))

            setattr(imsg, "_NAME_INDEX", None)
            with patch.object(imsg, "glob", return_value=paths):
                self.assertEqual(imsg.name_for("+15555550100"), "Correct Name")

    def test_imsg_and_contacts_rank_sources_by_the_same_metric(self):
        """Both helpers must resolve one handle to one name.

        `contacts` orders source DBs by ZABCDRECORD count; `imsg` must rank
        by that same count, or the two can disagree on the same handle.
        """
        imsg = load_script("imsg")
        contacts = load_script("contacts")
        with tempfile.TemporaryDirectory() as tmp:
            addressbook = Path(tmp)
            small = addressbook / "Sources" / "a-small" / "AddressBook-v22.abcddb"
            primary = addressbook / "Sources" / "z-primary" / "AddressBook-v22.abcddb"
            make_addressbook(small, [("Stale Label", "+15555550100")])
            make_addressbook(
                primary,
                [("Correct Name", "+15555550100")]
                + [(f"Contact {i}", None) for i in range(20)],
            )

            with patch.object(contacts, "ADDRESSBOOK_DIR", str(addressbook)):
                ranked = contacts.source_dbs()
            self.assertEqual(ranked[0], str(primary))

            setattr(imsg, "_NAME_INDEX", None)
            with patch.object(imsg, "glob", return_value=[str(small), str(primary)]):
                self.assertEqual(imsg.name_for("+15555550100"), "Correct Name")

    def test_contacts_orders_sources_largest_first_with_stable_path_tiebreak(self):
        contacts = load_script("contacts")
        with tempfile.TemporaryDirectory() as tmp:
            addressbook = Path(tmp)
            small = addressbook / "Sources" / "a-small" / "AddressBook-v22.abcddb"
            primary = addressbook / "Sources" / "z-primary" / "AddressBook-v22.abcddb"
            make_addressbook(small, [("Small", None)])
            make_addressbook(primary, [(f"Primary {i}", None) for i in range(3)])

            with patch.object(contacts, "ADDRESSBOOK_DIR", str(addressbook)):
                self.assertEqual(contacts.source_dbs(), [str(primary), str(small)])


if __name__ == "__main__":
    unittest.main()
