# ccwc - Build Your Own wc Tool

A Python implementation of the Unix `wc` (word count) command-line tool.

This project is part of the [Coding Challenges](https://codingchallenges.fyi/challenges/challenge-wc) series.

## Features

- Count bytes (`-c`)
- Count lines (`-l`)
- Count words (`-w`)
- Count characters (`-m`)
- Read from files or stdin
- Process multiple files with totals
- Configurable buffer size and encoding
- Efficient streaming for large files

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Count lines, words, and bytes (default)
ccwc test.txt

# Count lines only
ccwc -l test.txt

# Count words only
ccwc -w test.txt

# Count bytes only
ccwc -c test.txt

# Count characters only
ccwc -m test.txt

# Combine multiple options
ccwc -l -w test.txt

# Process multiple files
ccwc file1.txt file2.txt file3.txt

# Read from stdin
cat test.txt | ccwc -l

# Custom encoding
ccwc --encoding utf-16 test.txt

# Custom buffer size (in bytes)
ccwc --buffer-size 8192 test.txt
```

## Examples

```bash
$ ccwc test.txt
  7145  58164 342190 test.txt

$ ccwc -l test.txt
  7145 test.txt

$ cat test.txt | ccwc -w
  58164
```

## Requirements

- Python >= 3.7
