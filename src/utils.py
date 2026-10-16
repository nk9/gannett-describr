import csv
import json
import re
from collections import Counter
from logging import error
from pathlib import Path
from typing import NamedTuple

from src.store import Image

ARK_RE = re.compile("(3:1:[^/]+)")


class Source(NamedTuple):
    """Where a row's images come from: a microfilm, or a roll within a collection."""

    kind: str  # "film" or "roll"
    id: str  # digital film number or roll number
    collection: str

    def __str__(self):
        if self.kind == "roll":
            return f"roll {self.id} of collection {self.collection}"
        return f"film {self.id}"


def row_source(row) -> Source | None:
    if film_no := row.get("digital_film_no"):
        return Source("film", film_no, row.get("collection", ""))

    if (roll := (row.get("roll_no") or "").strip()).isdigit():
        return Source("roll", str(int(roll)), row.get("collection", ""))

    return None


def films_dir(index_csv: Path) -> Path:
    """Film and roll info JSONs live in a `films` directory beside the index CSV."""
    return Path(index_csv).parent / "films"


def source_info_path(index_csv: Path, source: Source) -> Path:
    if source.kind == "roll":
        return films_dir(index_csv) / f"{source.collection}-roll{source.id}.json"

    return films_dir(index_csv) / f"{source.id}.json"


def parse_index_set(spec: str) -> list[int]:
    """Parse an inclusive index set such as "150-155,160-200" into sorted indexes."""
    indexes = set()

    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            start, stop = (int(p) for p in part.split("-", 1))
            if start > stop:
                raise ValueError(f"range '{part}' runs backwards")
            indexes.update(range(start, stop + 1))
        else:
            indexes.add(int(part))

    return sorted(indexes)


def row_indexes(row) -> list[int]:
    """0-based image indexes for one index CSV row.

    Rows either have an `indexes` column holding a 1-based index set, matching
    the image numbers the FamilySearch viewer shows, or the older 0-based
    `start_index`/`stop_index` pair, which is treated as one inclusive range.
    """
    if "indexes" in row:
        indexes = parse_index_set(row["indexes"] or "")
        if indexes and indexes[0] < 1:
            raise ValueError("indexes are 1-based, so 0 isn't an image")
        return [i - 1 for i in indexes]

    if row.get("start_index") and row.get("stop_index"):
        return parse_index_set(f"{row['start_index']}-{row['stop_index']}")

    return []


def readIndexRows(index_csv: Path):
    """Yield (row, source, indexes) for each row naming a source and at least one index."""
    with open(index_csv) as csvf:
        for row in csv.DictReader(csvf):
            if not (source := row_source(row)):
                continue

            try:
                indexes = row_indexes(row)
            except ValueError as e:
                error(f"{row['year']} {row['utp_code']}: bad index set: {e}")
                continue

            if indexes:
                yield row, source, indexes


def neededSources(index_csv: Path) -> list[Source]:
    """Each distinct film or roll the index CSV uses, in order of first use."""
    return list(dict.fromkeys(source for _, source, _ in readIndexRows(index_csv)))


def missingSources(index_csv: Path) -> list[Source]:
    return [
        source
        for source in neededSources(index_csv)
        if not source_info_path(index_csv, source).is_file()
    ]


def loadSourceInfo(path: Path) -> tuple[list[str], str | None]:
    """The image ARKs in a film or roll info JSON, and the roll's waypoint if any."""
    with open(path) as jsonf:
        info = json.load(jsonf)

    arks = []
    for image in info["images"]:
        if m := ARK_RE.search(image):
            arks.append(m.group(1))

    return arks, info.get("waypoint")


def buildImageList(index_csv: Path, img_dir: Path):
    entries = []
    source_info = {}

    for row, source, indexes in readIndexRows(index_csv):
        if source not in source_info:
            path = source_info_path(index_csv, source)
            source_info[source] = loadSourceInfo(path) if path.is_file() else None

        if source_info[source] is None:
            error(f"No info json found for {source}")
            continue

        arks, waypoint = source_info[source]

        for index in indexes:
            if index < len(arks):
                entries.append((row, arks[index], index, waypoint))
            else:
                error(
                    f"{row['year']} {row['utp_code']}: 0-based index {index} is "
                    f"beyond the {len(arks)} images in {source}"
                )
                break

    # A metro may span several rows (e.g. several films), so count per metro
    metro_counts = Counter((row["year"], row["utp_code"]) for row, *_ in entries)
    metro_seen = Counter()
    images = []

    for row, ark, index, waypoint in entries:
        metro = (row["year"], row["utp_code"])
        images.append(
            Image(
                row["year"],
                row["utp_code"],
                ark,
                index,
                metro_seen[metro],
                metro_counts[metro],
                row["collection"],
                img_dir,
                waypoint,
            )
        )
        metro_seen[metro] += 1

    return images
