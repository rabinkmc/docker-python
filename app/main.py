import subprocess
import os
import sys
import tempfile


def main():
    command = sys.argv[3]
    args = sys.argv[4:]

    TEMP_DIR = tempfile.mkdtemp()
    directory = TEMP_DIR + command[: command.rfind("/")]
    os.makedirs(directory, exist_ok=True)
    subprocess.run(
        [
            "cp",
            "-r",
            command,
            directory,
        ]
    )
    os.chroot(TEMP_DIR)
    completed_process = subprocess.run([command, *args], capture_output=True)
    if completed_process.stdout:
        print(completed_process.stdout.decode("utf-8"), end="")
    elif completed_process.stderr:
        print(completed_process.stderr.decode("utf-8"), file=sys.stderr, end="")

    rc = completed_process.returncode
    sys.exit(rc)


if __name__ == "__main__":
    main()
