"""Merge the per-table contracts written by ``datacontract import csv`` into one ODCS contract.

``datacontract import csv`` writes one contract per CSV file and knows nothing about what the
columns mean or how the tables relate. This script puts the schema objects of several such
contracts into one contract and adds, from ``outputs/data-dictionary.yaml``, the table and column
descriptions, the primary keys and the foreign-key relationships between the merged tables.
``merge.yaml`` says what to merge and holds everything that is written by hand::

    contract:                               # any ODCS top-level fields, set on the merged contract
      id: synthea-ms-data
      name: Synthea MS Data
      description: {purpose: ...}
    output: outputs/synthea-ms-data.odcs.yaml
    server: {name: local, path: data/corrected/{model}.csv}   # {model} = table name
    dictionary: outputs/data-dictionary.yaml
    imports: imports                        # folder with the <table>.yaml contracts
    tables: [patients, encounters]          # merged in this order
    overrides:                              # per-table / per-column fields, applied last
      patients.DEATHDATE: {logicalType: date}
      patients.FIPS: {logicalType: string, logicalTypeOptions: null}   # null removes a field
      conditions: {quality: [...]}

Paths are relative to ``merge.yaml``. Everything is re-applied on each run, so the hand-written
parts in ``contract`` and ``overrides`` survive a re-import of the CSVs and a rebuild of the
dictionary: the output file is fully generated and never edited by hand. Note that ``datacontract test`` does not check referential integrity
from ``relationships``; use a SQL ``quality`` rule for that.

Examples
--------
Run from the repository root::

    python data-contract/scripts/merge_schemas.py data-contract/merge.yaml
"""

import sys
from pathlib import Path

import yaml
from open_data_contract_standard.model import OpenDataContractStandard, Relationship, Server
from pydantic import BaseModel


def apply(model: BaseModel, values: dict) -> BaseModel:
    """Return ``model`` with ``values`` set on top of its fields, validated by the model class.

    Parameters
    ----------
    model : BaseModel
        An ODCS model object (the contract, a schema object or a property).
    values : dict
        Fields to set, as they are written in the contract YAML.

    Returns
    -------
    BaseModel
        A new object of the same class.
    """
    return type(model).model_validate({**model.model_dump(by_alias=True, exclude_none=True), **values})


def main(config_file: Path) -> None:
    """Merge the contracts described in ``config_file`` and write the result.

    Parameters
    ----------
    config_file : Path
        The ``merge.yaml`` file (see the module docstring).
    """
    folder = config_file.resolve().parent
    config = yaml.safe_load(config_file.read_text(encoding="utf-8"))

    # One contract per table; the first one also provides the fundamentals (version, status, ...).
    imports = folder / config["imports"]
    imported = [OpenDataContractStandard.from_file(str(imports / f"{table}.yaml")) for table in config["tables"]]
    merged = apply(imported[0], config["contract"])
    merged.servers = [Server(server=config["server"]["name"], type="local", format="csv", path=config["server"]["path"])]
    merged.schema_ = [schema_obj for contract in imported for schema_obj in contract.schema_]

    # The dictionary replaces the importer's "Generated model of ..." placeholders and adds the keys.
    # Foreign keys only become relationships when the referenced table is part of the merge.
    dictionary = yaml.safe_load((folder / config["dictionary"]).read_text(encoding="utf-8"))["tables"]
    relationships = 0
    for schema_obj in merged.schema_:
        schema_obj.description = dictionary[schema_obj.name]["description"]
        columns = dictionary[schema_obj.name]["columns"]
        for prop in schema_obj.properties:
            entry = columns.get(prop.name)
            if entry is None:
                print(f"{schema_obj.name}: not in the dictionary: {prop.name}")
                continue
            prop.description = entry["description"]
            if entry.get("key") == "primary":
                prop.primaryKey = True
            if entry.get("references", "").split(".")[0] in config["tables"]:
                prop.relationships = [Relationship(type="foreignKey", to=entry["references"])]
                relationships += 1

    # Hand-written corrections and additions win over both the importer and the dictionary.
    # "table" targets the schema object, "table.COLUMN" the property.
    for target, values in config.get("overrides", {}).items():
        table, _, column = target.partition(".")
        index = [schema_obj.name for schema_obj in merged.schema_].index(table)
        if column:
            properties = merged.schema_[index].properties
            position = [prop.name for prop in properties].index(column)
            properties[position] = apply(properties[position], values)
        else:
            merged.schema_[index] = apply(merged.schema_[index], values)

    output = folder / config["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(merged.to_yaml(), encoding="utf-8")
    print(f"Written {len(merged.schema_)} tables with {relationships} relationships to {output}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: merge_schemas.py merge.yaml")
    main(Path(sys.argv[1]))
