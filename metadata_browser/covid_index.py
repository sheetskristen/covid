import json
import math
import re
import time

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import Index, Document, Text, Keyword, Integer
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import tokenizer, analyzer
from elasticsearch_dsl.query import MultiMatch, Match

year = re.compile(r'(\d\d\d\d)') #regex pattern for year

# Connect to local host server
connections.create_connection(hosts=['127.0.0.1'])

# Create elasticsearch object
es = Elasticsearch()

# Define analyzers appropriate for your data.
# You can create a custom analyzer by choosing among elasticsearch options
# or writing your own functions.
# Elasticsearch also has default analyzers that might be appropriate.

#used of simple text
basic_analyzer = analyzer('custom',
                          tokenizer='classic',
                          filter=['lowercase'])

#used for robust text
ks_analyzer = analyzer('custom',
                        tokenizer='standard',
                        filter=['lowercase', 'asciifolding', 'porter_stem'])


# Define document mapping (schema) by defining a class as a subclass of Document.
# This defines fields and their properties (type and analysis applied).
class CovidDoc(Document):
    title = Text(analyzer=ks_analyzer)
    abstract = Text(analyzer=ks_analyzer)
    authors = Text(analyzer=basic_analyzer)
    publish_time =  Text(analyzer='simple')


    # override the Document save method to include subclass field definitions
    def save(self, *args, **kwargs):
        return super(CovidDoc, self).save(*args, **kwargs)


# Populate the index
def buildIndex():
    """
    buildIndex creates a new film index, deleting any existing index of
    the same name.
    It loads a json file containing the covid doc metadata corpus and does bulk loading
    using a generator function.
    """
    doc_index = Index('covid_doc_index')
    if doc_index.exists():
        doc_index.delete()  # Overwrite any previous version
    doc_index.analyzer(basic_analyzer)  # register your customized analyzer as the default analyzer
    doc_index.create()

    # Open the covid metadata corpus
    with open('covid_comm_use_subset_meta.json', 'r', encoding='utf-8') as data_file:
        enum_id = 1
        documents = {}
        for line in data_file:
            try:
                doc = json.loads(line)
                for key in doc.keys():
                    if type(doc.get(key)) is not str:
                        if math.isnan(doc.get(key)):
                            doc.update({key: None})
                    if key == "publish_time" and doc.get(key) and len(doc.get(key)) > 4:
                        match = re.search(year, doc[key]).group(0)
                        if match:
                            doc.update({key: match})
                documents.update({str(enum_id): doc})
                enum_id+=1
            except json.decoder.JSONDecodeError:
                continue
        # load doc metadata from json file into dictionary
        size = len(documents)

    # Action series for bulk loading with helpers.bulk function.
    # Implemented as a generator, to return one movie with each call.
    # Note that we include the index name here.
    # The Document type is always 'doc'.
    # Every item to be indexed must have a unique key.
    def actions():
        # enum_id is an enumerated id created when reading the json and used as key into covid metadata dictionary)
        for enum_id in range(1, size + 1):
            yield {
                "_index": "covid_doc_index",
                "_type": 'doc',
                "_id": enum_id,
                "title": documents[str(enum_id)].get('title', 'None'),
                "text": documents[str(enum_id)].get('abstract', 'None'),
                "authors": documents[str(enum_id)].get('authors', 'None'),
                "publish_time": documents[str(enum_id)].get('publish_time', int(0000))
            }

    helpers.bulk(es, actions())


# command line invocation builds index and prints the running time.
def main():
    start_time = time.time()
    buildIndex()
    print("=== Built index in %s seconds ===" % (time.time() - start_time))


if __name__ == '__main__':
    main()
