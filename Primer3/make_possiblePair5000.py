import sys
import re

if len(sys.argv) != 2:
    print("Usage: python make_possiblePair5000.py <input_file>")
    sys.exit(1)
input_file = sys.argv[1]+".out.tab"
output_file = sys.argv[1]+"_possiblePair2000.tab"


def split_data(line):
    return [d.strip() for d in line.split('\t') if d]

def chomp_line(line):
    parts = split_data(line.rstrip('\n'))
    return '\t'.join(parts)

def match_pattern(pattern, line_list, default):
    if not line_list:
        return default
    first_part = split_data(line_list[0])
    pattern_str = '\t'.join(first_part) + '\n'
    for line in line_list[1:]:
        line_str = split_data(line)[0]
        if re.match(pattern_str, line_str):
            return line_str
    return default

def process_line(line):
    """chomp line and split it into parts, then process it to find pairs.

    Args:
        line (_type_): _description_

    Returns:
        _type_: _description_
    """
    chomped_line = chomp_line(line)
    data = split_data(chomped_line)
    return data
    result = []
    if len(data) < 3:
        return '\t'.join([data[0], data[1] or '', data[2] or ''] for _ in range(len(data)))
    last_pos = (data[2], data[3], data[4])
    left, right = '', ''

# read file contents
try:
    with open(input_file, 'r') as f:
        lines = f.readlines()
except FileNotFoundError:
    print("File not found. Please check the input file path.")
    sys.exit()
print(f"Processing file: {input_file}")
print(f"Output will be saved to: {output_file}")
print(len(lines))  # Debugging line to check number of lines read
# open output file
out_file = open(output_file, 'w')


# 
processed_lines = []
for line in lines:
    processed_line = process_line(line.rstrip('\n'))
    processed_lines.append(processed_line)

def pair():
    global count
    # print(f"bef={bef}, left={left}, right={right}")
    # print(f"left[0]={left[0]}, right[0]={right[0]}")
    if (left[0] and re.match(r'\w', left[0])) and (right[0] and re.match(r'\w', right[0])):
        for l in left:
            for r in right:
                l_match = re.match(r'(\S+)_(\d+)_(\d+)', l)
                if l_match:
                    lseq = l_match.groups()[0]
                    ls = int(l_match.groups()[1])
                    le = int(l_match.groups()[2])
                    if ls < le:
                        ldir = 'p'
                    else:
                        ldir = 'm'
                r_match = re.match(r'(\S+)_(\d+)_(\d+)', r)
                if r_match:

                    rseq = r_match.groups()[0]
                    rs = int(r_match.groups()[1])
                    rre = int(r_match.groups()[2])
                    if rs < rre:
                        rdir = 'p'
                    else:
                        rdir = 'm'
                if rseq in lseq:
                    if not rdir in ldir:
                        if ldir == 'p':
                            dist = rre - ls + 1
                            if dist < 5000 and -5000 < dist:
                                out_file.write(f"{bef}\t{lseq}\t{ls}\t{le}\t{ldir}\t{rs}\t{rre}\t{rdir}\t{dist}\n")
                        else:
                            dist = le - rs + 1
                            if dist < 5000 and -5000 < dist:
                                out_file.write(f"{bef}\t{lseq}\t{ls}\t{le}\t{ldir}\t{rs}\t{rre}\t{rdir}\t{dist}\n")


def make_pair(left_seq, right_seq):
    ldir = 'p' if '-' in left_seq else 'm'
    rdir = 'p' if '-' in right_seq else 'm'
    
    if ldir != rdir and (ldir == 'p'):
        dist = abs(int(left_seq[3]) - int(right_seq[3]))
        return f"Pair:{left_seq[1]}_{left_seq[2]}_{right_seq[1]}_{right_seq[2]}, Distance={dist}"
    else:
        return "No Pair"

pairs = []
bef=None
left = []
right = []
# $_ is parts joind by tab
for parts in processed_lines:
    line = '\t'.join(parts) 
    if re.match(r'PRIMER_(\w+)_(\d+)', parts[1]):
        match = re.match(r'PRIMER_(\w+)_(\d+)', parts[1])
        id = f"{parts[0]}_{match.group(2)}"
    pos = f"{parts[2]}_{parts[3]}_{parts[4]}"
    # print(f"{id}\t{pos}")
    if bef and (id in bef):
        if 'LEFT' in line:
            # print(f"1 then {bef}\t{id} {pos}")
            left.append(pos)
        else:
            # print(f"1 else {bef}\t{id} {pos}")
            right.append(pos)
        
    elif bef and re.match(r'\w', bef):
        pair()
        left = []
        right = []
        if 'LEFT' in line:
            # print(f"2 then {bef}\t{id} {pos}")
            left.append(pos)
        else:
            # print(f"2 else {bef}\t{id} {pos}")
            right.append(pos)
    else:
        if 'LEFT' in line:
            # print(f"3 then {bef}\t{id} {pos}")
            left.append(pos)
        else:
            # print(f"3 else {bef}\t{id} {pos}")
            right.append(pos)
    bef = id
pair()
# result = make_pair(line_left, line_right)

# print(result)


