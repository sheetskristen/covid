import json
from os import walk
from string import punctuation
import re

import jsonlines
from nltk import word_tokenize
from nltk.corpus import stopwords
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from tqdm import tqdm

folders = ['biorxiv_medrxiv', 'comm_use_subset', 'noncomm_use_subset', 'pmc_custom_liscence']
directory = './data/2020-03-13/'
stop_words = stopwords.words('english') + list(punctuation) + ['preprint', 'copyright', 'holder', 'license', 'cc', 'nc',
                                                               'nd', 'doi', 'CC-BY-NC-ND', 'biorxiv', 'medrxiv',
                                                               'author', 'peer', 'funder', 'author/funder']
parenthetical = re.compile(r'(\((\s){0,1}(\w*|(\w+(\, |-|\s))){1,}\)(\s){0,1})')
double_parenthetical = re.compile(r'(\((\s){0,1}(\w*\s){1,}(\([\w|-|,|.|\s|%]*\))(\s){0,1}\))')
reference = re.compile(r'((\(|\[)(\d|,\s\d){1,}(\)|\]))')
folder = re.compile(r'(\w*)$')

url = re.compile(r'(https:[\S]*)')
fig = re.compile(r'(\(((\s){0,1}[F|f]ig(.){0,1}\s\w*(\s){0,1}|,\s[F|f]ig(.){0,1}\s\w*){1,}\))')
cc = 'CC-BY-NC-ND 4.0 International license'
perp = 'who has granted medRxiv a license to display the preprint in perpetuity'
avail = 'It is made available under a'
ch = 'The copyright holder for this preprint'
doi = 'doi: medRxiv preprint'
pr = '(which was not peer-reviewed)'

def tokenize(text):
    words = [w.lower() for w in word_tokenize(text)]
    return [w for w in words if w not in stop_words and not w.isdigit()]

def tf_ifd(docs):
    cvec = CountVectorizer(stop_words=stop_words, min_df=3, max_df=0.5)
    sf = cvec.fit_transform(docs)
    transformer = TfidfTransformer()
    transformed_weights = transformer.fit_transform(sf)
    weights = np.asarray(transformed_weights.mean(axis=0)).ravel().tolist()
    weights_df = pd.DataFrame({'term': cvec.get_feature_names(), 'weight': weights})

    return weights_df.sort_values(by='weight', ascending=False).head(50)

def pre_process(text):
    text = re.sub(url, '', text)
    text = re.sub(reference, '', text)
    text = re.sub(fig, '', text)
    text = text.replace(cc, '')
    text = text.replace(perp, '')
    text = text.replace(avail, '')
    text = text.replace(ch, '')
    text = text.replace(doi, '')
    text = text.replace(pr, '')
    print(text)
    text = ' '.join(tokenize(text))
    print(text)

    return text

if __name__ == '__main__':

    for (dirpath, dirnames, filenames) in walk(directory, topdown=True):
        dirnames[:] = [d for d in dirnames if d in folders]
        if len(dirnames) == 0 and filenames:
            dirname = folder.findall(dirpath)[0]
            documents = []
            for filepath in tqdm(filenames, desc=dirname):
                with open(dirpath + '/' + filepath) as f:
                    paper = json.load(f)
                    paper_id = paper['paper_id']
                    body_text = paper['body_text']
                    for t in body_text:
                        text = pre_process(t['text'])
                        if text:
                            documents.append({'id': paper_id,
                                              'label': dirname,
                                              'text': text})

            dataset = './data/tmnt/_' + dirname + '.jsonl'
            with jsonlines.open(dataset, 'w') as jsonl:
                jsonl.write_all(documents)

    # docs = [d['text'] for d in documents]





