"""
Application Factory. Centraliza criação do app, configuração via .env,
registro de Blueprints e setup do Flask-Login.
"""
import os
from flask import Flask, jsonify
from flask_login import LoginManager
from dotenv import load_dotenv

from db.connection import init_pool
from routes.auth_routes import auth_bp, carregar_usuario
from routes.contas_routes import contas_bp
from routes.cartoes_routes import cartoes_bp
from routes.categorias_routes import categorias_bp
from routes.lancamentos_routes import lancamentos_bp
from routes.transferencias_routes import transferencias_bp

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")

    init_pool()

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.user_loader(carregar_usuario)

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"erro": "Autenticação necessária."}), 401

    app.register_blueprint(auth_bp)
    app.register_blueprint(contas_bp)
    app.register_blueprint(cartoes_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(lancamentos_bp)
    app.register_blueprint(transferencias_bp)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado."}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"erro": "Erro interno do servidor."}), 500

    return app
