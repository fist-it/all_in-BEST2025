from flask import Flask, render_template

app = Flask(__name__)


def main():
    # Uruchomienie serwera w trybie deweloperskim
    app.run(debug=True)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    main()
