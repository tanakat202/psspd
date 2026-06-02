"""Shared helpers for deriving per-species settings from the ``species`` list.

The pipeline used to enumerate every species (SpeciesA, SpeciesB, ...) in each
config section. Instead, ``config.yaml`` now carries a single ``species`` list
and an optional ``reference_count`` (default 1). Prefixes are assigned
automatically from the list order (AA, AB, ..., AZ, BA, ...), and every step
derives its per-species settings from this single source of truth.

Roles:
  * reference: the first ``reference_count`` species (default 1)
  * other:     the remaining species
  * all:       every species
"""

_ALPHABET_SIZE = 26
_MAX_SPECIES = _ALPHABET_SIZE * _ALPHABET_SIZE  # 676 (AA..ZZ)


def index_to_prefix(index):
    """Map a 0-based list position to a two-letter prefix (0->AA, 26->BA)."""
    if not isinstance(index, int) or index < 0 or index >= _MAX_SPECIES:
        raise ValueError(
            f"species index {index!r} out of range (0..{_MAX_SPECIES - 1}); "
            f"at most {_MAX_SPECIES} species are supported"
        )
    first = index // _ALPHABET_SIZE
    second = index % _ALPHABET_SIZE
    return chr(ord("A") + first) + chr(ord("A") + second)


def load_species(config):
    """Build the resolved species list from ``config``.

    Returns a list of dicts with keys: index, prefix, cds, genome, is_reference.
    Raises ValueError on malformed input.
    """
    species = config.get("species")
    if not species:
        raise ValueError("config must contain a non-empty 'species' list")
    if not isinstance(species, list):
        raise ValueError("'species' must be a list")

    reference_count = config.get("reference_count", 1)
    if not isinstance(reference_count, int) or not (1 <= reference_count <= len(species)):
        raise ValueError(
            f"'reference_count' must be an int in 1..{len(species)} "
            f"(got {reference_count!r})"
        )

    resolved = []
    for index, entry in enumerate(species):
        if not isinstance(entry, dict):
            raise ValueError(
                f"species[{index}] must be a mapping with 'cds' and 'genome' "
                f"(got {entry!r})"
            )
        cds = entry.get("cds")
        genome = entry.get("genome")
        if not cds:
            raise ValueError(f"species[{index}] is missing required key 'cds'")
        if not genome:
            raise ValueError(f"species[{index}] is missing required key 'genome'")
        resolved.append(
            {
                "index": index,
                "prefix": index_to_prefix(index),
                "cds": cds,
                "genome": genome,
                "is_reference": index < reference_count,
            }
        )
    return resolved


def all_species(config):
    """All species, in list order."""
    return load_species(config)


def reference_species(config):
    """The first ``reference_count`` species (the reference set)."""
    return [s for s in load_species(config) if s["is_reference"]]


def other_species(config):
    """The non-reference species."""
    return [s for s in load_species(config) if not s["is_reference"]]


# --------------------------------------------------------------------------
# Pipeline-specific derivation helpers.
#
# These replace the per-species enumerations that used to be written out by
# hand in every config section. Paths follow the same conventions as before
# (relative to each stage's working directory), with the species prefix and
# the per-entry genome filename substituted in.
# --------------------------------------------------------------------------

def reference_prefixes(config):
    """Prefixes of the reference species, in order."""
    return [s["prefix"] for s in reference_species(config)]


def blastp_input_files(config):
    """Amino-acid FASTA files for all species (build_blastp_db.input_files)."""
    return [f"../Materials/{s['prefix']}/{s['prefix']}.aa.fasta" for s in all_species(config)]


def gmap_build_databases(config):
    """GMAP databases to build, for the non-reference species (name + genome)."""
    return [
        {"name": s["prefix"], "genome": f"../Materials/DL_data/{s['genome']}"}
        for s in other_species(config)
    ]


def gmap_databases(config):
    """GMAP searches for the non-reference species (name + gff3 output)."""
    return [
        {"name": s["prefix"], "output": f"{s['prefix']}.gff3"}
        for s in other_species(config)
    ]


def hit_list_targets(config):
    """Prefixes for make_hit_list, for the non-reference species."""
    return [s["prefix"] for s in other_species(config)]


def complete_list_hit_files(config):
    """Hit-list files for make_complete_list, for the non-reference species."""
    return [f"../GMAP/{s['prefix']}_hit.tab" for s in other_species(config)]


def blastn_db_databases(config):
    """BLASTN databases to build, for all species (name + genome input + output)."""
    return [
        {
            "name": s["prefix"],
            "input": f"../Materials/DL_data/{s['genome']}",
            "output": f"{s['prefix']}.fna",
        }
        for s in all_species(config)
    ]


def blastn_short_databases(config):
    """BLASTN searches for all species (name + db + output)."""
    return [
        {"name": s["prefix"], "db": f"{s['prefix']}.fna", "output": f"{s['prefix']}.out"}
        for s in all_species(config)
    ]


def extract_hit_regions_targets(config):
    """Prefixes for extract_hit_regions, for all species."""
    return [s["prefix"] for s in all_species(config)]


def primer_pair_files(config):
    """Pair-candidate files for make_primer_list, for the non-reference species."""
    return [f"{s['prefix']}_possiblePair.tab" for s in other_species(config)]


def reference_pair_files(config):
    """Pair-candidate files for the reference species (read by make_primerList3)."""
    return [f"{s['prefix']}_possiblePair.tab" for s in reference_species(config)]
