from typing import Optional
import json

import yaml
import typer


def convert(
    fn: str,
    dirname: str,
    out: Optional[str] = None,
    verbose: bool = False,
):
    if out and verbose:
        typer.echo(f"Reading {fn}...")

    if '/' in dirname:
        typer.echo(f"Dirname must not contain slash", err=True)
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

    result = []
    for path in mapped_paths:
        docid = data[path]
        result.append({'docid': docid, 'path': f'{dirname}/{path}'})

    if out:
        typer.echo(f"Writing JSON to {out}...")
        with open(out, 'w') as outfile:
            json.dump(result, outfile, indent=4)
    else:
        typer.echo(json.dumps(result, indent=4))

    raise typer.Exit(code=0)


if __name__ == '__main__':
    typer.run(convert)
