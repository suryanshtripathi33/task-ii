# =============================================================================
#
#   INTELLIGENT FILE ORGANIZER
#   Kinetrexa Software Private Limited — Internship Automation Project
#
#   Intern Name     : Suryansh Tripathi
#   Application ID  : 59JDLQTW
#   Company         : Kinetrexa Software Private Limited
#   Language        : Python 3.8+
#   Libraries Used  : os, shutil, pathlib, logging, datetime (all built-in)
#
#   Description:
#       This script automatically scans a target directory and sorts every
#       file into a named sub-folder based on its extension.  It logs each
#       move operation (with a timestamp) to 'organizer.log' so there is a
#       full audit trail — no file is ever moved silently.
#
# =============================================================================

import os
import shutil
import logging

from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# SECTION 1 — FILE-CATEGORY MAPPING (Dictionary-based, human-optimized)
# ---------------------------------------------------------------------------
# Using a dictionary instead of a chain of if-elif statements keeps the
# mapping data-driven and easy to extend without touching any logic code.
# To add a new category, just add a new key-value pair here.

FILE_CATEGORIES: dict[str, list[str]] = {
    "Images":       [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
                     ".webp", ".tiff", ".ico", ".heic"],
    "Documents":    [".pdf", ".doc", ".docx", ".odt", ".txt", ".rtf",
                     ".md", ".tex", ".pages", ".epub"],
    "Spreadsheets": [".xls", ".xlsx", ".ods", ".csv", ".tsv"],
    "Presentations":[".ppt", ".pptx", ".odp", ".key"],
    "Audio":        [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a",
                     ".wma", ".opus"],
    "Video":        [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
                     ".webm", ".m4v", ".3gp"],
    "Archives":     [".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
                     ".xz", ".iso"],
    "Code":         [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h",
                     ".cs", ".go", ".rb", ".php", ".swift", ".kt",
                     ".rs", ".html", ".css", ".json", ".xml", ".yaml",
                     ".yml", ".toml", ".sh", ".bat", ".ps1"],
    "Databases":    [".db", ".sqlite", ".sqlite3", ".mdb", ".accdb",
                     ".sql"],
    "Fonts":        [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "Executables":  [".exe", ".msi", ".app", ".apk", ".deb", ".rpm",
                     ".dmg", ".bin"],
    "Misc":         [],   # Catch-all — populated dynamically at runtime
}


# ---------------------------------------------------------------------------
# SECTION 2 — LOGGING SETUP
# ---------------------------------------------------------------------------
# Professional scripts never rely on bare print() for critical operations.
# Python's built-in logging module writes timestamped entries to a log file
# AND mirrors INFO+ messages to the console simultaneously.

def setup_logger(log_dir: Path) -> logging.Logger:
    """
    Configure and return a logger that writes to both a rotating log file
    inside *log_dir* and to the console (stdout).

    Args:
        log_dir (Path): Directory where 'organizer.log' will be created.

    Returns:
        logging.Logger: Configured logger instance.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "organizer.log"

    logger = logging.getLogger("FileOrganizer")
    logger.setLevel(logging.DEBUG)  # Capture everything; handlers filter

    # --- File handler: full DEBUG-level detail with timestamps ---
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    # --- Console handler: INFO+ only (less noise in the terminal) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(fmt="%(levelname)-8s | %(message)s")
    console_handler.setFormatter(console_fmt)

    # Avoid adding duplicate handlers if the function is called more than once
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# ---------------------------------------------------------------------------
# SECTION 3 — CORE ORGANIZER CLASS
# ---------------------------------------------------------------------------

class FileOrganizer:
    """
    Scans a source directory and moves every file into a categorised
    sub-folder based on FILE_CATEGORIES.

    Attributes:
        source_dir (Path): The directory to scan and organise.
        logger     (logging.Logger): Logger for audit-trail output.
        _script_path (Path): Absolute path of *this* script — used for
                             the safety check that prevents self-deletion.
    """

    def __init__(self, source_dir: str | Path) -> None:
        """
        Initialise the organiser for a given directory.

        Args:
            source_dir (str | Path): Path to the folder to organise.

        Raises:
            FileNotFoundError: If *source_dir* does not exist.
            NotADirectoryError: If *source_dir* is a file, not a folder.
        """
        self.source_dir: Path = Path(source_dir).resolve()

        # Validate the target directory up-front
        if not self.source_dir.exists():
            raise FileNotFoundError(
                f"Source directory not found: '{self.source_dir}'"
            )
        if not self.source_dir.is_dir():
            raise NotADirectoryError(
                f"Provided path is not a directory: '{self.source_dir}'"
            )

        # Store the absolute path of this script for the safety check
        self._script_path: Path = Path(__file__).resolve()

        # Log file lives in a hidden sub-folder so it is never accidentally moved
        log_dir: Path = self.source_dir / ".organizer_logs"
        self.logger: logging.Logger = setup_logger(log_dir)

        # Runtime statistics
        self._stats: dict[str, int] = {
            "moved":   0,
            "skipped": 0,
            "errors":  0,
        }

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _get_category(self, extension: str) -> str:
        """
        Return the category name for a given file *extension*.

        The lookup is O(n_categories) but since there are fewer than 15
        categories this is negligible compared to any I/O operation.

        Args:
            extension (str): Lowercase file extension, e.g. '.pdf'.

        Returns:
            str: A key from FILE_CATEGORIES, defaulting to 'Misc'.
        """
        for category, extensions in FILE_CATEGORIES.items():
            if extension in extensions:
                return category
        return "Misc"

    def _resolve_destination(self, dest_dir: Path, file_path: Path) -> Path:
        """
        Return a unique destination path, appending a counter suffix if a
        file with the same name already exists in *dest_dir*.

        Example:
            report.pdf  →  report_1.pdf  →  report_2.pdf …

        Args:
            dest_dir  (Path): Target sub-folder.
            file_path (Path): The source file whose name will be reused.

        Returns:
            Path: A destination path guaranteed not to exist yet.
        """
        dest_path: Path = dest_dir / file_path.name

        if not dest_path.exists():
            return dest_path

        # Build a unique name by appending an incrementing counter
        stem      = file_path.stem
        suffix    = file_path.suffix
        counter   = 1

        while dest_path.exists():
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter  += 1

        self.logger.debug(
            "Name collision resolved → '%s'", dest_path.name
        )
        return dest_path

    def _is_safe_to_move(self, file_path: Path) -> bool:
        """
        Safety check — return False for files that must never be moved.

        Currently protects:
        * This script itself.
        * The organiser's own log directory.
        * Hidden files / folders (dot-prefixed).

        Args:
            file_path (Path): Candidate file path.

        Returns:
            bool: True if the file may be moved; False otherwise.
        """
        # Do NOT move this script
        if file_path.resolve() == self._script_path:
            self.logger.warning(
                "SAFETY CHECK — skipping script itself: '%s'", file_path.name
            )
            return False

        # Do NOT move anything inside the log folder
        if ".organizer_logs" in file_path.parts:
            return False

        # Skip hidden files (dot-files) — treat them as system/config files
        if file_path.name.startswith("."):
            self.logger.debug(
                "Skipping hidden file: '%s'", file_path.name
            )
            return False

        return True

    def _move_file(self, file_path: Path) -> None:
        """
        Determine the destination category folder, resolve any name
        collisions, then perform the actual move with shutil.move().

        Args:
            file_path (Path): Absolute path of the file to move.
        """
        extension: str = file_path.suffix.lower()
        category: str  = self._get_category(extension)

        dest_dir: Path = self.source_dir / category
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path: Path = self._resolve_destination(dest_dir, file_path)

        try:
            # shutil.move() works across different disk partitions —
            # a plain rename/os.rename() would fail in that case.
            shutil.move(str(file_path), str(dest_path))

            self.logger.info(
                "MOVED   %-40s  →  %s/%s",
                file_path.name,
                category,
                dest_path.name,
            )
            self._stats["moved"] += 1

        except PermissionError as exc:
            self.logger.error(
                "PERMISSION DENIED — cannot move '%s': %s",
                file_path.name, exc
            )
            self._stats["errors"] += 1

        except FileNotFoundError as exc:
            self.logger.error(
                "FILE NOT FOUND — '%s' vanished before move: %s",
                file_path.name, exc
            )
            self._stats["errors"] += 1

        except shutil.Error as exc:
            # Covers shutil-specific problems (e.g. dest already exists
            # despite our check — rare race condition on multi-user systems)
            self.logger.error(
                "SHUTIL ERROR — '%s': %s", file_path.name, exc
            )
            self._stats["errors"] += 1

        except OSError as exc:
            # Catch-all for unexpected OS-level errors
            self.logger.error(
                "OS ERROR — '%s': %s", file_path.name, exc
            )
            self._stats["errors"] += 1

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def organise(self) -> dict[str, int]:
        """
        Main entry point. Iterates over all top-level files in source_dir,
        applies the safety check, and moves each eligible file.

        Returns:
            dict[str, int]: A summary with 'moved', 'skipped', 'errors'.
        """
        self.logger.info("=" * 65)
        self.logger.info("Kinetrexa Software — Intelligent File Organizer")
        self.logger.info("Intern : Suryansh Tripathi  |  ID : 59JDLQTW")
        self.logger.info("Session started : %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.logger.info("Target directory: %s", self.source_dir)
        self.logger.info("=" * 65)

        # Collect only files (not sub-directories) at the top level
        all_items = list(self.source_dir.iterdir())
        files     = [item for item in all_items if item.is_file()]

        if not files:
            self.logger.info("No files found in '%s'. Nothing to do.", self.source_dir)
            return self._stats

        self.logger.info("Found %d file(s) to evaluate.", len(files))

        for file_path in files:
            if not self._is_safe_to_move(file_path):
                self._stats["skipped"] += 1
                continue
            self._move_file(file_path)

        # --- Session summary ---
        self.logger.info("-" * 65)
        self.logger.info(
            "SUMMARY  |  Moved: %d  |  Skipped: %d  |  Errors: %d",
            self._stats["moved"],
            self._stats["skipped"],
            self._stats["errors"],
        )
        self.logger.info("Session ended : %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.logger.info("=" * 65)

        return self._stats

    def preview(self) -> None:
        """
        Dry-run mode — prints what *would* happen without moving anything.
        Useful for verifying the mapping before committing to changes.
        """
        print("\n" + "=" * 65)
        print("  DRY RUN — No files will be moved")
        print("=" * 65)

        all_items = list(self.source_dir.iterdir())
        files     = [item for item in all_items if item.is_file()]

        if not files:
            print("  No files found.")
            return

        for file_path in files:
            if not self._is_safe_to_move(file_path):
                print(f"  SKIP    {file_path.name}")
                continue

            extension = file_path.suffix.lower()
            category  = self._get_category(extension)
            print(f"  WOULD MOVE  {file_path.name:<40}  →  {category}/")

        print("=" * 65 + "\n")


# ---------------------------------------------------------------------------
# SECTION 4 — COMMAND-LINE ENTRY POINT
# ---------------------------------------------------------------------------

def main() -> None:
    """
    CLI entry point.

    Usage examples:
        # Organise the current working directory
        python intelligent_file_organizer.py

        # Organise a specific folder
        python intelligent_file_organizer.py /path/to/folder

        # Preview without moving anything
        python intelligent_file_organizer.py /path/to/folder --preview
    """
    import sys

    # ---- Parse minimal CLI arguments (no external library needed) ----------
    args         = sys.argv[1:]
    preview_mode = "--preview" in args
    path_args    = [a for a in args if not a.startswith("--")]

    # Default to the current working directory if no path is provided
    target = path_args[0] if path_args else os.getcwd()

    print()
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║       KINETREXA SOFTWARE PRIVATE LIMITED                 ║")
    print("  ║       Intelligent File Organizer  v1.0.0                 ║")
    print("  ║       Intern : Suryansh Tripathi  |  ID : 59JDLQTW       ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print()

    try:
        organizer = FileOrganizer(source_dir=target)

        if preview_mode:
            organizer.preview()
        else:
            stats = organizer.organise()
            print(
                f"\n  ✅  Done!  Moved: {stats['moved']}  |  "
                f"Skipped: {stats['skipped']}  |  "
                f"Errors: {stats['errors']}"
            )
            print(f"  📄  Full log saved to: {Path(target).resolve() / '.organizer_logs' / 'organizer.log'}\n")

    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"\n  ❌  Error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
