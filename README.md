This tool is a pipeline to design strain-specific primer sets based on the genome sequences and the annotation data. When users prepare genome sequences and the annotation data, users can create primers that detect the certain strain(s) among compared strains on the genic regions. This pipeline creates primers on the genic regions that exist only in the targeted strain(s) but not in the other strains. 

**Steps of primer construction**
1.	Homology search (BLASTP) is performed among strains users prepared. Then, genes in the targeted strains that have no homologs in the other strains were selected.
2.	Homologous regions of the selected genes are searched in the genome sequences of the other strains to confirm the specificity of the genes (GMAP).
3.	On the genes, primers were constructed (Primer3).
4.	The specificity of the primers and the amplified sequences were elucidated on all genome sequences (BLASTN) by the length of the amplified sequences.

**Prerequisites**
1.	NCBI-BLAST: blastp: 2.11.0+
2.	GMAP: version 2017-03-17
3.	Primer3: libprimer3 release 2.6.1
4.	Python Library

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install pyyaml
```


**How to use the pipeline**
./psspd.sh config.yaml

You need to customize configuration file named “config.yaml” to define $PATH to tools, input files, output files and so on.

## setup conda

## setup test data

setup test input data and Codon.txt

```
cp -r /path/to/DL_Data Materials/
cp /path/to/Codon.txt Materials/
```

copy sample config

```
cp config_sample.yaml config.yaml
```

## create conda env

```
conda env create -n primer-design-tool -f environment.yaml
```

## execute with conda

```
conda activate primer-design-tool
```


```
./psspd.sh config.yaml
```
