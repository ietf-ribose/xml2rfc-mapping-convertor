Helper scripts for working with xml2rfc paths and mappings.

- |test_paths.py|_ for testing xml2rfc paths
- |update_sidecar_meta.py|_ for writing xml2rfc archive YAML sidecar metadata files from a simple YAML mapping file
- |validate.py|_ for validating xml2rfc archive XML contents for possible encoding issues and such
- |fix_w3c_mappings.py|_ for ensuring simple YAML mapping for W3C has docids prefixed with W3C, as per Relaton source

Setup
=====

::

    python3 -m virtualenv env
    source env/bin/activate
    pip install -r requirements.txt

.. |test_paths.py| replace:: ``test_paths.py``
.. _test_paths.py: #test_pathspy

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
- Second argument is path to ``bibxml-data-archive`` repository root on your local machine
- ``--reports-dir some/dir`` (required) points to a directory where reports can be placed (directory must exist, can be relative)
- ``--dirname <str>`` indicates a directory to test, e.g. “bibxml2”
- ``--randomize`` will cause paths to be processed at random,
  which means you can test a random subset of paths by running the script for a bit and aborting with ``Ctrl+C``
- ``--reference-root <URL>`` will additionally hit this API endpoint, and diff XML with it
- ``--check-aliases`` will additionally check path aliases (e.g., ``bibxml-w3c`` will also be checked for dirname ``bibxml4``; twice as many paths would be checked)
- ``--continue-at <num>`` will continue from path at given index. Requires a specific ``--dirname`` to work, and is incompatible (has no effect) with ``--check-aliases``, ``--randomize``
- ``--sleep <num>`` wait for this many seconds after each tested path (a sort of naive throttling mechanism)
- ``--verbosity <number>`` indicates verbosity level (default is 1)

Reports
-------

For each directory,

- An HTML report is written with breakdown by path and stats at the end.
- A simple log file is written with basic stats (failed count and counts by resolution method).

.. note::

   Both files are updated continuously.

   - You can view the report before the test finishes.
   - Hitting ``Ctrl+C`` at any point will leave a valid report for paths processed so far.
   - You can resume the report after that by noting latest processed path index in progress bar
     and passing that number via ``--continue-at``
     (as long as you only check one dirname, don’t use randomization, don’t check aliases,
     and leave report file from the previous run in the same place).


Reference comparison
--------------------

Example with reference comparison::

    python3 test_paths.py http://localhost:8000/public/rfc /path/to/bibxml-data-archive --dirname bibxml4 --reference-root http://xml2rfc.tools.ietf.org/public/rfc/ --verbosity 2 --reports-dir reports

This will incur additional API request, but will show a diff if resulting XML is not the same
(which is supposed to be the case since the main service API aims to provide newer data,
serialized to bibxml on the fly from authoritative bibliographic source data).

.. important:: There’s no throttling and endpoint provided via ``reference-root`` will be hammered many times during the test run.

.. |update_sidecar_meta.py| replace:: ``update_sidecar_meta.py``
.. _update_sidecar_meta.py: #update_sidecar_metapy

update_sidecar_meta.py
======================

This script takes mappings in YAML format,
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

If you are able to locally run a local copy of the service with sources indexed
(or don’t mind hitting an online instance), it’s recommended to pass BibXML API root,
in which case the service will validate that each primary docids exist before writing.

- Supply API access info with ``--bibxml-api-root <URL>`` and ``--bibxml-api-token <Datatracker token>``
- ``--validate-mappings`` can be set to ``strict``, ``skip`` or ``warn``
  (``strict`` will fail with an error if any docid doesn’t exist,
  ``skip`` will not output files for such paths)

Notable behavior that may cause data loss
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. important::

   It’s recommended to run this against bibxml-data-archive with everything committed,
   so that you can diff and undo changes easily.

- Any malformed sidecar metadata file is is deleted (with stderr warning).
- Any orphaned sidecar metadata file (without corresponding XML file) is deleted (with stderr warning).
- Preexisting docid mapping, if any for given mapped path, is overwritten (with stderr warning).
  The rest of sidecar metadata is preserved.

.. |fix_w3c_mappings.py| replace:: ``fix_w3c_mappings.py``
.. _fix_w3c_mappings.py: #fix_w3c_mappingspy

fix_w3c_mappings.py
===================

Document identifiers in W3C mappings
provided per https://github.com/ietf-ribose/bibxml-service/issues/133
seem to be missing a “W3C ” prefix. This script adds it, and takes two arguments:
YAML filename to read and YAML filename to write. It also excludes unmapped paths.

.. |validate.py| replace:: ``validate.py``
.. _validate.py: #validatepy

validate.py
===========

Given local path to bibxml-data-archive repository root, outputs to stdout any file
with unicode decode errors or NUL characters that break XML parsing.
