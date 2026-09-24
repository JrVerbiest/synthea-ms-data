"""Enrich the per-table contracts written by ``datacontract import csv`` from the data dictionary.

``datacontract import csv`` reads the CSV header and a sample of the rows, so it knows the column
names and can guess a type, but a CSV carries no meaning: the schema description is the placeholder
``Generated model of data/csv/<table>.csv``, the columns have no description, and there are no keys
and no relationships. ``tmp/data-dictionary.yaml``, built from the Synthea wiki by
``build_dictionary.py``, documents all of that. This script writes it into the contracts, in place::

    python data-contract/scripts/enrich_schemas.py data-contract/tmp/patients.yaml ...

Per schema object it sets the table description, and per column the description, the ``logicalType``
the dictionary documents, ``primaryKey`` and, for a foreign key, a ``relationships`` block. A
relationship is only written when the referenced table is one of the contracts enriched in the same
run, so the files passed on the command line are the scope: ``encounters.ORGANIZATION`` stays a
plain column until ``organizations.yaml`` is enriched along with it.

The dictionary type wins over the importer's guess, because the importer sees only a sample of one
filtered export: ``patients.DEATHDATE`` is a ``Date`` that looked like a string because most rows are
empty, and ``conditions.CODE`` is a SNOMED code that looked like an integer. When the type changes,
the ``logicalTypeOptions`` the importer inferred for the old type are dropped -- a minimum and a
maximum mean nothing for a code. What the importer derives from the data and the dictionary cannot
know is kept: ``examples``, ``unique`` and, deliberately, ``required``. The wiki states which columns
Synthea always fills, which is not the same as which columns are filled in this MS cohort
(``observations.ENCOUNTER`` is required on the wiki and empty in some rows here), and a contract has
to describe the data that exists.

Everything is read from the dictionary on every run, so the script is idempotent and can be re-run
after a new import. It is the step between the import and ``merge_schemas.py``; hand-written
corrections belong in ``merge.yaml``, not here.

Examples
--------
Run from the repository root::

    for t in patients encounters conditions observations; do
        datacontract import csv --source "data/csv/$t.csv" --output "data-contract/tmp/$t.yaml"
    done
    python data-contract/scripts/enrich_schemas.py data-contract/tmp/{patients,encounters,conditions,observations}.yaml
"""

import sys
from pathlib import Path

import yaml
from open_data_contract_standard.model import OpenDataContractStandard, Relationship

ROOT = Path(__file__).resolve().parents[1]  # data-contract/
DICTIONARY = ROOT / "tmp" / "data-dictionary.yaml"

# Wiki data type -> ODCS logicalType and the logicalTypeOptions that follow from it. The wiki's own
# format strings ("yyyy-MM-dd'T'HH:mm'Z'") are not written: they are notation for a reader and they
# do not match the exported values, which carry seconds.
TYPES = {
    "String": ("string", None),
    "UUID": ("string", {"format": "uuid"}),
    "Numeric": ("number", None),
    "Date": ("date", None),
    "iso8601 UTC Date": ("timestamp", None),
}


def main(contract_files: list[Path]) -> None:
    """Enrich every contract in ``contract_files`` from the dictionary and overwrite it.

    Parameters
    ----------
    contract_files : list of Path
        The ``<table>.yaml`` contracts to enrich. Their schema objects are also the scope for the
        relationships: a foreign key to a table outside this set is left as a plain column.
    """
    dictionary = yaml.safe_load(DICTIONARY.read_text(encoding="utf-8"))["tables"]
    contracts = {file: OpenDataContractStandard.from_file(str(file)) for file in contract_files}
    scope = {schema_obj.name for contract in contracts.values() for schema_obj in contract.schema_}

    for file, contract in contracts.items():
        for schema_obj in contract.schema_:
            entries = dictionary.get(schema_obj.name)
            if entries is None:
                raise SystemExit(f"{file}: not in the dictionary: {schema_obj.name}")
            schema_obj.description = entries["description"]

            columns = entries["columns"]
            keys, relationships, retyped, unknown = 0, 0, [], []
            for prop in schema_obj.properties:
                entry = columns.get(prop.name)
                if entry is None:
                    unknown.append(prop.name)
                    continue
                prop.description = entry["description"]

                logical_type, options = TYPES[entry["type"]]
                if logical_type != prop.logicalType:
                    retyped.append(f"{prop.name} {prop.logicalType}->{logical_type}")
                    prop.logicalTypeOptions = None
                prop.logicalType = logical_type
                if options is not None:
                    prop.logicalTypeOptions = options

                if entry.get("key") == "primary":
                    prop.primaryKey = True
                    keys += 1
                if entry.get("references", "").split(".")[0] in scope:
                    prop.relationships = [Relationship(type="foreignKey", to=entry["references"])]
                    relationships += 1

            described = len(schema_obj.properties) - len(unknown)
            print(
                f"{schema_obj.name}: {described} columns described, "
                f"{keys} primary key(s), {relationships} relationship(s)"
            )
            if retyped:
                print(f"  retyped from the dictionary: {', '.join(retyped)}")
            if unknown:
                print(f"  not in the dictionary, left as imported: {', '.join(unknown)}")

        file.write_text(contract.to_yaml(), encoding="utf-8")
        print(f"  written {file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: enrich_schemas.py <table>.yaml [<table>.yaml ...]")
    main([Path(argument) for argument in sys.argv[1:]])
