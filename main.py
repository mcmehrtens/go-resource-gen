import argparse


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "-V",
        help='package version to be used in `when("@<ver>")` constructions',
        metavar="package version",
    )

    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(title="source type", required=True)

    parser_archive = subparser.add_parser(
        "archive", help="source is a link to an archive (.tar.gz, .zip, etc.)", parents=[common]
    )
    parser_archive.add_argument("url", help="URL to a source archive")

    parser_git = subparser.add_parser(
        name="git", help="source is a Git URL and commit hash", parents=[common]
    )
    parser_git.add_argument("git-url", help="URL to an Git repository")
    parser_git.add_argument("hash", help="Git commit hash")

    args = parser.parse_args()


if __name__ == "__main__":
    main()
