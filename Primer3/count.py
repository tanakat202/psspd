#!/usr/bin/python3

import sys
import re

count=0
SUDE={}
GENE=0
with open(f"unique_primer3.tab") as IN:
    for l in IN:
        l = l.strip()
        dat = l.split("\t")
        m = re.match(r"(\S+)_(\d+)$", dat[0])
        if m:
            # m.group(1) is the first capture group, m.group(2) is the second
            seq_id = m.group(1)
            count += 1
            if not seq_id in SUDE:
                GENE += 1
                SUDE[seq_id] = 1


print(f"COUNT: {count}")
print(f"GENE: {GENE}")
sys.exit()
