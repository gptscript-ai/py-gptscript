#!/usr/bin/env python3

import os
import sys
import platform
import requests
from tqdm import tqdm
import zipfile
import tarfile
import shutil
from pathlib import Path

# Define platform-specific variables
platform_name = platform.system().lower()
arch = platform.architecture()[0]

gptscript_info = {
    "name": "gptscript",
    "url": "https://github.com/gptscript-ai/gptscript/releases/download/",
    "version": "v0.1.4",
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
output_dir = Path(__file__).resolve().parent / "bin"
gptscript_binary_name = "gptscript" if platform_name != "windows" else "gptscript.exe"
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


def copy_binary_to_python_bin(binary_path, python_bin_dir):
    python_bin_path = python_bin_dir / binary_path.name
    shutil.copy2(binary_path, python_bin_path)


def install():
    if file_exists(gptscript_binary_path):
        print("gptscript is already installed")
        sys.exit(0)

    if os.environ.get("NODE_GPTSCRIPT_SKIP_INSTALL_BINARY") == "true":
        print("Skipping binary download")
        sys.exit(0)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Download the file
    print(f"Downloading {url}...")
    download_file(
        url,
        output_dir / f"gptscript-{gptscript_info['version']}-{pltfm}-{arch}.{suffix}",
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

    # Copy binary to Python bin directory
    print("Copying binary to Python bin directory...")
    copy_binary_to_python_bin(gptscript_binary_path, python_bin_dir)

    print("Download, extraction, and copying completed.")


if __name__ == "__main__":
    install()
