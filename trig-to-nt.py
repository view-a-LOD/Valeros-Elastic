import argparse
import sys
from pathlib import Path

from rdflib import ConjunctiveGraph


def convert_trig_to_nt(input_path: Path, output_path: Path) -> None:
    g = ConjunctiveGraph()
    g.parse(input_path.as_posix(), format="trig")
    data = g.serialize(format="nt")
    if isinstance(data, bytes):
        data = data.decode("utf-8")

    output_path.write_text(data, encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a TriG (.trig) RDF file to N-Triples (.nt) using rdflib.",
    )
    parser.add_argument("input", help="Path to input .trig file")
    parser.add_argument("output", help="Path to output .nt file")

    args = parser.parse_args(argv)

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.is_file():
        parser.error(f"Input file does not exist: {in_path}")

    try:
        convert_trig_to_nt(in_path, out_path)
    except Exception as e:
        print(f"Error converting {in_path} to N-Triples: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
