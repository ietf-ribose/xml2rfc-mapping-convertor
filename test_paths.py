from typing import Callable, List, Tuple, Dict, Optional, Any, TextIO, cast
import os
import glob
from pathlib import Path
import dataclasses
import html
import random

import yaml
import typer
import requests
from tqdm import tqdm

import diff_match_patch


dmp = diff_match_patch.diff_match_patch()


@dataclasses.dataclass
class Stats:
    failed: int = 0
    used_fallback: int = 0
    used_mapping: int = 0
    used_auto_resolution: int = 0


@dataclasses.dataclass
class MethodOutcome:
    method: str
    success: bool
    config: Optional[str] = None
    error: Optional[str] = None


@dataclasses.dataclass
class PathOutcome:
    resulting_xml: Optional[str]
    error: Optional[str] = None
    methods_tried: Optional[List[MethodOutcome]] = None
    successful_method: Optional[MethodOutcome] = None
    reference: Optional[str] = None
    diff: Optional[str] = None


# Copy this from bibxml-service settings.
XML2RFC_COMPAT_DIR_ALIASES: Dict[str, List[str]] = {
    'bibxml': ['bibxml-rfcs'],
    'bibxml2': ['bibxml-misc'],
    'bibxml3': ['bibxml-ids'],
    'bibxml4': ['bibxml-w3c'],
    'bibxml5': ['bibxml-3gpp'],
    'bibxml6': ['bibxml-ieee'],
    'bibxml7': ['bibxml-doi'],
    'bibxml8': ['bibxml-iana'],
    'bibxml9': ['bibxml-rfcsubseries'],
    'bibxml-nist': [],
}


def test_xml2rfc_paths(
    api_root: str,
    archive_root: str,
    dirname: Optional[str] = None,
    reference_root: Optional[str] = None,
    reports_dir: Optional[str] = None,
    check_aliases: bool = False,
    randomize: bool = False,
    verbosity: int = 1,
):
    if dirname:
        dirnames = [dirname]
    else:
        dirnames = os.listdir(archive_root)

    outcomes: Dict[str, Dict[str, Any]] = dict()

    for _dirname in dirnames:
        if reports_dir:
            report, destroy_reporter = create_reporter(
                api_root,
                _dirname,
                reports_dir,
                reference_root,
            )
        else:
            report, destroy_reporter = None, None
        try:
            outcome = test_xml2rfc_dir(
                api_root,
                archive_root,
                _dirname,
                reference_root=reference_root,
                on_outcome=report,
                check_aliases=check_aliases,
                randomize=randomize,
                verbosity=verbosity,
            )
        except Exception as err:
            typer.secho(
                "Failed to test directory %s (%s)" % (dirname, err),
                err=True,
                fg='red')
            continue
        else:
            outcomes[_dirname] = outcome
        finally:
            if destroy_reporter:
                destroy_reporter()

    raise typer.Exit(code=0)


