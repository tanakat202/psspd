import sys
import re

hit_dict = {}
with open(f"possiblePair.list") as IN:
    for l in IN:
        l = l.strip()
        if not l:
            continue
        with open(l) as IN2:
            for line in IN2:
                line = line.strip()
                if not line:
                    continue
                dat = line.split("\t")
                seq_id = dat[0]
                hit_dict[seq_id] = 1

SUDE={}
output={}
with open(f"SpeciesA_possiblePair.tab") as IN:
    for l in IN:
        # chomp
        l = l.strip()
        if not l:
            continue
        # @dat = split("\t",$_);
        dat = l.split("\t")
        # $id = $dat[0];
        seq_id = dat[0]
        #print(seq_id)
        if seq_id in SUDE:
            SUDE[seq_id] = SUDE[seq_id] + 1
        else:
            SUDE[seq_id] = 1

        output[seq_id] = l

#sys.exit(0)  # Exit immediately, no further processing

INN = open(f"primer3.fa")
OUT = open(f"unique_primer3.tab", "w")

OUTPUT2 = {}
a = 0
for line in INN:
    # chomp
    line = line.strip()
    if not line:
        continue
    #print(line)
    m = re.search(r">(\S+)::PRIMER_(\w+)_(\d+)", line)
    #print(m)
    if m:
        seq_id = f"{m.group(1)}_{m.group(3)}"
        seq = m.group(2)
        ID = m.group(1)
        if seq_id in OUTPUT2:
            a=0
        if seq_id in SUDE and SUDE[seq_id]==1:
            a=1
            OUTPUT2[seq_id] = seq_id
        else:
            a=0
    elif a == 1:
        if "LEFT" in seq:
            OUT.write(f"{output[seq_id]}\t{line}")
        else:
            OUT.write(f"\t{line}\n")


sys.exit()

