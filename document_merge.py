'''
Author: Kristen Sheets

This module creates a merges .jsonl files created with document_parser.py

'''

import jsonlines
from tqdm import tqdm

files = ['biorxiv_medrxiv.jsonl', 'comm_use_subset.jsonl', 'noncomm_use_subset.jsonl']
directory = './data/tmnt/'

if __name__ == '__main__':

    with jsonlines.open(directory + 'covid.jsonl', 'a') as writer:
        for file in files:
            with jsonlines.open(directory + file) as reader:
                for line in tqdm(reader, desc=file):
                    writer.write(line)
