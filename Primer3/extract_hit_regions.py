import sys
import re

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_hit_regions.py <input_file_prefix>")
        return
    
    input_file = sys.argv[1]+".out"
    output_file = sys.argv[1]+".out.tab"
    # output_file must be empty
    with open(output_file, "w") as out_file:
                        
        try:
            with open(input_file, "r") as in_file:
                lines = in_file.read().splitlines()

            for line in lines:
                if not line.strip():
                    continue
                
                parts = line.split("\t")
                if len(parts) >= 1:
                    match = re.search(r'(\S+)::(PRIMER_\S+)::', parts[0])
                    if match:
                        sequence_id = match.group(1)
                        primer_type = match.group(2)
                        if len(parts) >= 3:
                            out_file.write(f"{sequence_id}\t{primer_type}\t{parts[1]}\t{parts[8]}\t{parts[9]}\n")

        except Exception as e:
            print(f"Error processing input: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    main()
