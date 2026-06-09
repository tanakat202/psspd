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

# GMAP database directory (gmap_build/gmap -D option), relative to the GMAP
# working directory.
GMAP_DB_DIR = "GMAP"

# GMAP query: the no-hit CDS FASTA produced by the BLASTP no-hit extraction
# step, relative to the GMAP working directory.
GMAP_QUERY = "../BLASTP/Nohit_cds.fa"

# make_complete_list (runs in the GMAP working directory): the no-hit CDS input
# and the resulting Target list / CDS outputs.
MAKE_COMPLETE_LIST_INPUT_CDS = "../BLASTP/Nohit_cds.fa"
MAKE_COMPLETE_LIST_OUTPUT_LIST = "../GMAP/Target.list"
MAKE_COMPLETE_LIST_OUTPUT_CDS = "../GMAP/Target_cds.fa"

# make_primer3_input (runs in the Primer3 working directory): the input CDS and
# the primer3_core input list it produces. (The primer-size knobs in that
# section stay configurable.)
MAKE_PRIMER3_INPUT_INPUT_CDS = "../GMAP/Target_cds.fa"
MAKE_PRIMER3_INPUT_OUTPUT_FILE = "../Primer3/primer3_input.list"

# primer3_core (runs in the Primer3 working directory): input / output list files.
PRIMER3_INPUT_FILE = "primer3_input.list"
PRIMER3_OUTPUT_FILE = "primer3_output.list"

# createFasta (runs in the Primer3 working directory): primer3_core output list
# -> primer FASTA.
CREATE_FASTA_INPUT_FILE = "primer3_output.list"
CREATE_FASTA_OUTPUT_FILE = "primer3.fa"
