"""
This module implements a (partial, sample) query interface for elasticsearch movie search.
You will need to rewrite and expand sections to support the types of queries over the fields in your UI.
"""

import re
from flask import *
from covid_index import CovidDoc, ks_analyzer
from pprint import pprint
from elasticsearch_dsl import Q
from elasticsearch_dsl.utils import AttrList
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

app = Flask(__name__)

# Initialize global variables for rendering page
tmp_text = ""
tmp_title = ""
tmp_auth = ""
tmp_min = ""
tmp_max = ""
gresults = {}
exact_match = re.compile(r'("(.*)")') #looks for quoted text in queries

# display query page
@app.route("/")
def search():
    return render_template('page_query.html')


# display results page for first set of results and "next" sets.
@app.route("/results", defaults={'page': 1}, methods=['GET', 'POST'])
@app.route("/results/<page>", methods=['GET', 'POST'])
def results(page):
    global tmp_text
    global tmp_title
    global tmp_auth
    global tmp_min
    global tmp_max
    global tmp_type
    global gresults

    # convert the <page> parameter in url to integer.
    if type(page) is not int:
        page = int(page.encode('utf-8'))
        # if the method of request is post (for initial query), store query in local global variables
    # if the method of request is get (for "next" results), extract query contents from client's global variables
    if request.method == 'POST':
        text_query = request.form['query']
        auth_query = request.form['author']
        mintime_query = request.form['mintime']
        search_type = request.form['type']
        if len(mintime_query) is 0:
            mintime = 0
        else:
            mintime = int(mintime_query)
        maxtime_query = request.form['maxtime']
        if len(maxtime_query) is 0:
            maxtime = 99999
        else:
            maxtime = int(maxtime_query)

        # update global variable template data
        tmp_text = text_query
        tmp_auth = auth_query
        tmp_min = mintime
        tmp_max = maxtime
        tmp_type = search_type
    else:
        # use the current values stored in global variables.
        text_query = tmp_text
        auth_query = tmp_auth
        search_type = tmp_type
        mintime = tmp_min
        if tmp_min > 0:
            mintime_query = tmp_min
        else:
            mintime_query = ""
        maxtime = tmp_max
        if tmp_max < 99999:
            maxtime_query = tmp_max
        else:
            maxtime_query = ""

    # store query values to display in search boxes in UI
    shows = {}
    shows['text'] = text_query
    shows['author'] = auth_query
    shows['maxtime'] = maxtime_query
    shows['mintime'] = mintime_query
    shows['type'] = search_type

    # Create a search object to query our index
    search = Search(index='covid_doc_index')

    # Build up your elasticsearch query in piecemeal fashion based on the user's parameters passed in.
    # The search API is "chainable".
    # Each call to search.query method adds criteria to our growing elasticsearch query.
    # You will change this section based on how you want to process the query data input into your interface.

    # search for publication time using a range query
    s = search.query('range', publish_time={'gte': mintime, 'lte': maxtime})

    # Conjunctive search over multiple fields (title and text) using the text_query passed in
    if len(text_query) > 0:
        m = re.search(exact_match, text_query)
        if m:
            s = s.query('query_string', query=text_query, fields=['title', 'text'])
        else:
            if search_type == "disjunctive":
                s = s.query('multi_match', query=text_query, type='cross_fields', fields=['title', 'text'],
                            analyzer=ks_analyzer, operator='or')
            else:
                s = s.query('multi_match', query=text_query, type='cross_fields', fields=['title', 'text'], analyzer=ks_analyzer,
                            operator='and')

    # search for matching authors
    # You should support multiple values (list)
    if len(auth_query) > 0:
        s = s.query('match', authors=auth_query)

    # highlight
    s = s.highlight_options(pre_tags='<mark>', post_tags='</mark>')
    s = s.highlight('text', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('title', fragment_size=999999999, number_of_fragments=1)

    # determine the subset of results to display (based on current <page> value)
    start = 0 + (page - 1) * 10
    end = 10 + (page - 1) * 10

    # execute search and return results in specified range.
    response = s[start:end].execute()

    # insert data into response
    resultList = {}
    for hit in response.hits:
        result = {}
        result['score'] = hit.meta.score

        if 'highlight' in hit.meta:
            if 'title' in hit.meta.highlight:
                result['title'] = hit.meta.highlight.title[0]
            else:
                result['title'] = hit.title

            if 'text' in hit.meta.highlight:
                result['text'] = hit.meta.highlight.text[0]
            else:
                result['text'] = hit.text

        else:
            result['title'] = hit.title
            result['text'] = hit.text
        resultList[hit.meta.id] = result

    # make the result list available globally
    gresults = resultList

    # get the total number of matching results
    result_num = response.hits.total['value']

    # if we find the results, extract title and text information from doc_data, else do nothing
    if result_num > 0:
        return render_template('page_SERP.html', results=resultList, res_num=result_num, page_num=page, queries=shows)
    else:
        message = []
        if len(text_query) > 0:
            message.append('Unknown search term: ' + text_query)
        if len(auth_query) > 0:
            message.append('Cannot find author: ' + auth_query)

        return render_template('page_SERP.html', results=message, res_num=result_num, page_num=page, queries=shows)


# display a particular document given a result number
@app.route("/documents/<res>", methods=['GET'])
def documents(res):
    global gresults
    covid_doc = gresults[res]
    doctitle = covid_doc['title']
    for term in covid_doc:
        if type(covid_doc[term]) is AttrList:
            s = "\n"
            for item in covid_doc[term]:
                s += item + ",\n "
            covid_doc[term] = s
    # fetch the result from the elasticsearch index using its id
    result = CovidDoc.get(id=res, index='covid_doc_index')
    covid_dic = result.to_dict()
    covid_doc['publish_time'] = str(covid_dic['publish_time'])
    return render_template('page_targetArticle.html', film=covid_doc, title=doctitle)


if __name__ == "__main__":
    app.run()
