#!/usr/bin/env python3
import sys

def main():
    try:
        html_content = sys.stdin.read()
    except Exception as e:
        print(f"findlinks: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        soup = sys.stdin.read()
    except Exception as e:
        print(f"findlinks: {e}", file=sys.stderr)
        sys.exit(1)
    
    links = main(soup)
    for link in links:
        print(link)

if __name__ == "__main__":
    main()