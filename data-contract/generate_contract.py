"""Generate the ODCS data contract of the Synthea CSV files in data/csv.

The contract is built in four steps:

1. Read the Synthea CSV data dictionary from the Synthea wiki.
2. Import each CSV file with datacontract-cli: one schema object per table.
3. Write the dictionary's descriptions, types and keys into the schema objects.
4. Merge them into one contract with the top-level fields and overrides of settings.yaml.

Run from the repo root::

    python data-contract/generate_contract.py
"""

import csv
import re
import urllib.request
from pathlib import Path

import yaml
from datacontract.data_contract import DataContract
from open_data_contract_standard.model import Relationship

SETTINGS = Path("data-contract/settings.yaml")
DICTIONARY = "https://raw.githubusercontent.com/wiki/synthetichealth/synthea/CSV-File-Data-Dictionary.md"

# (table, wiki name) -> CSV header, where the wiki lags behind the exporter
RENAMES = {("patients", "FIPS County Code"): "FIPS"}

# dictionary type -> ODCS logicalType and its logicalTypeOptions
TYPES = {
    "String": ("string", None),
    "UUID": ("string", {"format": "uuid"}),
    "Numeric": ("number", None),
    "Date": ("date", None),
    "iso8601 UTC Date": ("timestamp", None),
}


def clean(cell):
    """Return a wiki table cell as plain text.

    Parameters
    ----------
    cell : str
        A cell of a Markdown table, which may hold ``<br>`` tags and backticks.

    Returns
    -------
    str
        The cell without tags, backticks and repeated whitespace.
    """
    return re.sub(r"\s+", " ", re.sub(r"<br\s*/?>", " ", cell).replace("`", "")).strip()


def fold(name):
    """Return a column name without spaces and underscores, in lower case.

    Parameters
    ----------
    name : str
        A column name from the wiki or a CSV header.

    Returns
    -------
    str
        The name to match on, e.g. ``"Birth Date"`` and ``"BIRTHDATE"`` both give ``"birthdate"``.
    """
    return re.sub(r"[\s_]", "", name).lower()


def parse(markdown, data, tables):
    """Parse the data dictionary wiki page.

    Parameters
    ----------
    markdown : str
        The wiki page, one ``# <Table>`` section with a column table per CSV file.
    data : pathlib.Path
        The folder with the CSV files, whose headers give the column names.
    tables : list of str
        The tables to parse.

    Returns
    -------
    dict
        ``{table: {"description": str, "columns": {header: entry}}}``. An entry holds the column's
        ``description`` and ``type``, ``primary`` for a primary key, and ``references`` (``"<table>.Id"``)
        for a foreign key.
    """
    descriptions = dict(re.findall(r"\| \[`(\w+)\.csv`\]\(#[\w-]+\) \| (.+?) \|", markdown))
    sections = re.split(r"^# (.+)$", markdown, flags=re.MULTILINE)[1:]
    bodies = {title.strip().lower().replace(" ", "_"): body for title, body in zip(sections[::2], sections[1::2])}

    dictionary = {}
    for table in tables:
        with (data / f"{table}.csv").open(newline="", encoding="utf-8") as f:
            headers = {fold(header): header for header in next(csv.reader(f))}

        columns = {}
        for line in bodies[table].splitlines():
            cells = [clean(c) for c in line.strip().strip("|").split("|")]
            if not line.startswith("| ") or len(cells) != 5 or cells[1] == "Column Name":
                continue
            marker, wiki_name, data_type, _, description = cells
            wiki_name = re.sub(r"\s*\(.*\)$", "", wiki_name)
            name = RENAMES.get((table, wiki_name)) or headers.get(fold(wiki_name), wiki_name.upper())

            entry = {"description": description, "type": re.sub(r"\s*\(.+\)$", "", data_type)}
            if marker == ":key:":
                entry["primary"] = True
            if marker == ":old_key:":
                # "Foreign key to the supervising Provider." -> providers.Id
                for word in description.split():
                    if word.lower().strip(".") + "s" in bodies:
                        entry["references"] = f"{word.lower().strip('.')}s.Id"
                        break
            columns[name] = entry
        dictionary[table] = {"description": clean(descriptions[table]), "columns": columns}
    return dictionary


def enrich(schema, dictionary):
    """Write the data dictionary into the imported schema objects, in place.

    The dictionary's descriptions, types and keys win over the import, which guesses from the data.
    ``required`` and ``unique`` stay as imported: the contract describes the data that exists.
    Examples are dropped, because the import samples them at random.

    Parameters
    ----------
    schema : list of open_data_contract_standard.model.SchemaObject
        The imported tables.
    dictionary : dict
        The data dictionary, as returned by `parse`. A foreign key becomes a relationship only when it
        refers to one of its tables.
    """
    for schema_obj in schema:
        entries = dictionary[schema_obj.name]
        schema_obj.description = entries["description"]
        for prop in schema_obj.properties:
            prop.examples = None
            entry = entries["columns"].get(prop.name)
            if entry is None:
                print(f"{schema_obj.name}.{prop.name}: not in the dictionary, left as imported")
                continue
            prop.description = entry["description"]
            logical_type, options = TYPES[entry["type"]]
            if logical_type != prop.logicalType:
                prop.logicalType, prop.logicalTypeOptions = logical_type, None
            if options:
                prop.logicalTypeOptions = options
            if entry.get("primary"):
                prop.primaryKey = True
            if entry.get("references", "").split(".")[0] in dictionary:
                prop.relationships = [Relationship(type="foreignKey", to=entry["references"])]


def apply(model, values):
    """Return a copy of an ODCS model with fields set.

    Parameters
    ----------
    model : pydantic.BaseModel
        An ODCS contract, schema object or property.
    values : dict
        ODCS fields by name; each replaces the model's field of that name.

    Returns
    -------
    pydantic.BaseModel
        A validated copy of `model` with `values` set.
    """
    return type(model).model_validate({**model.model_dump(by_alias=True, exclude_none=True), **values})


def main():
    """Generate the contract with the settings in data-contract/settings.yaml and write it to their ``output``."""
    settings = yaml.safe_load(SETTINGS.read_text(encoding="utf-8"))
    data = Path(settings["data"])
    with urllib.request.urlopen(DICTIONARY, timeout=30) as response:
        dictionary = parse(response.read().decode("utf-8"), data, settings["tables"])

    imported = [DataContract.import_from_source("csv", str(data / f"{table}.csv")) for table in settings["tables"]]
    contract = apply(imported[0], settings["contract"])
    contract.schema_ = [schema_obj for imported_contract in imported for schema_obj in imported_contract.schema_]
    enrich(contract.schema_, dictionary)

    for target, values in settings.get("overrides", {}).items():
        table, _, column = target.partition(".")
        index = [schema_obj.name for schema_obj in contract.schema_].index(table)
        if column:
            properties = contract.schema_[index].properties
            position = [prop.name for prop in properties].index(column)
            properties[position] = apply(properties[position], values)
        else:
            contract.schema_[index] = apply(contract.schema_[index], values)

    Path(settings["output"]).write_text(contract.to_yaml(), encoding="utf-8")
    print(f"written {settings['output']}")


if __name__ == "__main__":
    main()
