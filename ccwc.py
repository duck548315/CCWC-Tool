import sys
import os
import stat
import argparse
from contextlib import contextmanager

def count_bytes(file):
    """
    Calculates the size of a file in bytes.
    Callback function for "wc -c <filename>" command.
    """
    try:
        fd = file.fileno()
        file_stat = os.fstat(fd)

        # If it is a pipe (S_ISFIFO), st_size is 0, so we must read content.
        if stat.S_ISREG(file_stat.st_mode):
            # Get file size directly from file descriptor metadata. O(1)
            return file_stat.st_size
        
        else:
            # For pipes, read content to count bytes.
            count = 0
            buffer_size = 1024 * 1024 # Read 1MB at a time

            while True:
                chunk = file.read(buffer_size)
                if not chunk: break
                count += len(chunk)

            return count
    
    except (OSError, AttributeError):
        # Fallback to streams that don't support stat (like stdin pipes).
        return len(file.read())
    
def count_lines(file):
    """
    Calculates the size of a file in lines.
    Callback function for "wc -l <filename>" command.
    """
    count = 0
    buffer_size = 1024 * 1024 # Read 1MB at a time

    while True:
        chunk = file.read(buffer_size)
        if not chunk: break
        count += chunk.count(b'\n')

    return count

@contextmanager
def get_stream(filename = None):
    """
    Context manager that yields a file object.
    Open a file if filename is provided, otherwise yields stdin buffer.
    Automatically closes the file if it was opened.
    """
    if filename:
        try:
            f = open(filename, 'rb')
            yield f

        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            sys.exit(1)

        except PermissionError:
            print(f"Error: Permission denied for reading '{filename}'.")
            sys.exit(1)

        except Exception as e:
            print("Error: An unknown error occurred: {e}")
            sys.exit(1)

        finally:
            f.close()

    else:
        yield sys.stdin.buffer

def produce_count_result(args, func):
    """Orchestrates the result based on parsed arguments."""
    #Use context manager to handle file opening/closing
    with get_stream(args.filename) as f:
        try:
            result = func(f)
    
        except Exception as e:
            print(f"Error during processing: {e}")
            sys.exit(1)

    #Output formatting
    if args.filename:
        print(f"  {result} {args.filename}")
    else:
        print(f"  {result}")

def create_parser():
    """Creates and configures the argument parser."""
    parser = argparse.ArgumentParser(
        description = "ccsc - Build your own wc tool.",
        prog = "ccwc"
    )

    group = parser.add_mutually_exclusive_group(required = True)

    group.add_argument(
        "-c", "--bytes",
        action = "store_true",
        help = "print the byte counts"
    )

    group.add_argument(
        "-l", "--lines",
        action = "store_true",
        help = "print the newline counts"
    )

    parser.add_argument(
        "filename",
        nargs = '?',
        help = "file to process (default: stdin)"
    )

    return parser

def main():
    """
    Main entry point for the ccwc tool.
    Parsed command-line arguments and executes the requested operation.
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.bytes:
        produce_count_result(args, count_bytes)
    if args.lines:
        produce_count_result(args, count_lines)

if __name__ == "__main__":
    main()