#!/usr/bin/env python3
"""
Folder Size Checker - v1 (terminal prototype)

Usage:
    python3 folder_size.py <depth>

    <depth>  How many folder levels down (from the current directory) to
             report sizes for. E.g. "2" prints the current folder, all its
             direct subfolders, and their subfolders (2 levels down),
             each with a human-readable size.

After the initial report, the script drops into an interactive prompt so
you can check other folders (by name/path, relative to the current
directory, or absolute) without restarting:

    Folder (blank = current dir) > Downloads
    Depth > 3

Every report is also written to a timestamped log file under:
    ~/Documents/Projects/FolderSizeLogs/

    folder_size_<foldername>_<mmddyyyy>.<HH>.<MM>.<SS>.txt   (24h time)

Press Enter (empty folder + depth) or Ctrl+C to quit.
"""

import os
import sys
from datetime import datetime

LOG_DIR = os.path.expanduser("~/Documents/Projects/FolderSizeLogs/")


def sizeof_fmt(num_bytes):
    """Human-readable byte size, e.g. 1234567 -> '1.2MB'."""
    num = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(num) < 1024.0:
            return f"{num:.0f}{unit}" if unit == "B" else f"{num:.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}EB"


def get_size_no_tree(path):
    """Full recursive size of a directory, without building a print tree."""
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_file():
                        total += entry.stat().st_size
                    elif entry.is_dir():
                        total += get_size_no_tree(entry.path)
                except OSError:
                    continue
    except OSError:
        pass
    return total


def build_tree(path, depth, max_depth):
    """
    Returns (total_size, children) for `path`.

    Sizes are always fully recursive (accurate), but `children` (used for
    printing) is only populated down to `max_depth` levels.
    """
    total = 0
    children = []
    try:
        with os.scandir(path) as it:
            entries = list(it)
    except OSError as e:
        print(f"  [!] Cannot read {path}: {e}", file=sys.stderr)
        return 0, []

    for entry in entries:
        try:
            if entry.is_symlink():
                continue
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                if depth < max_depth:
                    sub_total, sub_children = build_tree(entry.path, depth + 1, max_depth)
                else:
                    sub_total, sub_children = get_size_no_tree(entry.path), None
                total += sub_total
                children.append((entry.name, sub_total, sub_children))
        except OSError:
            continue

    children.sort(key=lambda c: c[1], reverse=True)
    return total, children


def render_tree(name, size, children, prefix="", is_last=True, is_root=True, lines=None):
    if lines is None:
        lines = []

    if is_root:
        lines.append(f"{name}  [{sizeof_fmt(size)}]")
        child_prefix = ""
    else:
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{name}  [{sizeof_fmt(size)}]")
        child_prefix = prefix + ("    " if is_last else "│   ")

    if children:
        for i, (c_name, c_size, c_children) in enumerate(children):
            render_tree(
                c_name, c_size, c_children,
                prefix=child_prefix,
                is_last=(i == len(children) - 1),
                is_root=False,
                lines=lines,
            )
    return lines


def analyze(path, depth):
    abs_path = os.path.abspath(os.path.expanduser(path))
    folder_name = os.path.basename(abs_path.rstrip("/")) or abs_path

    if not os.path.isdir(abs_path):
        print(f"Error: '{path}' is not a directory (resolved to {abs_path}).")
        return

    timestamp = datetime.now()
    print(f"\nScanning '{abs_path}' (depth={depth})...")

    total_size, children = build_tree(abs_path, 0, depth)
    tree_lines = render_tree(folder_name, total_size, children)

    header = [
        "Folder Size Report",
        f"Path:      {abs_path}",
        f"Depth:     {depth}",
        f"Generated: {timestamp.strftime('%m/%d/%Y %H:%M:%S')}",
        "-" * 60,
    ]

    output_lines = header + tree_lines
    report = "\n".join(output_lines)

    print()
    print(report)
    print()

    write_log(folder_name, timestamp, report)


def write_log(folder_name, timestamp, report):
    os.makedirs(LOG_DIR, exist_ok=True)
    stamp = timestamp.strftime("%m%d%Y.%H.%M.%S")
    safe_name = folder_name.replace("/", "_") or "root"
    log_path = os.path.join(LOG_DIR, f"folder_size_{safe_name}_{stamp}.txt")
    with open(log_path, "w") as f:
        f.write(report + "\n")
    print(f"Log saved: {log_path}")


def prompt_int(prompt_text):
    while True:
        raw = input(prompt_text).strip()
        if raw == "":
            return None
        try:
            value = int(raw)
            if value < 0:
                print("Depth must be 0 or greater.")
                continue
            return value
        except ValueError:
            print("Please enter a whole number (e.g. 2).")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 folder_size.py <depth>")
        print("  <depth> = how many folder levels down to report (0 = current folder only)")
        sys.exit(1)

    try:
        depth = int(sys.argv[1])
        if depth < 0:
            raise ValueError
    except ValueError:
        print("Error: <depth> must be a whole number >= 0.")
        sys.exit(1)

    analyze(".", depth)

    print("\nCheck another folder (relative to the current directory) or press Enter to quit.")
    try:
        while True:
            folder = input("\nFolder (blank = quit) > ").strip()
            if folder == "" or folder.lower() in ("q", "quit", "exit"):
                break
            new_depth = prompt_int("Depth > ")
            if new_depth is None:
                break
            analyze(folder, new_depth)
    except (KeyboardInterrupt, EOFError):
        pass

    print("\nDone.")


if __name__ == "__main__":
    main()
