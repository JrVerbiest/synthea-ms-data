"""Build ``outputs/data-dictionary.yaml`` from the Synthea CSV File Data Dictionary wiki page.

The wiki page documents every CSV file Synthea exports: a one-line description per file and,
per column, the name, data type, whether it is required, a description and whether it is a
primary (``:key:``) or foreign (``:old_key:``) key. This script fetches the page as Markdown,
parses those tables and writes them as one YAML dictionary that ``merge_schemas.py`` reads.
Re-run it when the wiki changes; the file records the source, the date and a hash of the page.

Column names on the wiki are written for humans (``BirthDate``, ``Patient ID``) while the CSV
headers are upper-case without spaces (``BIRTHDATE``, ``PATIENTID``), so each name is matched to
the header of ``data/corrected/<table>.csv`` ignoring case, spaces and underscores. The few
columns where the wiki and the exporter genuinely disagree are listed in ``RENAMES``.

Examples
--------
Run from the repository root::

    python data-contract/scripts/build_dictionary.py
"""

import csv
import hashlib
import re
import urllib.request
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]  # data-contract/
DATA = ROOT.parent / "data" / "corrected"
OUTPUT = ROOT / "outputs" / "data-dictionary.yaml"
PAGE_URL = "https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary"
RAW_URL = "https://raw.githubusercontent.com/wiki/synthetichealth/synthea/CSV-File-Data-Dictionary.md"

# (table, wiki name) -> CSV header, where the wiki lags behind the exporter.
RENAMES = {
    ("patients", "FIPS County Code"): "FIPS",
    ("immunizations", "Cost"): "BASE_COST",
    ("payer_transitions", "Start_Year"): "START_DATE",
    ("payer_transitions", "End_Year"): "END_DATE",
    ("payer_transitions", "Ownership"): "PLAN_OWNERSHIP",
}


def clean(cell: str) -> str:
    """Turn a Markdown table cell into plain text.

    Parameters
    ----------
    cell : str
        Cell content, possibly with backticks, ``<br/>`` tags and surrounding blanks.

    Returns
    -------
    str
        The text without markup, whitespace collapsed.
    """
    return re.sub(r"\s+", " ", re.sub(r"<br\s*/?>", " ", cell).replace("`", "")).strip()


def parse(markdown: str) -> dict[str, dict]:
    """Parse the wiki page into dictionary entries keyed by table and CSV column name.

    Parameters
    ----------
    markdown : str
        The wiki page content.

    Returns
    -------
    dict of str to dict
        ``table -> {file, description, columns: {name: {description, type, format, required,
        key, references}}}``; ``format``, ``key`` and ``references`` are present only when known.
    """
    # The overview table at the top maps each file to its one-line description.
    descriptions = dict(re.findall(r"\| \[`(\w+)\.csv`\]\(#[\w-]+\) \| (.+?) \|", markdown))
    # Each table has its own "# Title" section holding one Markdown table.
    sections = re.split(r"^# (.+)$", markdown, flags=re.MULTILINE)[1:]
    tables = {title.strip().lower().replace(" ", "_"): body for title, body in zip(sections[::2], sections[1::2])}

    dictionary = {}
    for table, body in tables.items():
        header = []
        if (DATA / f"{table}.csv").exists():
            with (DATA / f"{table}.csv").open(newline="", encoding="utf-8") as f:
                header = next(csv.reader(f))
        fold = {re.sub(r"[\s_]", "", h).lower(): h for h in header}

        columns = {}
        for line in body.splitlines():
            cells = [clean(c) for c in line.strip().strip("|").split("|")]
            if not line.startswith("| ") or len(cells) != 5 or cells[1] == "Column Name":
                continue
            marker, wiki_name, data_type, required, description = cells
            wiki_name = re.sub(r"\s*\(.*\)$", "", wiki_name)  # 'Start ("Date", prior to v3.0.0)' -> 'Start'
            name = RENAMES.get((table, wiki_name)) or fold.get(re.sub(r"[\s_]", "", wiki_name).lower(), wiki_name.upper())

            entry = {"description": description, "type": data_type, "required": required.lower() == "true"}
            if match := re.fullmatch(r"(.+?)\s*\((.+)\)", data_type):  # 'Date (YYYY-MM-DD)' -> type + format
                entry["type"], entry["format"] = match.group(1).strip(), match.group(2).strip()
            if marker == ":key:":
                entry["key"] = "primary"
            if marker == ":old_key:":
                entry["key"] = "foreign"
                # "Foreign key to the supervising Provider." -> providers.Id
                for word in description.split():
                    if word.lower().strip(".") + "s" in tables:
                        entry["references"] = f"{word.lower().strip('.')}s.Id"
                        break
            columns[name] = entry

        undocumented = [h for h in header if h not in columns]
        if undocumented:
            print(f"{table}: not on the wiki: {', '.join(undocumented)}")
        dictionary[table] = {"file": f"{table}.csv", "description": clean(descriptions[table]), "columns": columns}
    return dictionary


def main() -> None:
    """Fetch the wiki page, parse it and write ``outputs/data-dictionary.yaml``."""
    with urllib.request.urlopen(RAW_URL, timeout=30) as response:
        markdown = response.read().decode("utf-8")

    document = {
        "source": {
            "url": PAGE_URL,
            "retrieved": date.today().isoformat(),
            "sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        },
        "tables": parse(markdown),
    }
    header = "# Generated by build_dictionary.py from the Synthea wiki. Do not edit; re-run the script.\n"
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(header + yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    print(f"Written {len(document['tables'])} tables to {OUTPUT}")


if __name__ == "__main__":
    main()
