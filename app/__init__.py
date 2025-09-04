from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .config import Config
from .routes import init_routes

def create_app():
    """
    Cria e configura a aplicação Flask.

    Returns:
        Flask: Instância configurada do Flask.
    """
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY  # Define a chave secreta para segurança

    # Configurações
    app.config.from_object(Config)

    # Inicializa o CSRF para proteção contra ataques
    csrf = CSRFProtect(app)
    csrf.init_app(app)

    # Configura o Flask-Limiter para limitar requisições
    Limiter(app=app, key_func=get_remote_address, default_limits=["500 per hour"])

    # Registra as rotas
    init_routes(app)

    return app