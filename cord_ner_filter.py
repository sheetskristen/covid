'''
Author: Julian Fernandez

This module produces jsonl output that is deemed by our NER system to contain protein entities.

The jsonl output of this module contains a dictionary on each line such that:
> line.keys()
dict_keys(
  ['doc_id', 'sent', 'source', 'doi', 'pmcid', 'pubmed_id', 'publish_time', 'authors', 'journal']
)

'''


import jsonlines
import argparse
import spacy
import copy
import re

from tqdm import tqdm


# Load SciSpacy's JNLPBA NER model.
# It tags entities with the ontology [DNA, CELL_TYPE, CELL_LINE, RNA, PROTEIN].
nlp = spacy.load('en_ner_jnlpba_md')

# Command line arguments.
parser = argparse.ArgumentParser(description='Filter relevant documents with'
                                             ' SciSpacy\'s en_ner_jnlpba_md NER model.')

parser.add_argument('--doc_files', type=str, nargs='+',
                    default=['data/CORD-NER-corpus.json'],
                    help='List of filepaths to jsonl files which contain documents to be filtered.')
parser.add_argument('--out_file', type=str, default='data/CORD-NER-PROTEIN-corpus.jsonl',
                    help='jsonl output file to which CORD-NER protein entity-containing documents'
                         'will be written.')

args = parser.parse_args()


def sent_to_ent_types(doc):
    """
    Return a set of the entity types contained in a Spacy document object.
    :param doc: A Spacy Document object
    :return: a set of the entity types contained in the sentence.
    """
    return set(map(lambda e: e.label_, doc.ents))


def preprocess_sent(sent):
    """
    Preprocess a string so that it's ready for next steps in the pipeline.
    :param sent: a Spacy span that may contain undesired punctuation, numbers, etc.
    :return: cleaner_sent: a cleaner version of the input
    """
    sent = str(sent)

    # Make parentheticals into synonym-clauses.
    sent = re.sub('\(', ', or', sent)
    sent = re.sub('\)', ',', sent)

    tokens = sent.split()

    forbidden_tokens = set(
        '()[].,;!?`-'
    )

    cleaner_tokens = [
        token
        for token in tokens
        if (not token.isnumeric()) or len(token) == 4
        if token not in forbidden_tokens
    ]

    cleaner_sent = ' '.join(cleaner_tokens)

    return cleaner_sent


def get_text_from_sents(sents):
    all_tokens = map(lambda s: s['sent_tokens'], sents)
    all_sents = map(lambda tokens: ' '.join(tokens), all_tokens)
    text = ' '.join(all_sents)

    return text


def filter_file(doc_file):
    """
    Get a list of dictionaries which contain the relevant sentences along with metadata.
    :param doc_file: jsonl filepath which contains documents for tagging.
    :return: List of dictionaries which contain documents which contain protein entities.
    """

    protein_docs = []
    # Get number of lines in file for tqdm's sake
    with open(doc_file) as fp:
        num_lines = len(fp.readlines())

    with jsonlines.open(doc_file) as reader:
        # Loop through the JSON lines and collect the relevant documents.
        for line in tqdm(reader, desc=f'Filtering from {doc_file}', total=num_lines):
            sents = line['sents']

            text = get_text_from_sents(sents)

            try:
                # Tag the document text with the NER model.
                doc = nlp(text)
            except ValueError:
                # A value error may arise if the document is too long, so skip it.
                continue

            # Loop through the sentences of the document
            for i, sent in enumerate(doc.sents):
                # Get a set of the entity types in the sentence.
                ent_types = sent_to_ent_types(sent)

                # If one of the types is labeled protein, include it in the output list.
                if 'PROTEIN' in ent_types:
                    # > line.keys()
                    # dict_keys(
                    #   ['doc_id', 'sents', 'source', 'doi', 'pmcid', 'pubmed_id', 'publish_time', 'authors', 'journal']
                    # )
                    # > line['sents'][i].keys()
                    # dict_keys(
                    #   ['sent_id', 'sent_tokens']
                    # )
                    sent_dict = copy.deepcopy(line)
                    # Delete the rest of the sentences.
                    del sent_dict['sents']
                    # Add only the current sentence.
                    sent_dict['sent'] = preprocess_sent(sent)
                    protein_docs.append(sent_dict)

                    # Write to the file periodically and reset the list to save on memory.
                    if len(protein_docs) > 1000:
                        write_jsonl(protein_docs, args.out_file, mode='a')
                        protein_docs = []

    return protein_docs


def write_jsonl(protein_docs, output_file, mode='w'):
    """
    Store relevant doucments in a pickle object.
    :param protein_docs: List of dictionaries which contain relevant documents and metadata.
    :param output_file: Jsonl filename of the output file.
    :return: None
    """
    with jsonlines.open(output_file, mode=mode) as writer:
        writer.write_all(protein_docs)


if __name__ == '__main__':
    doc_files = args.doc_files
    out_file = args.out_file

    protein_docs = []
    # Filter out irrelevant documents in each provided file.
    for doc_file in doc_files:
        file_docs = filter_file(doc_file)

        protein_docs.extend(file_docs)

    print(f'Writing output file at {out_file}')
    # Write to the jsonl output file.
    write_jsonl(protein_docs, out_file, mode='a')
