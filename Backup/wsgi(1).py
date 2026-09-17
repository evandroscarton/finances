"""Ponto de entrada para `flask run` / gunicorn."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
