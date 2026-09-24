"""Merge the per-table contracts of ``enrich_schemas.py`` into one ODCS contract.

There is one contract per CSV file, each describing a single table and each carrying its own
fundamentals and its own ``local`` server. A data product needs one contract covering all of them.
This script puts their schema objects into one contract and adds everything that is written by hand.
The meaning of the columns, the keys and the relationships are already in the per-table contracts,
put there by ``enrich_schemas.py`` from the data dictionary, so this step only merges and overrides::

    contract:                               # any ODCS top-level fields, set on the merged contract
      id: synthea-ms-data
      name: Synthea MS Data
      description: {purpose: ...}
    output: tmp/synthea-ms-data.odcs.yaml
    server: {name: local, path: data/csv/{model}.csv}   # {model} = table name
    imports: tmp                            # folder with the <table>.yaml contracts
    tables: [patients, encounters]          # merged in this order
    overrides:                              # per-table / per-column fields, applied last
      conditions.CODE: {description: SNOMED CT code. Multiple sclerosis is 24700007.}
      conditions: {quality: [...]}

Paths in ``merge.yaml`` are relative to it, except ``server.path``, which ``datacontract test``
resolves from the directory it is run in. Everything is re-applied on each run, so the hand-written
parts in ``contract`` and ``overrides`` survive a re-import of the CSVs and a re-enrichment: the
output file is fully generated and never edited by hand. Note that ``datacontract test`` does not
check referential integrity from ``relationships``; use a SQL ``quality`` rule for that.

Examples
--------
Run from the repository root::

    python data-contract/scripts/merge_schemas.py data-contract/merge.yaml
"""

import sys
from pathlib import Path

import yaml
from open_data_contract_standard.model import OpenDataContractStandard, Server
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

    # One contract per table; the first one also provides the fundamentals (version, apiVersion, ...)
    # that `contract` does not set.
    imports = folder / config["imports"]
    imported = [OpenDataContractStandard.from_file(str(imports / f"{table}.yaml")) for table in config["tables"]]
    merged = apply(imported[0], config["contract"])
    merged.servers = [Server(server=config["server"]["name"], type="local", format="csv", path=config["server"]["path"])]
    merged.schema_ = [schema_obj for contract in imported for schema_obj in contract.schema_]

    # A relationship to a table that is not merged would point at nothing, so it is dropped here
    # rather than in the per-table contract, where it is true on its own.
    for schema_obj in merged.schema_:
        for prop in schema_obj.properties:
            outside = [r for r in prop.relationships or [] if r.to.split(".")[0] not in config["tables"]]
            if outside:
                print(f"{schema_obj.name}.{prop.name}: dropped, table not merged: {', '.join(r.to for r in outside)}")
                prop.relationships = [r for r in prop.relationships if r not in outside] or None

    # Hand-written corrections and additions win over the per-table contracts.
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

    relationships = sum(len(prop.relationships or []) for s in merged.schema_ for prop in s.properties)
    output = folder / config["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(merged.to_yaml(), encoding="utf-8")
    print(f"Written {len(merged.schema_)} tables with {relationships} relationships to {output}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: merge_schemas.py merge.yaml")
    main(Path(sys.argv[1]))
