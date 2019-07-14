from flask import Flask, request, render_template
import keras

app = Flask(__name__)

@app.route('/')
def my_form():
    return render_template('form.html')

@app.route('/', methods=['POST'])
def my_form_post():
    symbol = request.form['symbol']
    most_recent_days = request.form['days']
    processed_text = symbol.upper() + most_recent_days.upper() + keras.__version__
    return processed_text


if __name__ == "__main__":
    app.run(debug=False)

