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


def convert_folder(input_folder: Path) -> None:
    for trig_file in input_folder.glob("*.trig"):
        out_file = trig_file.with_suffix(".nt")
        try:
            convert_trig_to_nt(trig_file, out_file)
            print(f"Converted {trig_file} to {out_file}")
        except Exception as e:
            print(
                f"Error converting {trig_file} to N-Triples: {e}", file=sys.stderr)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a TriG (.trig) RDF file to N-Triples (.nt) using rdflib.",
    )
    parser.add_argument(
        "input", help="Path to input .trig file or folder containing .trig files")
    parser.add_argument(
        "--output", help="Path to output .nt file (required if input is a single file)")

    args = parser.parse_args(argv)

    in_path = Path(args.input)

    if in_path.is_dir():
        convert_folder(in_path)
    elif in_path.is_file() and in_path.suffix == ".trig":
        if args.output is None:
            parser.error(
                "Output path is required when converting a single file.")
        out_path = Path(args.output)
        try:
            convert_trig_to_nt(in_path, out_path)
            print(f"Converted {in_path} to {out_path}")
        except Exception as e:
            print(
                f"Error converting {in_path} to N-Triples: {e}", file=sys.stderr)
            return 1
    else:
        parser.error(f"Invalid input: {in_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
