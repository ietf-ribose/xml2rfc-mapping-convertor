import glob

import os
import typer
from tqdm import tqdm


def validate(archive_root: str):
    """Checks XML files for NUL characters.
    Outputs affected filenames to stdout.
    """
    xml_files = glob.glob(f'{archive_root}/**/*.xml')

    for fname in tqdm(xml_files):
        with open(fname, 'r') as xml_fhandler:
            relative_fname = fname.removeprefix(
              os.path.commonprefix([archive_root, fname]))
            try:
                xml_data = xml_fhandler.read()
            except UnicodeDecodeError as err:
                typer.echo(f"{relative_fname}: UnicodeDecodeError ({err})")
            else:
                if '\x00' in xml_data:
                    typer.echo(f"{relative_fname}: NUL character in XML string")


if __name__ == '__main__':
    typer.run(validate)
