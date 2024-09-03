import sys

def log(*args, **kwargs):
    """Log to stderr to keep stdout clean"""
    print(*args, file=sys.stderr, **kwargs)