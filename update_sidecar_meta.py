from typing import Optional, Dict, Any
import glob
import os
from pathlib import Path

import yaml
import typer
from tqdm import tqdm


def update_sidecar_meta(
    fn: str,
    datadir: str,
    conflictbehavior: Optional[str] = None,
    verbose: bool = False,
):

    archive_root = Path(datadir)

    error_stats: Dict[str, int] = {
        'orphaned sidecar files': 0,
        'malformed sidecar files': 0,
        'nonexistent paths mapped': 0,
    }


    # Gather all xml2rfc paths

    xml_files = glob.glob(f'{archive_root}/*.xml')


    # Read given mappings

    if verbose:
        typer.echo(f"Reading {fn}...")

    try:
        with open(fn, 'r') as f:
            mapping_dict = yaml.load(f.read(), Loader=yaml.SafeLoader)
    except (IOError, RuntimeError) as err:
        typer.echo(f"Unable to read file or parse YAML: {err}", err=True)
        if verbose:
            raise err
        else:
            raise typer.Exit(code=1)

    if isinstance(mapping_dict, dict):
        all_paths = mapping_dict.keys()
        mapped_paths = [
            p for p in all_paths
            if p in mapping_dict and (mapping_dict.get(p, None) or '').strip() != ''
        ]
        if verbose:
            typer.echo(f"Given {len(mapped_paths)} mapped path(s)")
        xml_basenames = [os.path.basename(p) for p in xml_files]
        for mapped_path in mapped_paths:
            if mapped_path not in xml_basenames:
                typer.secho(f"Mapping references nonexistent file: %s" % mapped_path, err=True, fg='red')
                error_stats['nonexistent paths mapped'] += 1
    else:
        typer.echo(f"File contains an invalid structure", err=True)
        raise typer.Exit(code=1)

    if len(mapped_paths) < 1:
        typer.echo("Nothing to do: file contains no mapped paths", err=True)
        raise typer.Exit(code=0)


    # Check data dir

    if verbose:
        typer.echo("Target data directory: %s" % archive_root)

    if not archive_root.exists() or not archive_root.is_dir():
        typer.echo("Error: not a directory: %s" % archive_root, err=True)

    existing_sidecar_files = glob.glob(f'{archive_root}/*.yaml')

    sidecar_data: Dict[str, Any] = dict()
    # Deserialized sidecar metadata keyed by XML file basename

    for sidecar_fpath in tqdm(existing_sidecar_files, desc="Validating integrity"):
        basename = os.path.basename(sidecar_fpath)
        basename_noext = os.path.splitext(basename)[0]
        xml_fpath = archive_root / f'{basename_noext}.xml'

        if xml_fpath.exists() and xml_fpath.is_file():
            with open(sidecar_fpath, 'r') as f:
                parsed = yaml.load(f.read(), Loader=yaml.SafeLoader)
                try:
                    validate_sidecar(parsed)
                except ValueError as err:
                    typer.secho("Removing malformed sidecar file: %s (%s)" % (sidecar_fpath, err), err=True, fg='red')
                    os.remove(sidecar_fpath)
                    error_stats['malformed sidecar files'] += 1
                else:
                    sidecar_data[basename_noext] = parsed
        else:
            typer.secho("Orphaned sidecar file: %s" % sidecar_fpath, err=True, fg='red')
            os.remove(sidecar_fpath)
            error_stats['orphaned sidecar files'] += 1


    # Write sidecar files

    stats: Dict[str, int] = {
        'unchanged sidecar files': 0,
        'updated sidecar files': 0,
        'new sidecar files': 0,
    }

    for xml_fpath in tqdm(xml_files, desc="Writing sidecar data"):
        basename = os.path.basename(xml_fpath)
        basename_noext = os.path.splitext(basename)[0]
        primary_docid = mapping_dict.get(basename, None)
        sidecar_fpath = archive_root / f'{basename_noext}.yaml'

        if primary_docid:
            existing_meta = sidecar_data.get(basename_noext, dict())
            existing_docid = existing_meta.get('primary_docid', None)

            if existing_docid:
                if existing_docid != primary_docid:
                    typer.echo("Changed mapping for %s: %s -> %s" % (
                        basename,
                        existing_docid,
                        primary_docid,
                    ), err=True)
                    stats['updated sidecar files'] += 1
                else:
                    stats['unchanged sidecar files'] += 1
                    continue
            else:
                stats['new sidecar files'] += 1

            existing_meta['primary_docid'] = primary_docid
            with open(sidecar_fpath, 'w') as f:
                f.write(yaml.dump(existing_meta))

    typer.echo("Done")

    for label, stat in stats.items():
        typer.echo(f"{label}: {stat}")

    for label, stat in error_stats.items():
        typer.secho(f"{label}: {stat}", fg='red' if stat > 0 else None)

    raise typer.Exit(code=0)


def validate_sidecar(entry: dict):
    """Raises a ValueError if entry is not a valid sidecar meta file entry."""

    if not isinstance(entry, dict):
        raise ValueError("Not an object")

    docid = entry.get('primary_docid', None)
    invalid = entry.get('invalid', None)

    if docid is not None and (not isinstance(docid, str) or docid.strip() == ''):
        raise ValueError("Invalid or missing primary docid mapping")
    if invalid is not None and not isinstance(invalid, bool):
        raise ValueError("Invalid “invalid” marker")


if __name__ == '__main__':
    typer.run(update_sidecar_meta)
