#!/usr/bin/python3
from pprint import pprint
import sys
import os
import re
import yaml

# Fixed directory for species input files (relative to Materials/)
INPUT_DIR = "DL_data"


def resolve_input_file(filename):
    """Resolve species input filename under INPUT_DIR, rejecting path traversal.

    Only a plain filename (no directory components, not absolute) is accepted.
    """
    if not isinstance(filename, str) or not filename:
        raise ValueError(f"input_file must be a non-empty string: {filename!r}")
    if filename in ('.', '..'):
        raise ValueError(f"input_file must be a filename, not '{filename}'")
    if os.path.isabs(filename) or '/' in filename or '\\' in filename \
            or filename != os.path.basename(filename):
        raise ValueError(
            f"input_file '{filename}' must be a plain filename "
            f"(no path components). Place files under '{INPUT_DIR}/'."
        )
    return os.path.join(INPUT_DIR, filename)


def translation(seq, bef, output_aa, output_codons, codon_dict):
    """Translate codon sequences to amino acid sequences"""
    seq = seq.replace("a", "A").replace("t", "T").replace("g", "G").replace("c", "C")
    output_codons.write(seq + "\n")
    data = list(seq)
    num = int((len(data)+1)/3+1)
    for i in range(1, num):
        j = i * 3 - 3
        codon = seq[j:j+3]
        if codon in codon_dict and re.search(r"\w", codon_dict[codon]):
            output_aa.write(codon_dict[codon])
        elif re.match(r"^\w$", codon) or re.match(r"^\w\w$", codon):
            print(f"{bef}\tLAST\t{codon}")
        else:
            output_aa.write("X")
    output_aa.write("\n")


def process_species(input_file, prefix, codon_dict):
    """Process translation for one species"""
    print(f"Processing: {prefix} ({input_file})")

    # directory prefix
    if not os.path.exists(prefix):
        os.makedirs(prefix)

    # Open output files for writing
    out_aa_path = f"{prefix}/{prefix}.aa.fasta"
    out_codons_path = f"{prefix}/{prefix}.cds.fasta"
    out_list_path = f"{prefix}/{prefix}.list"

    with open(out_aa_path, "w") as output_aa, \
         open(out_codons_path, "w") as output_codons, \
         open(out_list_path, "w") as open_list:

        A = 0
        acc = ""
        bef = ""
        seq = ""

        with open(input_file, "r") as in_file:
            for lineno, line in enumerate(in_file, start=1):
                line = line.strip()
                if line.startswith(">"):
                    # Extract ID: from the character after '>' up to the first
                    # whitespace, or to end of line if no whitespace is present.
                    header_tokens = line[1:].split(maxsplit=1)
                    acc = header_tokens[0] if header_tokens else ""
                    if not acc:
                        raise ValueError(
                            f"Malformed FASTA header at {input_file}:{lineno}: "
                            f"'{line}' has no ID (expected '>id ...' format)"
                        )
                    if bef and re.search(r"\w", bef):
                        translation(seq, bef, output_aa, output_codons, codon_dict)

                    A = A + 1
                    open_list.write(f"gene{A}\t{acc}\n")
                    output_aa.write(f">{prefix}_gene{A}\n")
                    output_codons.write(f">{prefix}_gene{A}\n")
                    bef = acc
                    seq = ""
                else:
                    seq = seq + line

            if seq:
                translation(seq, bef, output_aa, output_codons, codon_dict)

    print(f"  -> {out_aa_path}, {out_codons_path}, {out_list_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 step0_translation.py <CONFIG_FILE>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        codon_file = config['codon_file']

        # Process multiple species if species list exists, otherwise use legacy format
        if 'species' in config:
            species_list = config['species']
        elif 'input_file' in config and 'prefix' in config:
            # Backward compatibility: legacy format
            species_list = [{
                'input_file': config['input_file'],
                'prefix': config['prefix']
            }]
        else:
            print("Error: 'species' list or 'input_file'/'prefix' required in config.")
            sys.exit(1)

    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found.")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Required key {e} not found in config file.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML format in config file: {e}")
        sys.exit(1)

    # Load codon table
    codon_dict = {}
    try:
        with open(codon_file, "r") as f:
            for line in f:
                line = line.strip()
                match = re.match(r"(\w\w\w)\t(\S)", line)
                if match:
                    codon = match.group(1)
                    aa = match.group(2)
                    codon_dict[codon] = aa
    except FileNotFoundError:
        print(f"Error: Codon file '{codon_file}' not found.")
        sys.exit(1)

    # Process each species
    input_dir_abs = os.path.abspath(INPUT_DIR)
    for species in species_list:
        try:
            input_file = resolve_input_file(species['input_file'])
            prefix = species['prefix']
            process_species(input_file, prefix, codon_dict)
        except KeyError as e:
            print(f"Error: Missing {e} in species entry: {species}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError:
            print(
                f"Error: Input file '{input_file}' not found.\n"
                f"  Place species input files in: {input_dir_abs}/\n"
                f"  (config 'input_file' must be a plain filename, "
                f"resolved relative to '{INPUT_DIR}/')",
                file=sys.stderr,
            )
            sys.exit(1)
        except Exception as e:
            print(f"Error processing {prefix}: {str(e)}", file=sys.stderr)
            sys.exit(1)

    print(f"Completed: {len(species_list)} species processed.")


if __name__ == "__main__":
    main()
