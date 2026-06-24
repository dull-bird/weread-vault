"""PyInstaller entry point for the standalone Win/Mac builds.

Double-clicking the binary (no arguments) starts the local dashboard and opens the
browser. Run it from a terminal with the usual subcommands for everything else, e.g.
``weread-vault-macos sync`` or ``weread-vault-windows.exe update``.
"""

from __future__ import annotations

import sys

from weread_vault.cli import main

if __name__ == "__main__":
    args = sys.argv[1:] or ["serve", "--open"]
    main(args)
