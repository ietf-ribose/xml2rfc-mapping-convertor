This tiny script converts mappings in YAML format,
such as given in https://github.com/ietf-ribose/bibxml-service/issues/133#issuecomment-1106762628,
to JSON format recognized by BibXML service mapping import view
(https://dev.bibxml.org/ref/modules/xml2rfc_compat/#xml2rfc_compat.views.import_manual_map).

Setup
=====

::

    python3 -m virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

Running
=======

Simple example::

    python convert.py w3c-mapping-2.yaml bibxml4

With ``w3c-mapping-2.yaml`` as file containing mappings in YAML
and ``bibxml4`` the corresponding prefix directory
from https://github.com/ietf-ribose/bibxml-data-archive.

This will print JSON to standard output,
you can pipe it into a file for example.

More flags::

    python convert.py w3c-mapping-2.yaml bibxml4 --verbose --out w3c-mappings.json

This writes JSON to a file (overwriting it, if exists)
and provides more detailed output.

Using append::

    python convert.py w3c-mapping-2.yaml bibxml4 --verbose --out all-mappings.json --append

This appends newly parsed mappings to the specified JSON file,
preserving mappings already in that file if such file exists.

Notable behaviour:

- If specified JSON file exists, but preexisting contents
  do not conform to the mappings file format, an error will be raised.

- If a path already exists in the specified output file
  and maps to the same docid, script will output a warning to stderr.
  If it maps to a *different* docid, script will fail with an error.
