import sys
import os
import stat
import argparse
import codecs
from contextlib import contextmanager

class CCWC:
    """
    A class to handle Word Count operations.
    Encapsulates configuration (buffer size, encoding) and logic.
    """
    DEFAULT_BUFFER_SIZE = 64 * 1024

    def __init__(self, buffer_size = DEFAULT_BUFFER_SIZE, encoding = 'utf-8'):
        self.buffer_size = buffer_size
        self.encoding = encoding

    # Helper function (refactored)
    def _read_chunks(self, file):
        """Generator that yields chunks of data from a file object."""
        while True:
            chunk = file.read(self.buffer_size)
            if not chunk: break
            yield chunk

    # Logical layer
    def count_bytes(self, file):
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
                # Load the whole file into memory.
                if self.buffer_size == 0:
                    return len(file.read())
                
                total = 0
                for chunk in self._read_chunks(file):
                    total += len(chunk)
                return total
        
        except (OSError, AttributeError):
            # Fallback to streams that don't support stat (like stdin pipes).
            if self.buffer_size == 0:
                return len(file.read())
                
            total = 0
            for chunk in self._read_chunks(file):
                total += len(chunk)
            return total
        
    def count_lines(self, file):
        """
        Calculates the size of a file in lines.
        Callback function for "wc -l <filename>" command.
        """
        # Load the whole file into memory.
        if self.buffer_size == 0:
            return file.read().count(b'\n')
                
        total = 0
        for chunk in self._read_chunks(file):
            total += chunk.count(b'\n')

        return total

    def count_words(self, file):
        """
        Calculates the size of a file in words.
        Callback function for "wc -w <filename>" command.
        """
        if self.buffer_size == 0:
            try:
                content = file.read().decode(self.encoding, errors = 'ignore')

            except LookupError:
                print(f"Error: Unknown encoding: '{self.encoding}'.")

            except Exception:
                file.seek(0)
                content = str(file.read())

            return len(content.split())

        total = 0
        # Check if the previous chunk ended with space.
        last_char_was_space = True

        for chunk in self._read_chunks(file):
            words = chunk.split()
            total += len(words)

            # Check if the current chunk starts with space
            first_char_is_space = chunk[0:1].isspace()

            # If they both are word, it means we split a single word, so subtract 1.
            if not last_char_was_space and not first_char_is_space:
                total -= 1

            last_char_was_space = chunk[-1:].isspace()

        return total
    
    def count_chars(self, file):
        """
        Calculates the size of a file in characters.
        Callback function for "wc -m <filename>" command.
        """
        if self.buffer_size == 0:
            try:
                return len(file.read().decode(self.encoding, errors = 'replace'))
            
            except LookupError:
                print(f"Error: Unknown encoding: '{self.encoding}'.")

            except Exception:
                file.seek(0)
                return len(str(file.read()))
            
        total = 0
        
        try:
            # Multi-byte characters that might be split across chunk boundaries.
            # For example, if a 3-byte character is split [byte1, byte2] | [byte3].
            # The decoder will hold the first two bytes until the third one arrives.
            decoder = codecs.getincrementaldecoder(self.encoding)(errors = 'replace')
            total = 0
            for chunk in self._read_chunks(file):
                text = decoder.decode(chunk, final = False)
                total += len(text)
            total += len(decoder.decode(b'', final = True))
            return total
        
        except LookupError:
            print(f"Error: Unknown encoding: '{self.encoding}'.")

        except Exception:
            # Fallback if stream is not seekable
            try:
                file.seek(0)
                return len(file.read())
            except:
                return 0
            
    def count_all(self, file):
        """
        Default Option: Calculates lines, words, bytes, and chars in one pass.
        Optimized for single-pass reading (crucial for pipes/stdin).
        Returns a dict: {'lines': int, 'words': int, 'bytes': int, 'chars': int}
        """
        totals = {'lines': 0, 'words': 0, 'chars': 0, 'bytes': 0}
        # Helper objects for streaming logic
        last_char_was_space = True
        try:
            decoder = codecs.getincrementaldecoder(self.encoding)(errors='replace')

        except LookupError:
            print(f"Error: Unknown encoding '{self.encoding}'")
            sys.exit(1)

        if self.buffer_size == 0:
            content = file.read()
            totals['lines'] = content.count(b'\n')
            totals['bytes'] = len(content)

            # words
            try:
                text_content = content.decode(self.encoding, errors='ignore')
                totals['words'] = len(text_content.split())

            except Exception:
                totals['words'] = len(str(content).split())

            # chars
            try:
                totals['chars'] = len(content.decode(self.encoding, errors = 'replace'))

            except Exception:
                totals['chars'] = len(str(content))
            
            return totals


        for chunk in self._read_chunks(file):
            totals['lines'] += chunk.count(b'\n')
            totals['bytes'] += len(chunk)


            # words
            totals['words'] += len(chunk.split())
            first_char_is_space = chunk[0:1].isspace()

            if not last_char_was_space and not first_char_is_space:
                totals['words'] -= 1

            last_char_was_space = chunk[-1:].isspace()

            # chars
            text = decoder.decode(chunk, final = False)
            totals['chars'] += len(text)
        totals['chars']  += len(decoder.decode(b'', final = True))

        return totals
            
