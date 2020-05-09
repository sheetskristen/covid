from flask import *


app = Flask(__name__)


@app.route('/')
def search_page():
    return render_template('page_query.html')


@app.route('/results', methods=['GET', 'POST'])
def results_page():
    return render_template('page_results.html')


@app.route("/documents/<result>", methods=['GET'])
def target_page():
    return render_template('page_target.html')

if __name__ == '__main__':
    app.run(debug=True)
