"""Fixed default values that were previously set via config.yaml.

These values are centralized here so that, if they ever need to change,
there is a single place to edit. They are intentionally not configurable
from the config file anymore.
"""

# BLASTP all-vs-all concatenated FASTA file. The same file is used as the
# makeblastdb input, the BLASTP database, and the BLASTP query.
# Resolved relative to the BLASTP working directory (BASE_DIR/BLASTP),
# which is the CWD when the BLASTP scripts run.
BLASTP_ALL_AA_FASTA = "all_aa.fasta"

# makeblastdb database type for the BLASTP database (protein).
BLASTP_DBTYPE = "prot"

# BLASTP tabular output file. Written in the BLASTP working directory and read
# back by the downstream no-hit extraction step.
BLASTP_OUTPUT = "blastp.out"
