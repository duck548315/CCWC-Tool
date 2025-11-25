import sys
import os

def get_file_bytes(filename):
    """
    Calculates the size of a file in bytes.
    You can use the "wc -c <filename>" command.
    
    Args: 
        filename (str): The path to the file to be measured.

    Return:
        int: The size of the file in bytes.
    
    Raises:
        SystemExit: If the file is not found or cannot be read due to the permission errors.
    """
    try:
        with open(filename, 'rb') as f:
            file = f.read()
            return len(file)
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    except PermissionError:
        print(f"Error: Permission denied for reading '{filename}'.")
        sys.exit(1)

    except Exception as e:
        print("Error: An unknown error occurred: {e}")

def main():
    """
    Main entry point for the ccwc tool.
    Parsed command-line arguments and executes the requested operation.
    """

    args = sys.argv

    if len(args) != 3:
        print("Usage: mvcc -c <filename>")

    command = args[1]
    filename = args[2]

    if command == "-c":
        byte_counts = get_file_bytes(filename)
        print(f"  {byte_counts} {filename}")
    else:
        print(f"Unknown command '{command}'.")

if __name__ == "__main__":
    main()