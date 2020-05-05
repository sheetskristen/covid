import csv
import re

from tqdm import tqdm
import jsonlines
import spacy

fi = 'data/CORD-NER-PROTEIN-500.jsonl'
fo = 'data/relations.csv'
nlp = spacy.load('en_ner_jnlpba_md')

def open_ner_data(fi):
    with jsonlines.open(fi) as reader:
        data = [line for line in tqdm(reader, desc="Opening file")]
    return data

def create_string(tokenized_sent):
    return  ' '.join(tokenized_sent)

def create_text_doc(data):
    text = [(create_string(sent['sent_tokens']), doc['doc_id'], sent['sent_id']) for doc in data for sent in doc['sents']]
    # return ' '.join(text)
    return text

def parse(data):
    triples = []
    text = create_text_doc(data)
    for (sent, doc_id, sent_id) in tqdm(text, desc="Parsing sentences"):
        doc = nlp(sent)
        triple = {}
        for token in doc:
            if token.dep_ == "ROOT":
                # token.lemma_
                triple.update({'doc_id': doc_id, 'sent_id': sent_id})
                triple_lst = [token.lemma_]
                for child in token.children:
                    # if child.pos_ == "NOUN":
                    left_edge = child.left_edge.i
                    right_edge = child.right_edge.i + 1
                    triple_lst.append(doc[left_edge:right_edge].text)
                    # triple_lst.append(re.sub(r'\s\d*\s', '', doc[left_edge:right_edge].text))
                triple.update({'triple': tuple(triple_lst)})
        triples.append(triple)
    return triples

if __name__ == '__main__':
    data = open_ner_data(fi)
    triples = parse(data)
    with open(fo, 'w', encoding='utf-8') as output_file:
        fieldnames = list(triples[0].keys())
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for relation in tqdm(triples, desc="Writing file"):
            writer.writerow(relation)