Helper scripts for working with xml2rfc paths and mappings.

Setup
=====

::

    python3 -m virtualenv env
    source env/bin/activate
    pip install -r requirements.txt

update_sidecar_meta.py
======================

This tiny script takes mappings in YAML format,
such as given in https://github.com/ietf-ribose/bibxml-service/issues/133#issuecomment-1106762628,
and creates/updates sidecar metadata files under given ``bibxml-data-archive`` root.

Usage
-----

Example::

    python3 update_sidecar_meta.py w3c-mapping-2.yaml /path/to/bibxml-data-archive/bibxml4

With ``w3c-mapping-2.yaml`` as file containing mappings
and second argument pointing to local copy
of https://github.com/ietf-ribose/bibxml-data-archive.

This will update the contents of /path/to/bibxml-data-archive/bibxml4.
It won’t affect any of the XML files but it will create new sidecar YAML files
with ``primary_docid`` pointing to respective values within the given mapping YAML.

Notable behavior that may cause data loss
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. important::

   It’s recommended to run this against bibxml-data-archive with everything committed,
   so that you can diff and undo changes easily.

- Any malformed sidecar metadata file is is deleted (with stderr warning).
- Any orphaned sidecar metadata file (without corresponding XML file) is deleted (with stderr warning).
- Preexisting docid mapping, if any for given mapped path, is overwritten (with stderr warning).
  The rest of sidecar metadata is preserved.

test_paths.py
=============

This script goes through entries in ``bibxml-data-archive``
and pulls xml2rfc API endpoint for each path, optionally comparing with a reference (e.g., ``xml2rfc.tools.ietf.org``)
and reporting results.

Usage
-----

Example::

    python3 test_paths.py http://localhost:8000/public/rfc /path/to/bibxml-data-archive --dirname bibxml4 --verbosity 2 --reports-dir reports

Arguments:

- First argument is API endpoint to test (complete with ``/public/rfc/`` suffix)
- Second argument is ``bibxml-data-archive`` root on your local machine
- ``dirname`` indicates a directory to test
- ``verbosity`` indicates verbosity level (default is 1)
- ``reports-dir`` points to a directory where reports can be placed (directory must exist, can be relative).
- ``randomize`` will cause paths to be processed at random,
  which means you can test a random subset of paths by running the script for a bit and aborting with ``Ctrl+C``
- ``reference-root`` will additionally hit this API endpoint
- ``check-aliases`` will additionally check path aliases (e.g., ``bibxml-w3c`` will also be checked for dirname ``bibxml4``)

Reports
-------

For each directory,

- An HTML report is written with breakdown by path and stats at the end.
- A simple log file is written with basic stats (failed count and counts by resolution method).

.. note:: Both files are updated continuously and hitting ``Ctrl+C`` halfway will still leave usable results.


Reference comparison
--------------------

Example with reference comparison::

    python3 test_paths.py http://localhost:8000/public/rfc /path/to/bibxml-data-archive --dirname bibxml4 --reference-root http://xml2rfc.tools.ietf.org/public/rfc/ --verbosity 2 --reports-dir reports

This will incur additional API request, but will show a diff if resulting XML is not the same
(which is supposed to be the case since the main service API aims to provide newer data,
serialized to bibxml on the fly from authoritative bibliographic source data).

.. important:: There’s no throttling and endpoint provided via ``reference-root`` will be hammered many times during the test run.
