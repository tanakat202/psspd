This tool is an offline pipeline to design strain-specific primer sets based on the genome sequences and the annotation data. When users prepare genome and coding sequences for targeted and untargeted strains, users can create primers that detect the targeted strain(s) among compared strains on the genic regions. While there are 16 analytic steps in the pipeline, only one command can proceed all steps.

**Quick start to use psspd**

psspd is available from [Bioconda](https://bioconda.github.io/recipes/psspd/README.html).
The `conda-forge` channel is required as well.

```sh
conda create -n psspd -c conda-forge -c bioconda psspd
conda activate psspd
mkdir -p ~/analysis/Materials/DL_data && cd ~/analysis
cp -r /path/to/DL_Data/* Materials/DL_data/
cp "$CONDA_PREFIX/share/psspd/config_sample.yaml" config.yaml
psspd config.yaml
```

If `cp` cannot find the bundled `config_sample.yaml`, you can download it
instead. Replace `1.1.1` with the installed version shown by
`conda list psspd`:

```sh
curl -fsSL \
  https://raw.githubusercontent.com/tanakat202/psspd/1.1.1/config_sample.yaml \
  -o config.yaml
```

To run psspd from a source checkout instead, see the
[developer guide](docs/DEVELOPMENT.md).

**Steps of primer construction**
1.	Homology search (BLASTP) is performed among strains users prepared. Then, genes in the targeted strains that have no homologs in the other strains were selected.
2.	Homologous regions of the selected genes are searched in the genome sequences of the other strains to confirm the specificity of the genes (GMAP).
3.	On the genes, primers were constructed (Primer3).
4.	The specificity of the primers and the amplified sequences were elucidated on all genome sequences (BLASTN) by the length of the amplified sequences.

**Prerequisites**
1.	NCBI-BLAST: 2.16.0
2.	GMAP: version 2025.07.31
3.	Primer3: libprimer3 release 2.6.1
4.	Python: 3.12.3
5.	Python Library: PyYAML 6.0.3


**How to use the pipeline**
psspd config.yaml

You need to customize the configuration file `config.yaml` to define input
files, output files and so on. External tools are looked up on `PATH`; the
Bioconda package installs them into the same environment. To use a specific
executable, set its path in the `executables:` section of `config.yaml`.

## Input data

Run psspd in a work directory of your choice (`~/analysis` in the Quick start)
and place the input FASTA files under `Materials/DL_data/` there:

```sh
mkdir -p Materials/DL_data
cp -r /path/to/DL_Data/* Materials/DL_data/
```

The file names must match the `cds:` and `genome:` entries of the species list
in `config.yaml`.

## Work directory

`psspd` runs the pipeline in the directory it is invoked from (the *work
directory*). The stage directories `Materials/`, `BLASTP/`, `GMAP/` and
`Primer3/`, which hold the inputs, intermediate files and results, are created
under the work directory, while the bundled Python scripts and data files are
always looked up under the directory `psspd` is installed in
(`$CONDA_PREFIX/share/psspd/` for the Bioconda package). Nothing is written
into the installation directory, so you can use any number of work directories
with one installation:

```sh
mkdir -p ~/analysis2/Materials/DL_data && cd ~/analysis2
cp -r /path/to/other/DL_Data/* Materials/DL_data/
cp "$CONDA_PREFIX/share/psspd/config_sample.yaml" config.yaml
psspd config.yaml
```

External tools (`blastn`, `blastp`, `makeblastdb`, `gmap`, `gmap_build`,
`primer3_core`) are looked up on `PATH`; the Bioconda package installs them
into the same environment. A path can be given explicitly per tool in the
`executables:` section of the config file.

## License

Copyright 2026 Tsuyoshi TANAKA

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE) for details.

The external tools invoked by this pipeline (NCBI BLAST+, GMAP, Primer3) are not
distributed as part of this software and are governed by their own licenses.
