This tool is an offline pipeline to design strain-specific primer sets based on the genome sequences and the annotation data. When users prepare genome and coding sequences for targeted and untargeted strains, users can create primers that detect the targeted strain(s) among compared strains on the genic regions. While there are 16 analytic steps in the pipeline, only one commands can proceed all steps. 

**Quick start to use psspd**

```
git clone https://github.com/manabuishii/psspd.git
conda env create -n psspd -f environment.yaml
conda activate psspd
cp config_sample.yaml config.yaml
./psspd.sh config.yaml
```

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
./psspd.sh config.yaml

You need to customize configuration file named “config.yaml” to define $PATH to tools, input files, output files and so on.

## setup conda

## setup test data

Setup test input data.

```
cp -r /path/to/DL_Data Materials/
```

## License

Copyright 2026 Tsuyoshi TANAKA

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE) for details.

The external tools invoked by this pipeline (NCBI BLAST+, GMAP, Primer3) are not
distributed as part of this software and are governed by their own licenses.
