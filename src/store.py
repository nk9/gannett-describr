import csv
import json
import re
from pathlib import Path

from ordered_set import StableSet

from src.ed import Ed
from src.log import get_logger

prev = lambda obj: obj.prev()

CAT_1930 = "1037259"
FS_IMG_URL = "https://www.familysearch.org/ark:/61903/{ark}?i={i}&cat={cat}"


class Image:
    def __init__(self, year, utp_code, ark, i, metro_index, metro_image_count, cat):
        self.year = year
        self.utp_code = utp_code
        self.ark = ark
        self.image_index = i
        self.metro_image_index = metro_index
        self.metro_image_count = metro_image_count
        self.cat = cat
        self.eds = StableSet([])
        self.db_id = None

    def __eq__(self, other):
        return self.ark == other.ark

    def __repr__(self):
        return f"{self.year} {self.utp_code:15} {self.image_index:4} {self.ark} [{self.metro_image_index:4}/{self.metro_image_count}]"

    def addED(self, ed):
        self.eds.add(str(ed).upper())

    def removeED(self, ed):
        self.eds.remove(str(ed).upper())

    @property
    def url(self):
        return FS_IMG_URL.format_map(
            {"ark": self.ark, "i": self.image_index, "cat": self.cat}
        )


class Store:
    def __init__(self, db, images):
        self.images = images
        self.index = 0

        self.db = db
        self.init_db()
        self.populate_db(images)
        self.log = get_logger()

    def __iter__(self):
        return self

    def __next__(self):
        if self.index + 1 < len(self.images):
            self.index += 1
            return self.images[self.index]

        raise StopIteration

    def prev(self):
        if self.index - 1 >= 0:
            self.index -= 1
            return self.images[self.index]

        raise StopIteration

    def nextMetro(self):
        for index, img in enumerate(self.images):
            if (
                index < len(self.images) - 1
                and index >= self.index
                and img.utp_code != self.images[index + 1].utp_code
            ):
                self.index = index + 1
                return self.images[self.index]

        return None

    def prevMetro(self):
        for index, img in reversed(list(enumerate(self.images[: self.index + 1]))):
            if (
                index >= 1
                and index <= self.index
                and img.utp_code != self.images[index - 1].utp_code
            ):
                self.index = index - 1
                return self.images[self.index]

        return None

    def curr(self):
        return self.images[self.index]

    def addEDToCurrentImage(self, ed: Ed):
        image = self.images[self.index]
        try:
            self.db.execute(
                """
                INSERT INTO eds (image_id, name) VALUES (?, ?)
                ON CONFLICT DO NOTHING
                """,
                (image.db_id, str(ed)),
            )
            image.addED(ed)
            self.db.connection.commit()
        except Exception as e:
            self.log.warning(f"Failed to insert '{ed}' for '{image}': {e}")

    def removeLastED(self):
        image = self.images[self.index]
        try:
            res = self.db.execute(
                """
                SELECT id, name
                FROM eds
                WHERE image_id = ?
                ORDER BY id DESC -- get most recent
                LIMIT 1;
                """,
                (image.db_id,),
            ).fetchone()

            # Make sure there's an ED to remove!
            if res is not None:
                (ed_id, name) = res
                self.db.execute(
                    """
                    DELETE FROM eds WHERE id = ?
                    """,
                    (ed_id,),
                )
                image.removeED(name)
                self.db.connection.commit()
        except Exception as e:
            self.log.warning(f"Failed to remove last ED for '{image}': {e}")

    def largestEDForCurrentMetro(self):
        image = self.images[self.index]

        res = self.db.execute(
            """
            SELECT name
            FROM eds AS e
                JOIN images AS i ON i.id = e.image_id
            WHERE i.utp_code = ?
            ORDER BY e.name DESC
            LIMIT 1
            """,
            (image.utp_code,),
        ).fetchone()

        return res[0] if res is not None else "1"

    def skipToLastEntered(self):
        for index, img in reversed(list(enumerate(self.images))):
            if len(img.eds):
                self.index = index
                break

    def skipToLastEnteredWithinMetro(self):
        for index, img in reversed(list(enumerate(self.images))):
            if self.curr().utp_code == img.utp_code and len(img.eds):
                self.index = index
                break

    def init_db(self):
        self.db.connection.execute("PRAGMA foreign_keys = 1")

        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY,
                year INTEGER NOT NULL,
                utp_code VARCHAR NOT NULL,
                ark VARCHAR NOT NULL,
                image_index INTEGER NOT NULL,
                cat INTEGER NOT NULL,
                UNIQUE(ark));
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS eds (
                id INTEGER PRIMARY KEY,
                image_id INTEGER NOT NULL,
                name VARCHAR,
                FOREIGN KEY (image_id) REFERENCES images (id),
                UNIQUE(image_id, name));
            """
        )
        self.db.connection.commit()

    def populate_db(self, images):
        for image in images:
            data = (
                int(image.year),
                image.utp_code,
                image.ark,
                image.image_index,
                image.cat,
            )
            self.db.execute(
                """
                INSERT INTO images (year, utp_code, ark, image_index, cat)
                    VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING""",
                data,
            )
            res = self.db.execute(
                """SELECT id FROM images WHERE ark = ?""", (image.ark,)
            ).fetchone()
            image.db_id = res[0]

            res = self.db.execute(
                """SELECT name FROM eds WHERE image_id = ?""", (image.db_id,)
            ).fetchall()
            image.eds.update([e[0] for e in res])

        self.db.connection.commit()
