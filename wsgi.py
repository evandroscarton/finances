"""Ponto de entrada da aplicação. FLASK_APP=wsgi no .env."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
