import jsonlines
import argparse
import spacy
import pickle
from tqdm import tqdm
import pathlib
import os.path

# Export load_docs() for use in other modules.
# This loads the docs from their pickle file which is the output
# of running this file.
# They have the form:
# {
#   id: paper SHA code
#   label: containing dataset (comm_use_subset, biorxiv_medrxiv, etc)
#   doc: Spacy doc of a sentence which contains a protein entity.
# }
__all__ = ['load_docs']


def load_docs(pickle_filename):
    """
    Load docs from pickle.

    Usage:

    from document_filter import load_docs
    docs = load_docs('data/pickle/rel_docs.pickle')
    ...

    :param pickle_filename: pickle file were docs are stored.
    :return: a list of dictionaries which contain relevant documents and their metadata.
    """
    with open(pickle_filename, 'rb') as fp:
        docs = pickle.load(fp)

    return docs


# Load SciSpacy's JNLPBA NER model.
# It tags entities with the ontology [DNA, CELL_TYPE, CELL_LINE, RNA, PROTEIN].
nlp = spacy.load('en_ner_jnlpba_md')

# Command line arguments.
parser = argparse.ArgumentParser(description='Filter relevant JSONL documents with'
                                             ' SciSpacy\'s en_ner_jnlpba_md NER model.')

parser.add_argument('--doc_files', type=str, nargs='+',
                    default=['data/tmnt/_biorxiv_medrxiv.jsonl',
                             'data/tmnt/_comm_use_subset.jsonl',
                             'data/tmnt/_noncomm_use_subset.jsonl'],
                    help='List of filepaths to JSONL files which contain documents to be filtered.')
parser.add_argument('--out_folder', type=str, default='data/pickle/',
                    help='Folder which stores pickled relevant documents')

args = parser.parse_args()


def sent_to_ent_types(doc):
    """
    Return a set of the entity types contained in a Spacy document object.
    :param doc: A Spacy Document object
    :return: a set of the entity types contained in the sentence.
    """
    return set(map(lambda e: e.label_, doc.ents))

def filter_file(doc_file):
    """
    Get a list of dictionaries which contain the relevant sentences along with metadata.
    :param doc_file: JSONL filepath which contains documents for tagging.
    :return: List of dictionaries which contain Spacy documents which contain protein entities.
    """

    protein_docs = []
    with jsonlines.open(doc_file) as reader:
        # Loop through the JSON lines and collect the relevant documents.
        for line in tqdm(list(reader), desc=f'Filtering from {doc_file}'):
            sent_id = line['id']
            sent_label = line['label']
            sent = line['text']

            # Tag the sentence with the NER model.
            # NOTE: it's slow to tag each sentence as its own document,
            # but Spacy can't handle the whole file's sentences as a document.
            # NER tagging could be done in batches to speed up this function,
            # but since we're pickling its output, it's okay that it's slow.
            doc = nlp(sent)

            # Get a set of the entity types in the sentence.
            ent_types = sent_to_ent_types(doc)

            # If one of the types is labeled protein, include it in the output list.
            if 'PROTEIN' in ent_types:
                # Store ID and label alongside Spacy document so we can later refer back
                # to where the sentence came from.
                protein_docs.append({
                    'id': sent_id,
                    'label': sent_label,
                    'doc': doc
                })

    return protein_docs


def pickle_docs(protein_docs, pickle_folder):
    """
    Store relevant doucments in a pickle object.
    :param protein_docs: List of dictionaries which contain relevant documents and metadata.
    :param pickle_filename: Filename where the pickle object will be stored.
    :return: None
    """
    # Make the folder if necessary.
    pathlib.Path(pickle_folder).mkdir(parents=True, exist_ok=True)

    pickle_filename = os.path.join(pickle_folder, 'rel_docs.pickle')

    print(f'Pickling docs at {pickle_filename}')
    with open(pickle_filename, 'wb') as fp:
        pickle.dump(protein_docs, fp)


if __name__ == '__main__':
    doc_files = args.doc_files
    out_folder = args.out_folder

    protein_docs = []
    # Filter out irrelevant documents in each provided file.
    for doc_file in doc_files:
        file_docs = filter_file(doc_file)

        protein_docs.extend(file_docs)

    # Pickle the relevant documents.
    pickle_docs(protein_docs, out_folder)
