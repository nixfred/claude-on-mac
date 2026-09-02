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
