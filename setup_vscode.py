import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
from subprocess import CompletedProcess
import sys
import functools
import platform
from typing import Any


###################################

web_extensions: list[str] = [
    "alexandernanberg.horizon-theme-vscode",
    "christian-kohler.path-intellisense",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "github.vscode-pull-request-github",
    "ms-vscode-remote.remote-wsl",
    "ms-vscode.vscode-typescript-next",
    "ms-vsliveshare.vsliveshare",
    "pranaygp.vscode-css-peek",
    "ritwickdey.liveserver",
    "streetsidesoftware.code-spell-checker",
]

web_settings: dict = {
    "workbench.colorTheme": "Horizon",
    "files.autoSave": "afterDelay",
    "editor.formatOnSave": True,
    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "javascript.updateImportsOnFileMove.enabled": "always",
    "typescript.updateImportsOnFileMove.enabled": "always",
    "[typescript]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
    "[typescriptreact]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
    "[css]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
    "[html]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.suggest.insertMode": "replace",
    },
    "[json]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
}

test_settings: dict = {
    "files.autoSave": "afterDelay",
    "editor.formatOnSave": False,
    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "[css]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
    "[html]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "test_should_be_here": "test",
    },
    "[json]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
}


###################################


def install(args: argparse.Namespace) -> None:
    print_header("Installing")
    if args.extensions:
        print_header("Installing Extensions")

        for extension_id in web_extensions:
            subprocess.run(["code", "--install-extension", f"{extension_id}"])

        print_end()
    if args.settings:
        print_header("Installing settings")
        backup_settings_json()

        with open(find_settings_json(), "r+") as settings_file:
            settings_json: dict = json.load(settings_file)

            update_setting(settings_json, web_settings)

            print(settings_json)

            settings_file.seek(0)
            json.dump(settings_json, settings_file, indent=2)

            settings_file.close()

        print_end()

    print_header("Installing successfully")


def uninstall(args: argparse.Namespace) -> None:
    print_header("Uninstalling")
    if args.extensions:
        print_header("Uninstalling Extensions")

        for extension_id in web_extensions:
            subprocess.run(["code", "--uninstall-extension", f"{extension_id}"])

        print_end()
    if args.settings:
        print_header("Uninstalling settings")

        backup_settings: dict
        current_settings: dict

        with open(find_backup_settings_json()) as backup_file:
            backup_settings = json.load(backup_file)

        with open(find_settings_json(), "r+") as current_file:
            current_settings = json.load(current_file)

        uninstall_setting(current_settings, backup_settings, web_settings)

        with open(find_settings_json(), "r+") as current_file:
            json.dump(current_settings, current_file)

        print(current_settings)

        print_end()
    print_header("Uninstalling successfully")


def uninstall_setting(
    current_settings: dict, backup_settings: dict, applied_settings: dict
) -> None:
    for applied_key, applied_value in applied_settings.items():

        current_value: Any = current_settings.get(applied_key, None)
        backup_value: Any = backup_settings.get(applied_key, None)

        if isinstance(applied_value, dict) and isinstance(current_value, dict):
            if backup_value != None:
                uninstall_setting(current_value, backup_value, applied_value)
            else:
                for key in applied_value:
                    current_value.pop(key, None)
        else:
            if backup_value != None:
                current_settings[applied_key] = backup_value
            else:
                current_settings.pop(applied_key, None)


def update_setting(old_settings: dict[str, Any], new_settings: dict[str, Any]) -> None:
    """old_settings gets updated with the new_settings"""
    for key, value in new_settings.items():
        if isinstance(value, dict):
            if key in old_settings:
                if isinstance(old_settings[key], dict):
                    update_setting(old_settings[key], value)
                else:
                    old_settings[key] = value
            else:
                old_settings[key] = copy.deepcopy(value)
        else:
            old_settings[key] = value


def backup_settings_json() -> bool:
    print("Backing up settings.json")
    settings_path: Path = find_settings_json()
    backup_settings_path = settings_path.with_suffix(settings_path.suffix + ".backup")

    if not settings_path.exists:
        print(f"Failed to backup settings.json: settings.json is does not exists")
        return False
    if not settings_path.is_file:
        print(f"Failed to backup settings.json: settings.json is not a file")
        return False

    try:
        shutil.copy(settings_path, backup_settings_path)
        return True
    except Exception as e:
        print(f"Failed to backup settings.json: {e}")
        return False


@functools.cache
def find_settings_json() -> Path:

    # override
    # return Path(wsl_expandvars(r"%UserProfile%\Projects\vscode\settings.json"))

    if sys.platform == "win32":
        return Path(os.path.expandvars(r"%APPDATA%\Code\User\settings.json"))
    elif is_wsl():
        return Path(wsl_expandvars(r"%APPDATA%\Code\User\settings.json"))
    elif sys.platform == "linux":
        return Path(os.path.expandvars(r"$HOME/.config/Code/User/settings.json"))
    elif sys.platform == "darwin":
        return Path(
            os.path.expandvars(
                r"$HOME/Library/Application\ Support/Code/User/settings.json"
            )
        )
    else:
        sys.exit("OS not supported")


@functools.cache
def find_backup_settings_json() -> Path:
    settings_path: Path = find_settings_json()
    return settings_path.with_suffix(settings_path.suffix + ".backup")


# code gotten from here https://github.com/scivision/detect-windows-subsystem-for-linux/blob/main/is_wsl.py
@functools.cache
def is_wsl(v: str = platform.uname().release) -> bool:
    """
    detects if Python is running in WSL
    """

    if v.endswith("-Microsoft"):
        return True
    elif v.endswith("microsoft-standard-WSL2"):
        return True

    return True


def wsl_expandvars(path: str) -> str:
    result: CompletedProcess[str] = subprocess.run(
        f'wslpath -ua "$(cmd.exe /C "echo {path}")"',
        capture_output=True,
        text=True,
        shell=True,
    )

    return result.stdout.strip()


def parse_args() -> argparse.Namespace:

    global_parser = argparse.ArgumentParser(
        description=f"Setup VsCode to CrabKing's liking"
    )

    subparsers = global_parser.add_subparsers(
        title="Available Commands",
        description="Commands to install or uninstall VS Code extensions and settings",
        help="Run a command followed by --help for more information",
    )

    extensions_arg_names: tuple = ("--extensions", "-e")
    extensions_arg_template: dict = {
        "action": "store_true",
        "help": "Install or uninstall VS Code extensions",
    }

    settings_arg_names: tuple = ("--settings", "-s")
    settings_arg_template: dict = {
        "action": "store_true",
        "help": "Apply or remove custom VS Code settings",
    }

    install_parser = subparsers.add_parser("install", help="installs stuff")
    install_parser.add_argument(*extensions_arg_names, **extensions_arg_template)
    install_parser.add_argument(*settings_arg_names, **settings_arg_template)
    install_parser.set_defaults(func=install)

    uninstall_parser = subparsers.add_parser("uninstall", help="uninstall stuff")
    uninstall_parser.add_argument(*extensions_arg_names, **extensions_arg_template)
    uninstall_parser.add_argument(*settings_arg_names, **settings_arg_template)
    uninstall_parser.set_defaults(func=uninstall)

    return global_parser.parse_args()


def print_header(title: str, width: int = 40) -> None:
    title_size: int = len(title)
    half_size: int = (width - (title_size + 2)) // 2

    print("=" * half_size + f" {title} " + "=" * half_size)


def print_end(width: int = 40) -> None:
    print("=" * width)


def main() -> None:
    args: argparse.Namespace = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
