# CORD-19 Exploration 

### CORD-19 Topic Modelling 

This repository contains code and datasets which reprocess the CORD-19 dataset for use in MITRE's TMNT Topic Model

### Usage

`document_parser.py` parsers through the body text of of each paper from the CORD-19 dataset and outputs a jsonlines 
dataset ready for use in TMNT.

`document_merge.py` merges multiple jsonlines files together for use in TMNT. 

### Data

The preprocessed CORD-19 data batched in train and validation sets can be found in the `data/tmnt/train` and `data/tmnt/test`
respectively. Vectorized training, validation and vocabulary files, built using a 2,000 word vocabulary can be found in `data/tmnt/vector_files`.

Details on the experiments and respective model configurations can be found in `data/tmnt/_experiments`

### Results

A visualization of the best performing model's results can be found in `data/tmnt/results`.

## Metadata browser 

To be continued.

## Open relationship Extraction 

To be continued. 
