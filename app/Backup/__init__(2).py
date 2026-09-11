"""
Application Factory. Registra blueprints, configura Flask-Login,
carrega variáveis de ambiente e registra filtro Jinja customizado.
"""
import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    from services.auth_service import carregar_usuario

    @login_manager.user_loader
    def load_user(usuario_id):
        return carregar_usuario(usuario_id)

    # Filtro customizado para valor absoluto em templates Jinja
    app.jinja_env.filters["abs"] = abs

    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.contas_routes import contas_bp
    from routes.cartoes_routes import cartoes_bp
    from routes.categorias_routes import categorias_bp
    from routes.lancamentos_routes import lancamentos_bp
    from routes.transferencias_routes import transferencias_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(contas_bp)
    app.register_blueprint(cartoes_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(lancamentos_bp)
    app.register_blueprint(transferencias_bp)

    return app
