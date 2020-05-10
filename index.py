"""
Author: Julian Fernandez

This file generates an elasticsearch index. Run this before running web_app.py.
Make sure that elasticsearch is running in the background beforehand.
"""


import csv
import time

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import Index, Document, Text
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import analyzer

# Connect to local host server
connections.create_connection(hosts=['127.0.0.1'])

# Create elasticsearch object
es = Elasticsearch()

# Analyzers for both the predicate and arguments.
predicate_analyzer = analyzer('covid_predicate_analyzer',
                              tokenizer='whitespace',
                              # Use a stemmer to capture predicates with similar stems.
                              filter=['lowercase', 'stemmer'])

argument_analyzer = analyzer('covid_argument_analyzer',
                             tokenizer='whitespace',
                             filter=['lowercase'])


class RelationDocument(Document):
    """
    A RelationDocument contains two text fields for querying over.
    predicate refers to the tuple's first element.
    arguments refers to the tuple's remaining elements.
    """
    predicate = Text(analyzer=predicate_analyzer)
    arguments = Text(analyzer=argument_analyzer)

    def save(self, *args, **kwargs):
        return super(RelationDocument, self).save(*args, **kwargs)


def build_index():
    """
    Main function of this module. Build the covid relation index.
    :return: None
    """
    covid_index = Index('covid_relation_index')

    if covid_index.exists():
        # Overwrite any previous version
        covid_index.delete()

    covid_index.document(RelationDocument)

    covid_index.create()

    metadata = {}
    with open('data/relations.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)

        # For each value in the CSV file, create a dictionary entry to store
        # it's information in the appropriate place.
        for i, cols in enumerate(reader):
            metadata[str(i+1)] = {}
            for key, col in zip(header, cols):
                # If the value type is triple, decompose the value
                # into arg subcomponents.
                if key == 'triple':
                    # Get the predicate and the arguments.
                    predicate, *args = col[2:-2].replace('\'', '').split(',')
                    metadata[str(i+1)]['predicate'] = predicate
                    metadata[str(i + 1)]['arguments'] = args
                else:
                    metadata[str(i+1)][key] = col

    def actions():
        for rel_id in range(1, len(metadata)+1):
            dict_id = str(rel_id)
            try:
                yield {
                    '_index': 'covid_relation_index',
                    '_type': '_doc',
                    '_id': rel_id,
                    # The DOI allows us to link directly to the article's page where it's hosted.
                    'doi': metadata[dict_id]['doi'],
                    # The doc_id refers to the CORD-NER-corpus.json dataset. This field is unused in our web app.
                    'doc_id': metadata[dict_id]['doc_id'],
                    # Sent refers to the sentence from which the document was drawn.
                    'sent': metadata[dict_id]['sent'],
                    # Predicate refers to the predicate as explained in the RelationDocument class
                    'predicate': metadata[dict_id]['predicate'],
                    # Argument refers to the arguments as explained in the RelationDocument class
                    'arguments': metadata[dict_id]['arguments'],
                }
            except ValueError:
                continue

    helpers.bulk(es, actions())


# Run this module to build the index.
if __name__ == '__main__':
    start_time = time.time()
    build_index()
    print(f'=== Built index in {time.time() - start_time} seconds ===')
