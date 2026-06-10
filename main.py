import argparse
import logging
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse

LOCAL_TIMEOUT = 30  # [s]
NET_TIMEOUT = 300  # [s]


logger = logging.getLogger(__name__)


def fetch_archive(url: str, dest: Path) -> Path:
    logging.info("downloading %s", url)

    logging.debug("opening connection with %s", url)
    # using LOCAL_TIMEOUT instead of NET_TIMEOUT since this is per-socket, not per-download
    # it's gross … whatever
    with urllib.request.urlopen(url, timeout=LOCAL_TIMEOUT) as r:
        name = None
        cd = r.headers.get("Content-Disposition")
        if cd and "filename=" in cd:
            name = cd.split("filename=")[-1].strip().strip('"')
        if not name:
            name = Path(unquote(urlparse(r.url).path)).name

        archive = dest / name
        with open(archive, "wb") as f:
            logger.debug("downloading archive to %s", archive)
            shutil.copyfileobj(r, f)

    logger.info("successfully downloaded")
    if zipfile.is_zipfile(archive):
        logger.debug("opening %s", archive)
        with zipfile.ZipFile(archive) as z:
            logger.info("extracting archive")
            top = z.namelist()[0].split("/")[0]
            z.extractall(dest)
            logger.debug("extracted into %s", dest / top)
    elif tarfile.is_tarfile(archive):
        logger.debug("opening %s", archive)
        with tarfile.open(archive) as t:
            logger.info("extracting archive")
            top = t.getnames()[0].split("/")[0]
            t.extractall(dest, filter="data")
            logger.debug("extracted into %s", dest / top)
    else:
        raise RuntimeError(f"unknown archive format: {archive}")

    logger.info("successfully extracted")
    return dest / top


def fetch_git(url: str, hash: str, dest: Path):
    logger.info("fetching %s at %s", url, hash)
    try:
        logger.debug("attempting to fetch by SHA")
        logger.debug("initializing a git repository")
        subprocess.run(
            ["git", "init", dest],
            timeout=LOCAL_TIMEOUT,
            check=True,
        )
        logger.debug("adding the remote: %s", url)
        subprocess.run(
            ["git", "-C", dest, "remote", "add", "origin", url],
            timeout=LOCAL_TIMEOUT,
            check=True,
        )
        logger.debug("fetching the remote: %s", url)
        subprocess.run(
            ["git", "-C", dest, "fetch", "--depth", "1", "origin", hash],
            timeout=NET_TIMEOUT,
            check=True,
        )
        logger.debug("checking out commit: %s", hash)
        subprocess.run(
            ["git", "-C", dest, "checkout", "FETCH_HEAD"],
            timeout=LOCAL_TIMEOUT,
            check=True,
        )
    except subprocess.CalledProcessError:
        logger.debug("shallow fetch by SHA failed, falling back to full clone")
        logger.debug("cleaning %s", dest)
        shutil.rmtree(dest, ignore_errors=True)
        logger.debug("cloning: %s", url)
        subprocess.run(
            ["git", "clone", url, dest],
            timeout=NET_TIMEOUT,
            check=True,
        )
        logger.debug("checking out commit: %s", hash)
        subprocess.run(
            ["git", "-C", dest, "checkout", hash],
            timeout=LOCAL_TIMEOUT,
            check=True,
        )

    logger.info("successfully cloned and checked out")


def parse_arguments() -> argparse.Namespace:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "-V",
        help='package version to be used in `when("@<ver>")` constructions',
        metavar="package version",
    )
    common.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="output verbose logging messages for debugging purposes",
    )

    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(title="source type", dest="command", required=True)

    parser_archive = subparser.add_parser(
        "archive", help="source is a link to an archive (.tar.gz, .zip, etc.)", parents=[common]
    )
    parser_archive.add_argument("url", help="URL to a source archive")

    parser_git = subparser.add_parser(
        name="git", help="source is a Git URL and commit hash", parents=[common]
    )
    parser_git.add_argument("git_url", help="URL to an Git repository", metavar="git-url")
    parser_git.add_argument("hash", help="Git commit hash")

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    # configure logging
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    # set up a temp directory
    logger.debug("setting up temporary working directory")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        logger.debug("temporary working directory created: %s", tmp_dir)

        # get the tarball or check out the git repo at the specified tag
        src_dir = tmp_dir
        if args.command == "archive":
            src_dir = fetch_archive(args.url, tmp_dir)
        elif args.command == "git":
            fetch_git(args.git_url, args.hash, tmp_dir)
        else:
            logger.critical("unhandled subcommand")
            return 1
        logger.debug("source is ready for scanning at %s", src_dir)

        input("press enter to continue")

        # find the go.mod or the go.sum; may not be at the repository root

        # determine the dependencies

        # delegate to resources.py for turning those dependencies into resource() directives

        # print the resource directives to stdout

    return 0


if __name__ == "__main__":
    sys.exit(main())
