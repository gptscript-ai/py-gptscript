#!/usr/bin/env python3

import os
import platform
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

# Define platform-specific variables
platform_name = platform.system().lower()

machine = platform.machine().lower()
if machine in ["x86_64", "amd64"]:
    arch = "amd64"
elif machine in ["aarch64", "arm64"]:
    arch = "arm64"
else:
    # Handle other architectures or set a default/fallback
    arch = "unknown"
    print(f"Warning: Unhandled architecture '{machine}'. This may not be supported.")

gptscript_info = {
    "name": "gptscript",
    "url": "https://github.com/gptscript-ai/gptscript/releases/download/",
    "version": "v0.9.2",
}

pltfm = {"windows": "windows", "linux": "linux", "darwin": "macOS"}.get(
    platform_name, None
)

if platform_name == "darwin":
    arch = "universal"

suffix = {"windows": "zip", "linux": "tar.gz", "darwin": "tar.gz"}.get(
    platform_name, None
)

if not pltfm or not suffix:
    print("Unsupported platform:", platform_name)
    sys.exit(1)

url = f"{gptscript_info['url']}{gptscript_info['version']}/gptscript-{gptscript_info['version']}-{pltfm}-{arch}.{suffix}"

# Define output directory
output_dir = Path(__file__).resolve().parent / ".." / "scratch"
gptscript_binary_name = "gptscript" + (".exe" if platform_name == "windows" else "")
gptscript_binary_path = output_dir / gptscript_binary_name

# Define Python bin directory
python_bin_dir = Path(sys.executable).parent


def file_exists(file_path):
    return file_path.exists()


def download_file(url, save_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024
    progress_bar = tqdm(total=total_size, unit="B", unit_scale=True)

    with open(save_path, "wb") as f:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            f.write(data)

    progress_bar.close()


def extract_zip(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)


def extract_tar_gz(tar_path, extract_dir):
    with tarfile.open(tar_path, "r:gz") as tar_ref:
        tar_ref.extractall(extract_dir)


def copy_binary_to_python_bin(binary_path, target):
    shutil.copy2(binary_path, target)
    print(f"Binary copied to {target}")


def symlink_versioned_binary_to_bin(versioned_binary_path, python_bin_dir):
    symlink_name = "gptscript" + (".exe" if platform_name == "windows" else "")
    symlink_path = python_bin_dir / symlink_name

    if symlink_path.is_symlink():
        existing_target = Path(os.readlink(symlink_path))
        if existing_target != versioned_binary_path:
            symlink_path.unlink()  # Remove the old symlink if it doesn't point to the correct versioned binary
            symlink_path.symlink_to(versioned_binary_path)
            print(f"Symlink updated to point to {versioned_binary_path}.")
        else:
            print("Symlink is already up to date.")
    else:
        # If the path exists but is not a symlink (i.e., a regular file or directory), remove it before creating a symlink
        if symlink_path.exists():
            symlink_path.unlink()
        symlink_path.symlink_to(versioned_binary_path)
        print(f"Symlink created to point to {versioned_binary_path}.")


def install():
    versioned_binary_name = f"gptscript-{gptscript_info['version']}" + (
        ".exe" if platform_name == "windows" else ""
    )
    versioned_binary_path = python_bin_dir / versioned_binary_name

    if versioned_binary_path.exists():
        print(f"{versioned_binary_name} is already installed.")
    else:
        if os.environ.get("GPTSCRIPT_SKIP_INSTALL_BINARY") == "true":
            print("Skipping binary download")
            sys.exit(0)

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download the file
        print(f"Downloading {url}...")
        download_file(
            url,
            output_dir
            / f"gptscript-{gptscript_info['version']}-{pltfm}-{arch}.{suffix}",
        )

        # Extract the file
        print("Extracting...")
        if suffix == "zip":
            extract_zip(
                output_dir
                / f"gptscript-{gptscript_info['version']}-{pltfm}-{arch}.{suffix}",
                output_dir,
            )
        elif suffix == "tar.gz":
            extract_tar_gz(
                output_dir
                / f"gptscript-{gptscript_info['version']}-{pltfm}-{arch}.{suffix}",
                output_dir,
            )

        # Find the extracted binary and rename/move it to the versioned name in the python bin directory
        extracted_binary_path = next(
            output_dir.glob(gptscript_binary_name), None
        )  # Adjust the glob pattern if necessary
        if extracted_binary_path:
            shutil.move(str(extracted_binary_path), str(versioned_binary_path))
            print(f"Copied {extracted_binary_path} to {versioned_binary_path}")

        # Remove the output directory
        print("Removing the output directory...")
        shutil.rmtree(output_dir)

    # Update the symlink to point to the new version
    symlink_versioned_binary_to_bin(versioned_binary_path, python_bin_dir)

    print("Installation or update completed.")


if __name__ == "__main__":
    install()