# Infrastructure layer
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

        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            sys.exit(1)

        except PermissionError:
            print(f"Error: Permission denied for reading '{filename}'.")
            sys.exit(1)

        except Exception as e:
            print("Error: An unknown error occurred: {e}")
            sys.exit(1)

        try:
            yield f

        finally:
            f.close()

    else:
        yield sys.stdin.buffer

# Application layer
def produce_count_result(args):
    """Orchestrates the result based on parsed arguments."""

    # Initialize the tool with configuration.
    tool = CCWC(buffer_size = args.buffer_size, encoding = args.encoding)

    request_commands = []
    if args.lines: request_commands.append('lines')
    if args.words: request_commands.append('words')
    if args.chars: request_commands.append('chars')
    if args.bytes: request_commands.append('bytes')

    tool_map = {
        'lines': tool.count_lines,
        'words': tool.count_words,
        'chars': tool.count_chars,
        'bytes': tool.count_bytes
    }

    # Default to lines, words, bytes when no flags specified (like wc)
    if not request_commands:
        request_commands = ['lines', 'words', 'bytes']

    # None is for stdin.
    filenames = args.filenames if args.filenames else [None]
                
    total_counter = {'lines': 0, 'words': 0, 'chars': 0, 'bytes': 0}
    # Dealing with files
    for filename in filenames:
        with get_stream(filename) as f:
            #Use count_all() for multi-command.
            if len(request_commands) > 1:
                try:
                    file_counter = tool.count_all(f)

                    # Update totals
                    for metric in total_counter:
                        total_counter[metric] += file_counter.get(metric, 0)
                        
                    outputs = []
                    for metric in request_commands:
                        outputs.append(str(file_counter[metric]))
                    if filename:
                        print(f" {' '.join(outputs)} {filename}")
                    else:
                         print(f" {' '.join(outputs)}")
                         return # stdin: single input, no totals needed

                except Exception as e:
                    print(f"Error during processing file '{filename}': {e}")
                    continue

            # Single flag → use dedicated function (avoids unnecessary computation).
            elif len(request_commands) == 1:
                try:
                    metric = request_commands[0]
                    func = tool_map[metric]
                    result = func(f)
                    if filename:
                        print(f"  {result} {filename}")
                        total_counter[metric] += result
                    else:
                        print(f"  {result}")
                        return # stdin: single input, no totals needed
                    
                except Exception as e:
                    print(f"Error during processing file '{filename}': {e}")
                    continue
        

    # Print total if multiple files were processed.
    if len(filenames) > 1:
        outputs = []
        for metric in request_commands:
            outputs.append(str(total_counter[metric]))

        print(f" {' '.join(outputs)} total")

# Interface layer
def create_parser():
    """Creates and configures the argument parser."""
    parser = argparse.ArgumentParser(
        description = "ccsc - Build your own wc tool.",
        prog = "ccwc"
    )

    parser.add_argument("-c", "--bytes", action = "store_true", help = "print the byte counts")
    parser.add_argument("-l", "--lines", action = "store_true", help = "print the newline counts")
    parser.add_argument("-w", "--words", action = "store_true", help = "print the word counts")
    parser.add_argument("-m", "--chars", action = "store_true", help = "print the character counts")

    parser.add_argument(
        "--buffer-size",
        type = int,
        default = CCWC.DEFAULT_BUFFER_SIZE,
        help="buffer size in bytes (default: 65536). Set 0 to read entire file at once."
    )

    parser.add_argument(
        "--encoding",
        default = 'utf-8',
        help="encoding (default: utf-8)"
    )

    parser.add_argument(
        "filenames",
        nargs = '*',
        help = "files to process (default: stdin)"
    )

    return parser

# Entry point
def main():
    """
    Main entry point for the ccwc tool.
    Parsed command-line arguments and executes the requested operation.
    """
    parser = create_parser()
    args = parser.parse_args()
    try:
        produce_count_result(args)
    except KeyboardInterrupt:
        sys.exit(130)

if __name__ == "__main__":
    main()