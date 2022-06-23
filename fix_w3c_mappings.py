from typing import Dict
import yaml
import typer


def fix_w3c_mappings(
    infile: str,
    outfile: str,
):
    """
    Fixes W3C mappings given in YAML in ``path: docid`` format,
    adding ``W3C `` prefix to those docids that miss it.

    Also removes nonexistent paths while at it.
    """
    with open(infile, 'r') as infh, open(outfile, 'w') as outfh:
        indata = yaml.load(infh.read(), Loader=yaml.SafeLoader)
        outdata: Dict[str, str] = dict()
        for key, value in indata.items():
            if value:
                outdata[key] = f"W3C {value.removeprefix('W3C ')}"
        outfh.write(yaml.dump(outdata))


if __name__ == '__main__':
    typer.run(fix_w3c_mappings)
