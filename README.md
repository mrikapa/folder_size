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
