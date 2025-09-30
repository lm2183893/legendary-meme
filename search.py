from ..utils import format
from .base import SubCommandBase


class SubCommand(SubCommandBase):
    name = "search"

    def main(self):
        self.search(
            self.args.name[0],
            limit=self.args.limit,
            offset=self.args.offset,
            sort=self.args.sort,
            artifact_family=self.args.family,
            platform=self.args.platform,
        )

    def search(
        self,
        name,
        limit=50,
        offset=0,
        sort="-download_count",
        artifact_family=None,
        platform=None,
    ):
        data = self.api.get_artifacts(
            name,
            limit=limit,
            offset=offset,
            sort=sort,
            artifact_family=artifact_family,
            platform=platform,
        )
        packages = data.pop("items")
        data["limit"] = limit
        data["offset"] = offset
        data["sort"] = sort
        format.format_packages(packages, data, self.log)

    def add_parser(self, subparsers):
        parser = subparsers.add_parser(
            self.name,
            help="Search in your Anaconda repository",
            description="Search in your Anaconda repository",
            epilog=__doc__,
        )
        parser.add_argument("name", nargs=1, type=str, help="Search string")
        parser.add_argument(
            "-o",
            "--offset",
            default=0,
            type=int,
            help="Offset when displaying the results",
        )
        parser.add_argument(
            "-l",
            "--limit",
            default=50,
            type=int,
            help="Offset when displaying the results",
        )
        parser.add_argument(
            "-s",
            "--sort",
            default="download_count",
            type=str,
            help="Offset when displaying the results",
        )
        parser.add_argument(
            "-f",
            "--family",
            choices=[
                "conda",
                "python",
                "cran",
                "anaconda_project",
                "anaconda_env",
                "notebook",
                "gra",
            ],
            help="Only search for packages of this Artifact Family",
        )
        parser.add_argument(
            "-p",
            "--platform",
            choices=[
                "osx-64",
                "win-32",
                "win-64",
                "linux-32",
                "linux-64",
                "linux-armv6l",
                "linux-armv7l",
                "linux-ppc64le",
                "linux-ppc64",
                "linux-s390x",
                "linux-aarch64",
                "osx-arm64",
                "zos-z",
                "noarch",
            ],
            help="only search for packages of the chosen platform",
        )
        parser.set_defaults(main=self.main)
