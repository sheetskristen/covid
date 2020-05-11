"""
Author: Julian Fernandez

This module defines a web app for querying over our extracted protein tuples.

index.py must be run before this file as the web app uses that module's output index for querying over.

View the web app in your browser with the link provided upon running this file.
"""

from flask import *
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections


app = Flask(__name__)

# Connect to local host server
connections.create_connection(hosts=['127.0.0.1'])


g_predicate = ''
g_args = []
g_search_type = 'and'


@app.route('/')
def search_page():
    """
    Render the homepage of the UI. Users query here.
    :return: the rendered root page.
    """
    return render_template('page_query.html', search_label=g_search_type)


@app.route('/results', defaults={'page_num': 1}, methods=['GET', 'POST'])
@app.route("/results/<page_num>", methods=['GET', 'POST'])
def results_page(page_num):
    """

    :return: rendered SERP page.
    """
    global g_predicate, g_args, g_search_type

    # Convert the <page_num> parameter in url to integer.
    if type(page_num) is not int:
        page_num = int(page_num.encode('utf-8'))

    # Get form info.
    if request.method == 'POST':
        predicate = request.form['predicate']
        # Get all the arguments to the predicate.
        # There are len(request.form)-2 arguments by the structure of the form.
        args = [request.form[f'arg{arg_num + 1}'] for arg_num in range(len(request.form) - 2)]

        search_type = request.form['search-type']

        g_predicate = predicate
        g_args = args
        g_search_type = search_type
    else:
        predicate = g_predicate
        args = g_args
        search_type = g_search_type

    # Query over form info.
    s = Search(index='covid_relation_index')

    if predicate != '':
        # Query over predicate.
        s = s.query('query_string',
                    query=predicate,
                    fields=['predicate'],
                    default_operator=search_type)

    # Query over args.
    arg_query_string = ' '.join([arg for arg in args if arg != ''])
    if arg_query_string != '':
        s = s.query('query_string',
                    query=arg_query_string,
                    fields=['arguments'],
                    default_operator=search_type)

    # determine the subset of results to display (based on current <page> value)
    start = 0 + (page_num - 1) * 10
    end = 10 + (page_num - 1) * 10

    # Use query results to pass a result-list into the template.
    response = s[start:end].execute()
    result_list = {}
    for hit in response.hits:
        result = {
            'score': hit.meta.score,
            'doi': hit.doi,
            'sent': hit.sent,
            'predicate': hit.predicate,
            'arguments': hit.arguments,
        }

        result_list[hit.meta.id] = result

    num_results = response.hits.total['value']

    # Set args to be two empty strings so that the values can be set in the form.
    if len(args) == 0:
        args = ['', '']

    return render_template('page_results.html', num_results=num_results, result_list=result_list,
                           predicate=predicate, args=args, search_label=search_type, page_num=page_num)


if __name__ == '__main__':
    app.run(debug=True)
