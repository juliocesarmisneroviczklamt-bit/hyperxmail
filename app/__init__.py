from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from .config import Config
from .routes import init_routes

# Cria a instância do SocketIO
socketio = SocketIO()

def create_app():
    """
    Cria e configura a aplicação Flask e o SocketIO.

    Returns:
        tuple: Instância configurada do Flask e do SocketIO.
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

    # Inicializa o SocketIO com a app
    socketio.init_app(app)

    # Registra as rotas
    init_routes(app)

    return app, socketio