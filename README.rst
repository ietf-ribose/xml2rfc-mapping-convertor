This tiny script takes mappings in YAML format,
such as given in https://github.com/ietf-ribose/bibxml-service/issues/133#issuecomment-1106762628,
and creates/updates sidecar metadata files under given ``bibxml-data-archive`` root.

Setup
=====

::

    python3 -m virtualenv env
    source env/bin/activate
    pip install -r requirements.txt

Running
=======

Simple example::

    python update_sidecar_meta.py w3c-mapping-2.yaml /path/to/bibxml-data-archive/bibxml4

With ``w3c-mapping-2.yaml`` as file containing mappings
and second argument pointing to local copy
of https://github.com/ietf-ribose/bibxml-data-archive.

This will update the contents of /path/to/bibxml-data-archive/bibxml4.
It won’t affect any of the XML files but it will create new sidecar YAML files
with ``primary_docid`` pointing to respective values within the given mapping YAML.

Notable behavior that may cause data loss
-----------------------------------------

.. important::

   It’s recommended to run this against bibxml-data-archive with everything committed,
   so that you can diff and undo changes easily.

- Any malformed sidecar metadata file is is deleted (with stderr warning).
- Any orphaned sidecar metadata file (without corresponding XML file) is deleted (with stderr warning).
- Preexisting docid mapping, if any for given mapped path, is overwritten (with stderr warning).
  The rest of sidecar metadata is preserved.