def create_reporter(
    api_root: str,
    dirname: str,
    reports_root: str,
    reference_root: Optional[str] = None,
) -> Tuple[Callable[[str, PathOutcome], None], Callable[[], None]]:
    _reports_dir = Path(reports_root)
    stats_file = open(_reports_dir / f'{dirname}-stats.log', 'w')
    report_file = open(_reports_dir / f'{dirname}-report.html', 'w')
    report_file.truncate(0)
    report_file.seek(0)
    report_file.write(f'''<!doctype html>
        <head>
        <style>
            body, html {{
                padding: 0;
                margin: 0;
            }}
            body {{
                padding: 1em;
                font-size: 14px;
                line-height: 1.2;
                font-family: sans-serif;
            }}
            h1 {{
                font-size: 120%;
            }}
            pre.xml {{
                white-space: pre-line;
                max-width: 80vw;
                overflow: auto;
                background: whiteSmoke;
                padding: 1em;
            }}
            .tools a {{
                margin-right: 1em;
            }}
        </style>
        <meta charset="utf-8">
        <title>xml2rfc path report for {dirname} directory</title>
        <body>
        <h1>xml2rfc path report for {dirname} directory</h1>
        <p>
            Testing {api_root}
            {"comparing with " if reference_root else ""}{reference_root or ""}
        <p class="tools">
            <a href="javascript:document.querySelectorAll('details').forEach(el => el.setAttribute('open', 'open'))">Open all</a>
            <a href="javascript:document.querySelectorAll('details').forEach(el => el.removeAttribute('open'))">Close all</a>
            <a href="javascript:document.querySelectorAll('details.path:not(.error)').forEach(el => el.style.display = 'none')">Hide successful paths</a>
            <a style="{"display: none" if not reference_root else ""}" href="javascript:document.querySelectorAll('details.path:not(.has-diff)').forEach(el => el.style.display = 'none')">Hide paths w/o diff</a>
            <a href="javascript:document.querySelectorAll('details.path').forEach(el => el.style.display = 'block')">Show all paths</a>
        </p>
        <details>
            <summary>Processed paths</summary>
    ''')

    stats: Stats = Stats()
    report: List[Tuple[str, PathOutcome]] = []

    def destroy():
        try:
            stats_file.close()
        except:
            pass
        try:
            report_file.write('</details>')
            report_file.write('<h2>Stats</h2>')
            report_file.write(f'<pre>{yaml.dump(dataclasses.asdict(stats))}</pre>')
        except:
            pass
        finally:
            report_file.close()

    def report_outcome(
        subpath: str,
        outcome: PathOutcome,
    ):
        basename = os.path.basename(subpath)
        test_url = f"{api_root.removesuffix('/')}/{basename}"

        if outcome.error:
            outcome_desc = f'<p>Request failed with (error possibly truncated): <pre>{html.escape(outcome.error[:500])}</pre>'
            stats.failed += 1
        elif meth := outcome.successful_method:
            outcome_desc = f'<p>{method_labels[meth.method]} succeeded'
            if meth.method == 'manual':
                stats.used_mapping += 1
            elif meth.method == 'auto':
                stats.used_auto_resolution += 1
            elif meth.method == 'fallback':
                stats.used_fallback += 1

        if reference_root and outcome.reference:
            ref_url = f"{reference_root.removesuffix('/')}/{basename}"
            reference_link = f'<p>Comparing with reference: <a href="{ref_url}">{ref_url}</a>'
        else:
            reference_link = ''

        if outcome.diff:
            xml = f'<p>Diff of effective outcome against reference: <pre class="xml">{outcome.diff}</pre>'
        elif outcome.reference:
            xml = f'<details><summary>Obtained XML is identical to reference</summary><pre class="xml">{html.escape(outcome.resulting_xml or "XML N/A")}</pre></details>'
        elif outcome.resulting_xml:
            xml = f'<details><summary>Obtained XML</summary><pre class="xml">{html.escape(outcome.resulting_xml)}</pre></details>'
        else:
            xml = ''

        report_file.write(f'''
            <details class="path {"error" if outcome.error else "success"} {"has-diff" if outcome.diff else ""}">
                <summary>
                    {dirname} / {basename}
                    — {"<strong>error ⚠️</strong>" if outcome.error else outcome.successful_method.method}
                    {"— diff available" if outcome.diff else ""}
                </summary>
                <div style="padding: 0 1em 1em 1em;">
                    <p>
                        Attempted <a href="{test_url}">{test_url}</a>
                        {outcome_desc}
                    {reference_link}
                    {xml}
                </div>
            </details>
        ''')

        stats_file.truncate(0)
        stats_file.seek(0)
        stats_file.write(yaml.dump(dataclasses.asdict(stats)))

    return report_outcome, destroy


