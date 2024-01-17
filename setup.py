import os
import shutil
import subprocess
import json
import sys
import csv

def setup_prerequisites():
    RELEASE_DATA = {}
    with open("/etc/os-release") as f:
        reader = csv.reader(f, delimiter="=")
        for row in reader:
            if row:
                RELEASE_DATA[row[0]] = row[1]

    os_name = RELEASE_DATA['NAME']
    print(f"Detected OS: {os_name}")

    version = RELEASE_DATA['VERSION_ID']
    print(f"Detected OS Version: {version}")

    desktop_environment = os.environ.get('XDG_CURRENT_DESKTOP')
    print(f"Detected Desktop Environment: {desktop_environment}")

    if not shutil.which('jq'):
        print("jq is not installed. Installing jq...")
        subprocess.run(['dnf', 'install', '-y', '-q', 'jq'])
        print("jq installed successfully")
    else:
        print("jq is already installed")

    print("Installing RPM Fusion repository")
    subprocess.run(['dnf', 'install', '-y', '-q', f"https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-{version}.noarch.rpm"])
    subprocess.run(['dnf', 'install', '-y', '-q', f"https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-{version}.noarch.rpm"])
    print("RPM Fusion repository installed successfully")

    print("Installing Flathub repository")
    subprocess.run(['flatpak', 'remote-add', '--if-not-exists', 'flathub', 'https://flathub.org/repo/flathub.flatpakrepo'])
    print("Flathub repository installed successfully")

def process_rpm_files(package_folder):
    for root, dirs, files in os.walk(package_folder):
        for file in files:
            if file.endswith(".rpm"):
                rpm_file = os.path.join(root, file)
                print(f"Processing RPM file : {rpm_file}")
                subprocess.run(['dnf', 'install', '-y', '-q', rpm_file])

def process_flatpaks(config_file):
    if os.path.isfile(config_file):
        with open(config_file) as f:
            flatpaks = json.load(f)['flatpaks']
            for flatpak in flatpaks:
                print(f"Installing flatpak : {flatpak['name']} with id: {flatpak['id']}")
                subprocess.run(['flatpak', 'install', '-y', flatpak['id']])
    else:
        print("Config file not found")

def process_packages(config_file):
    if os.path.isfile(config_file):
        with open(config_file) as f:
            packages = json.load(f)['packages']
            for package in packages:
                print(f"Installing package : {package['name']}")
                subprocess.run(['dnf', 'install', '-y', '-q', package['name']])
    else:
        print("Config file not found")

def process_url(config_file, package_folder):
    if os.path.isfile(config_file):
        with open(config_file) as f:
            urls = json.load(f)['urls']
            for url in urls:
                print(f"Installing package {url['name']} from url : {url['url']}")
                subprocess.run(['curl', '-s', '-L', f"{url['url']}", '-o', f"{package_folder}/{url['name']}.rpm"])
    else:
        print("Config file not found")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run as root")
        subprocess.run(['sudo', 'python3'] + sys.argv)
        exit(1)

    print("Setting up prerequisites")
    working_folder = os.getcwd()
    package_folder = os.path.join(working_folder, 'packages')
    config_file = os.path.join(working_folder, 'config.json')

    setup_prerequisites()
    print("Prerequisites setup complete")
    print("Processing urls")
    process_url(config_file, package_folder)
    print("Processing packages")
    process_rpm_files(package_folder)
    print("Processing flatpaks")
    process_flatpaks(config_file)
    print("Processing packages")
    process_packages(config_file)
