"""
Unified converter CLI prototype for bank2budget

Usage examples:
  python bin/unify-convert.py file1.csv file2.csv
  python bin/unify-convert.py --preview .scratch/bob-sample-raw.csv

Behavior:
- Detects source by header heuristics and dispatches to the appropriate converter module
- Supports bob-to-actual.py, wise-to-actual.py and revolut-to-actual.py (imports them)
- --preview prints which converter would run and output locations without writing files
"""
import sys
import os
import argparse
import importlib.util

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))

# Helper to import a script as module

def load_script_module(path):
    spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(path))[0], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Basic detection heuristics

def detect_source(path):
    """Return one of: 'bob', 'wise', 'revolut', or None"""
    try:
        with open(path, encoding='utf-8-sig', newline='') as f:
            head = f.read(4096).lower()
    except Exception:
        return None

    if 'transaction date' in head and 'reference no' in head:
        return 'bob'
    if 'source currency' in head and 'target currency' in head:
        return 'wise'
    if 'started date' in head and 'description' in head:
        return 'revolut'
    return None

# Dispatch map: source -> (module_path, run_callable_name)

def make_dispatch():
    base = REPO_ROOT
    return {
        'bob': (os.path.join(base, 'bob-to-actual.py'), 'process_csv'),
        'wise': (os.path.join(base, 'wise-to-actual.py'), 'convert_csv'),
        'revolut': (os.path.join(base, 'revolut-to-actual.py'), 'convert_xlsx_to_csv'),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description='Unified converter CLI prototype')
    parser.add_argument('files', nargs='*', help='Input CSV/XLSX files to convert')
    parser.add_argument('--preview', action='store_true', help='Do not write outputs; print actions')
    args = parser.parse_args(argv)

    dispatch = make_dispatch()

    if not args.files:
        print('No input files provided; nothing to do.')
        return 1

    for f in args.files:
        if not os.path.exists(f):
            print(f'File not found: {f} -- skipping')
            continue

        src = detect_source(f)
        if not src:
            print(f'Could not detect source for {f} -- skipping')
            continue

        if src not in dispatch:
            print(f'No converter registered for source {src} -- skipping')
            continue

        module_path, callable_name = dispatch[src]

        print(f'File: {f} detected as {src}. Using {os.path.basename(module_path)}')

        if args.preview:
            continue

        # Load module and invoke
        mod = load_script_module(module_path)

        # Call different functions depending on the converter interface
        if src == 'bob':
            # bob.process_csv expects filename (path) or uses cwd; call with the full path
            try:
                mod.process_csv(f)
            except Exception as e:
                print(f'Error running bob converter on {f}: {e}')
        elif src == 'wise':
            # wise.convert_csv reads from global INPUT_FILENAME; set it then call
            try:
                mod.INPUT_FILENAME = f
                # Allow the module to auto-detect base currency if implemented
                mod.convert_csv()
            except Exception as e:
                print(f'Error running wise converter on {f}: {e}')
        elif src == 'revolut':
            # revolut.convert_xlsx_to_csv accepts input_file arg
            try:
                mod.convert_xlsx_to_csv(input_file=f)
            except Exception as e:
                print(f'Error running revolut converter on {f}: {e}')

    return 0

if __name__ == '__main__':
    sys.exit(main())
