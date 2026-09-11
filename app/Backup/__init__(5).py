"""
Application Factory do sistema Finance.
Registra blueprints, configura sessão, banco e filtros Jinja customizados.
"""
import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

from db.connection import init_pool
from services import auth_service
from utils.filtros_jinja import moeda_br

load_dotenv()

login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

    # init_pool() lê host/port/dbname/user/password direto das env vars
    # (com defaults), não recebe parâmetros.
    init_pool()

    login_manager.init_app(app)

    # Filtro customizado: {{ valor|moeda_br }} -> formatação pt-BR (milhar '.', decimal ',')
    app.jinja_env.filters["moeda_br"] = moeda_br

    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.contas_routes import contas_bp
    from routes.cartoes_routes import cartoes_bp
    from routes.categorias_routes import categorias_bp
    from routes.lancamentos_routes import lancamentos_bp
    from routes.transferencias_routes import transferencias_bp
    from routes.relatorios_routes import relatorios_bp
    from routes.extrato_routes import extrato_bp
    from routes.lancamentos_previstos_routes import lancamentos_previstos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(contas_bp)
    app.register_blueprint(cartoes_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(lancamentos_bp)
    app.register_blueprint(transferencias_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(extrato_bp)
    app.register_blueprint(lancamentos_previstos_bp)

    @login_manager.user_loader
    def load_user(user_id):
        # Reutiliza a função já existente em auth_service, que consulta
        # o usuário por id e retorna um objeto Usuario (UserMixin).
        return auth_service.carregar_usuario(user_id)

    return app

    def formatar_moeda_br(valor):
        """
        Formata NUMERIC como moeda brasileira: R$ 1.234,56 (negativo -> -R$ 1.234,56).
        Evita usar locale do sistema operacional (não confiável entre ambientes).
        """
        valor = float(valor)
        sinal = "-" if valor < 0 else ""
        valor_abs = abs(valor)
        inteiro, decimal = f"{valor_abs:.2f}".split(".")
        inteiro_formatado = f"{int(inteiro):,}".replace(",", ".")
        return f"{sinal}R$ {inteiro_formatado},{decimal}"

    app.jinja_env.filters["moeda_br"] = formatar_moeda_br
