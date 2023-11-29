import subprocess
import os
import sys
import tempfile
import ctypes
import json
import urllib.request
import tarfile
import shutil


def get_token(repo):
    token_url = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/{repo}:pull"
    res = urllib.request.urlopen(token_url)
    res_json = json.load(res)
    return res_json["token"]


def extract_blob(repo, sha, token, tmpdir):
    # get the blob
    url = f"https://registry.hub.docker.com/v2/library/{repo}/blobs/{sha}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    content = urllib.request.urlopen(req).read()

    # write the blob and extract it
    file = tmpdir + "/" + sha
    with open(file, "wb") as fp:
        fp.write(content)

    tar = tarfile.open(file)
    tar.extractall(tmpdir)
    tar.close()
    os.remove(file)


def get_manifest(repo, tag, token):
    url = f"https://registry.hub.docker.com/v2/library/{repo}/manifests/{tag}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            # "Accept": "application/vnd.docker.distribution.manifest.v2+json",
        },
    )
    content = urllib.request.urlopen(req)
    res_json = json.load(content)
    return res_json


def pull_image(img, tmpdir):
    if ":" in img:
        repo, tag = img.split(":")
    else:
        repo = img
        tag = "latest"
    token = get_token(repo)
    manifests = get_manifest(repo, tag, token)
    for layer in manifests["fsLayers"]:
        blobSum = layer["blobSum"]
        extract_blob(repo, blobSum, token, tmpdir)


def main():
    img = sys.argv[2]
    command = sys.argv[3]
    args = sys.argv[4:]

    TEMP_DIR = tempfile.mkdtemp()  # chroot directory
    pull_image(img, TEMP_DIR)
    os.chroot(TEMP_DIR)
    CLONE_NEWPID = 0x20000000
    libc = ctypes.cdll.LoadLibrary(None)  # type: ignore
    libc.unshare(CLONE_NEWPID)

    completed_process = subprocess.run([command, *args], capture_output=True)
    if completed_process.stdout:
        print(completed_process.stdout.decode("utf-8"), end="")
    elif completed_process.stderr:
        print(completed_process.stderr.decode("utf-8"), file=sys.stderr, end="")

    rc = completed_process.returncode
    sys.exit(rc)


if __name__ == "__main__":
    main()
