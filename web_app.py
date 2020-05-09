from flask import *


app = Flask(__name__)


@app.route('/')
def search_page():
    return render_template('page_query.html')




if __name__ == '__main__':
    app.run(debug=True)
