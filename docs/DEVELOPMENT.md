# Developer guide

This guide is for people who want to run psspd from a source checkout, for
example to modify the pipeline or to test unreleased changes. If you only want
to use psspd, install it from Bioconda as described in the
[README](../README.md).

## Prerequisites

You need [conda](https://docs.conda.io/) (Miniforge or Miniconda) and git.
The pinned tool versions used for development are listed in
[`environment.yaml`](../environment.yaml) and in the *Prerequisites* section
of the [README](../README.md).

## Set up from source

```sh
git clone https://github.com/tanakat202/psspd.git
cd psspd
conda env create -n psspd -f environment.yaml
conda activate psspd
```

## Run from the clone

```sh
cp config_sample.yaml config.yaml
./psspd config.yaml
```

Edit `config.yaml` before running to list your species and input files. Input
FASTA files go under `Materials/DL_data/`:

```sh
cp -r /path/to/DL_Data/* Materials/DL_data/
```

To check that all bundled scripts and external tools are found without running
the pipeline:

```sh
./psspd config.yaml --check-only
```

## Run the clone from another directory

`psspd` uses the directory it is invoked from as the work directory (see
*Work directory* in the [README](../README.md)), so the clone can also be run
against a separate analysis directory:

```sh
mkdir -p ~/analysis/Materials/DL_data && cd ~/analysis
cp -r /path/to/DL_Data/* Materials/DL_data/
cp /path/to/psspd/config_sample.yaml config.yaml
/path/to/psspd/psspd config.yaml
```

Running `./psspd config.yaml` from inside the clone behaves the same way: there
the work directory and the installation directory are the same.
