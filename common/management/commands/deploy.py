import getpass
import os
import subprocess
import re
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand

"""
This management command deploys the project to remote servers using rsync.

This requires the remote cloud provider to have rsync installed and accessible.
- Provider must allow inbound SSH connections
- Provider must provide ability to set up custom SSH keys
- Provider must allow to update root password
- Provider must support rsync for file transfers

REQUIREMENTS::
- `exclude.txt` file must be located in the project root
"""


from dotenv import load_dotenv

load_dotenv(override=True)

# All remote source should be located in this path
DEFAULT_PATH = "~/src/"
DEFAULT_SSH_KEY = os.getenv("DEFAULT_SSH_KEY")
REMOTE_SERVERS = [
    {
        "provider": "Linode",
        "name": "prod1",
        "user": "root",
        "host": "192.46.237.119",
    },
    # Add more servers here
]

SETTINGS_FILE = Path("./core/settings.py")
VERSION_RE = re.compile(
    r'^VERSION\s*=\s*"(?P<date>\d{4}\.\d{2}\.\d{2})\+(?P<build>\d+)"',
    re.MULTILINE,
)


def next_version():
    today = datetime.now().strftime("%Y.%m.%d")
    content = SETTINGS_FILE.read_text()
    match = VERSION_RE.search(content)

    if not match:
        # First deploy ever
        return f"{today}+1"

    last_date = match.group("date")
    last_build = int(match.group("build"))

    if last_date == today:
        return f"{today}+{last_build + 1}"

    # New day → reset build
    return f"{today}+1"


class Command(BaseCommand):
    help = "Update version and deploy project using rsync"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default="~/src/",
            help="Remote project path",
        )
        parser.add_argument(
            "--key",
            type=str,
            default=DEFAULT_SSH_KEY,
            help="SSH private key local path",
        )

    def handle(self, *args, **options):
        # 1️⃣ Dynamically update VERSION in settings.py
        new_version = self.update_settings()
        self.stdout.write(self.style.SUCCESS(f"Updated VERSION to {new_version}"))

        # 2️⃣ Loop over servers
        for server in REMOTE_SERVERS:
            remote = f"{server['user']}@{server['host']}"
            self.stdout.write(
                self.style.SUCCESS(f"Deploying to {server['name']} ({remote})")
            )
            self.rsync_deploy(
                remote=remote,
                path=options["path"],
                key=options["key"],
            )

    def get_next_build(self, today):
        try:
            tags = (
                subprocess.check_output(["git", "tag", "--list", f"v{today}*"])
                .decode()
                .splitlines()
            )
            builds = [int(tag.split("+")[-1]) for tag in tags if "+" in tag]
            return max(builds) + 1 if builds else 1
        except Exception:
            return 1

    def update_settings(self):
        new_version = next_version()
        content = SETTINGS_FILE.read_text()

        if VERSION_RE.search(content):
            content = VERSION_RE.sub(
                f'VERSION = "{new_version}"',
                content,
            )
        else:
            content += f'\nVERSION = "{new_version}"\n'

        SETTINGS_FILE.write_text(content)
        return new_version

    def rsync_deploy(self, remote, path, key):
        rsync_command = [
            "rsync",
            "-avz",
            "--delete",
            "--exclude-from=./exclude.txt",
            "-e",
            f"ssh -i {key}",
            "./",  # django project root (directory containing manage.py)
            f"{remote}:{path}",
        ]

        self.stdout.write(self.style.SUCCESS(f"Running: {' '.join(rsync_command)}"))
        subprocess.run(rsync_command)
