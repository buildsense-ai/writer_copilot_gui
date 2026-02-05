#!/usr/bin/env python3
"""
Paper-CLI Launcher
Run this from anywhere to use the Paper-CLI assistant.
"""
import sys
import os


def resolve_cli_dir() -> str:
    if __file__:
        return os.path.dirname(os.path.abspath(__file__))

    possible_paths = [
        os.path.join(os.path.expanduser("~"), "Documents", "apps", "cli_first_app"),
        os.path.join(os.path.expanduser("~"), "apps", "cli_first_app"),
        os.path.join(os.getcwd(), "cli_first_app"),
    ]
    for candidate in possible_paths:
        if os.path.isdir(candidate):
            return candidate

    raise RuntimeError("Could not resolve CLI directory")


CLI_DIR = resolve_cli_dir()
sys.path.insert(0, CLI_DIR)
os.chdir(CLI_DIR)

from src.main import app

if __name__ == "__main__":
    # Change back to original directory for actual work
    import subprocess
    result = subprocess.run([sys.executable, "-m", "src.main"] + sys.argv[1:], cwd=CLI_DIR)
    sys.exit(result.returncode)