def test_xml2rfc_dir(
    api_root: str,
    archive_root: str,
    dirname: str,
    on_outcome: Optional[Callable[[str, PathOutcome], None]],
    reference_root: Optional[str] = None,
    check_aliases: bool = False,
    randomize: bool = False,
    verbosity: int = 1,
) -> Dict[str, PathOutcome]:
    """
    Goes through each file
    under specified ``dirname`` under ``archive_root``,
    hits the appropriate URLs
    relative to ``api_root`` and ``reference_root``,
    and compares results.

    Returns a dictionary that maps each filename
    to either error
    """

    if check_aliases:
        dirnames = unalias_dirname(dirname)
        if verbosity > 1:
            typer.echo("Dirname %s unpacked to include %s" % (
                dirname,
                ', '.join(dirnames),
            ))
    else:
        dirnames = [dirname]

    xml_files = glob.glob(f'{archive_root}/{dirname}/*.xml')

    if randomize:
        random.shuffle(xml_files)

    outcomes: Dict[str, PathOutcome] = dict()

    for alias in dirnames:
        for xml_fname in tqdm(xml_files, desc="Checking paths in %s" % alias):
            basename = os.path.basename(xml_fname)
            basename_noext = os.path.splitext(basename)[0]
            outcome = test_xml2rfc_path(
                f'{dirname}/{basename}',
                api_root,
                reference_root,
            )
            if on_outcome:
                on_outcome(xml_fname, outcome)
            outcomes[xml_fname] = outcome

    return outcomes


def test_xml2rfc_path(
    subpath: str,
    api_root: str,
    reference_root: Optional[str] = None,
) -> PathOutcome:
    """
    Tests a given subpath by:

    1. Appending ``subpath`` to ``api_root``
    2. Requesting resulting URL and ensuring HTTP 200 with valid XML
       is obtained
    3. If ``reference_root`` is given, appending ``subpath``
       to it and diffing the resulting XML with XML in step (2)

    May take a while since it makes an actual request.

    :raises:
        Passes through any exception from :mod:`requests`.

    :raises ValueError:
        If HTTP 200 did not obtain or XML is not valid.

    :returns:
        2-tuple (outcome, diff) where diff will be None
        if request to reference fails or if ``reference_root`` is not given.
    """

    test_url = f"{api_root.removesuffix('/')}/{subpath}"
    test_resp = requests.get(
        test_url,
        headers={'X-Requested-With': 'xml2rfcResolver'})

    try:
        test_resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        err_resp = err.response
        outcome = PathOutcome(
            resulting_xml=None,
            error=f'HTTP {err_resp.status_code}: {err_resp.text}',
            methods_tried=get_methods_tried(err_resp.headers)[0],
        )
    else:
        methods_tried, successful_method = get_methods_tried(test_resp.headers)
        outcome = PathOutcome(
            resulting_xml=test_resp.text,
            methods_tried=methods_tried,
            successful_method=successful_method,
        )

    if reference_root and not outcome.error:
        reference_url = f"{reference_root.removesuffix('/')}/{subpath}"
        reference_result = requests.get(reference_url)
        try:
            reference_result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            pass
        else:
            outcome.reference = reference_result.text
            if outcome.reference != outcome.resulting_xml:
                diffs = dmp.diff_main(
                    outcome.reference,
                    outcome.resulting_xml,
                )
                dmp.diff_cleanupSemantic(diffs)
                outcome.diff = dmp.diff_prettyHtml(diffs)

    return outcome


def get_methods_tried(headers: Dict[str, Any]) -> Tuple[
    List[MethodOutcome],
    Optional[MethodOutcome],
]:
    """
    Given HTTP response headers, returns a 2-tuple of a list of method outcomes
    and the successful outcome, if any.
    """
    methods_tried = []
    successful_method = None

    if ';' in headers.get('x-resolution-methods', ''):
        methods = headers['x-resolution-methods'].split(';')
        outcomes = headers.get('x-resolution-outcomes', '').split(';')
        if len(methods) == len(outcomes):
            for method, outcome in zip(methods, outcomes):
                if ',' in outcome:
                    config, err = outcome.split(',')
                    outcome = MethodOutcome(
                        method=method,
                        success=err == '',
                        config=config if config != '' else None,
                        error=err if err != '' else None,
                    )
                    methods_tried.append(outcome)
                    if not err:
                        successful_method = outcome

    return methods_tried, successful_method


method_labels = {
    'auto': "Automatic resolution",
    'manual': "Mapping by primary docid",
    'fallback': "Fallback to bibxml data archive",
}


def unalias_dirname(dirname: str) -> List[str]:
    if dirname in XML2RFC_COMPAT_DIR_ALIASES:
        return [dirname, *XML2RFC_COMPAT_DIR_ALIASES[dirname]]
    else:
        raise ValueError("Unknown xml2rfc directory %s" % dirname)


if __name__ == '__main__':
    typer.run(test_xml2rfc_paths)
