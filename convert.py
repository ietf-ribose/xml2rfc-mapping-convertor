from typing import Optional
import json
from pathlib import Path

import yaml
import typer


def convert(
    fn: str,
    dirname: str,
    out: Optional[str] = None,
    verbose: bool = False,
    append: bool = False,
):
    # Extra argument validation
    if '/' in dirname:
        typer.echo(f"Dirname must not contain slash", err=True)
        raise typer.Exit(code=1)

    if out and verbose:
        typer.echo(f"Reading {fn}...")

    if append and not out:
        typer.echo(f"--append can only be used with --out", err=True)
        raise typer.Exit(code=1)

    try:
        with open(fn, 'r') as f:
            data = yaml.load(f.read(), Loader=yaml.SafeLoader)
    except (IOError, RuntimeError) as err:
        typer.echo(f"Unable to read file or parse YAML: {err}", err=True)
        if verbose:
            raise err
        else:
            raise typer.Exit(code=1)

    # Reading given paths
    if isinstance(data, dict):
        all_paths = data.keys()
        mapped_paths = [
            p for p in all_paths
            if p in data and (data.get(p, None) or '').strip() != ''
        ]
        if verbose and out:
            typer.echo(f"{len(all_paths)} paths total, {len(mapped_paths)} mapped")

    else:
        typer.echo(f"File has invalid structure", err=True)
        raise typer.Exit(code=1)

    if len(mapped_paths) < 1:
        typer.echo("Nothing to do: file contains no mapped paths", err=True)
        raise typer.Exit(code=0)

    # Preparing result
    if out:
        if append:
            path = Path(out)
            try:
                if path.exists() and path.is_file():
                    with open(out, 'r') as outfile:
                        result = json.load(outfile)
                    if isinstance(result, list):
                        for idx, entry in enumerate(result):
                            try:
                                validate_mapping(entry)
                            except ValueError as err:
                                raise ValueError(
                                    f"Invalid mapping entry at {idx + 1}: "
                                    f"{repr(entry)}: {err}")
                else:
                    result = []
            except (IOError, ValueError, RuntimeError) as err:
                typer.echo(f"Unable to read or parse existing JSON file: {err}", err=True)
                if verbose:
                    raise err
                else:
                    raise typer.Exit(code=1)
        else:
            result = []

    preexisting_mappings = {}
    for p_mapping in result:
        preexisting_mappings[p_mapping['path']] = p_mapping['docid']

    # Adding to result
    for filename in mapped_paths:
        docid = data[filename]
        path = f'{dirname}/{filename}'
        if path in preexisting_mappings:
            if preexisting_mappings[path] != docid:
                typer.echo(
                    f"Path {path} is already mapped "
                    f"to {preexisting_mappings[path]}, will map to {docid}", err=True)
                raise typer.Exit(code=1)
            else:
                typer.echo(f"Path {path} is already mapped, skipping", err=True)
        else:
            result.append({'docid': docid, 'path': path})

    # Writing JSON
    if out:
        typer.echo(f"Writing JSON to {out}...")
        with open(out, 'w') as outfile:
            json.dump(result, outfile, indent=4)
    else:
        typer.echo(json.dumps(result, indent=4))

    raise typer.Exit(code=0)


def validate_mapping(entry: dict):
    """Raises a ValueError if entry is not a valid mapping file entry."""

    if not isinstance(entry, dict):
        raise ValueError("Not an object")

    docid = entry.get('docid', None)
    path = entry.get('path', None)

    if not isinstance(docid, str) or docid.strip() == '':
        raise ValueError("Invalid or missing docid")
    if not isinstance(path, str) or path.strip() == '':
        raise ValueError("Invalid or missing path")


if __name__ == '__main__':
    typer.run(convert)
