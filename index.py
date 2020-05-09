import csv

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import Index, Document, Text
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import analyzer

# Connect to local host server
connections.create_connection(hosts=['127.0.0.1'])

# Create elasticsearch object
es = Elasticsearch()

predicate_analyzer = analyzer('covid_predicate_analyzer',
                              tokenizer='whitespace',
                              filter=['lowercase'])

argument_analyzer = analyzer('covid_argument_analyzer',
                             tokenizer='whitespace',
                             filter=['lowercase'])


class RelationDocument(Document):
    predicate = Text(analyzer=predicate_analyzer)

    #                                 multi=True here v?
    argument_analyzer = Text(analyzer=argument_analyzer)

    def save(self, *args, **kwargs):
        return super(RelationDocument, self).save(*args, **kwargs)


def build_index():
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
        for i, cols in enumerate(reader):
            for key, col in zip(header, cols):
                metadata[str(i+1)][key] = col

    def actions():
        for rel_id in range(1, len(metadata)+1):
            dict_id = str(rel_id)
            try:
                yield {
                    '_index': 'covid_relation_index',
                    '_type': '_doc',
                    '_id': rel_id,
                    'doi': metadata[dict_id]['doi'],
                    'doc_id': metadata[dict_id]['doc_id'],
                    'sent': metadata[dict_id]['sent'],
                    'relation': metadata[dict_id]['triple']
                }
            except ValueError:
                continue

    helpers.bulk(es, actions())


if __name__ == '__main__':
    build_index()