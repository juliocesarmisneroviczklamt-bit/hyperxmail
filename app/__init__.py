from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from .config import Config
from .routes import init_routes

# Cria a instância do SocketIO e do SQLAlchemy
socketio = SocketIO()
db = SQLAlchemy()

def create_app(testing=False):
    """
    Cria e configura a aplicação Flask e o SocketIO.

    Args:
        testing (bool): Se True, configura a aplicação para testes.

    Returns:
        tuple: Instância configurada do Flask e do SocketIO.
    """
    app = Flask(__name__)

    # Configurações
    app.config.from_object(Config)

    if testing:
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Desabilita CSRF para testes
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Usa um banco de dados em memória

    # Define a chave secreta para segurança do CSRF
    app.secret_key = Config.SECRET_KEY

    # Inicializa o CSRF para proteção contra ataques (se não estiver em modo de teste)
    if not testing:
        CSRFProtect(app)

    # Inicializa o banco de dados
    db.init_app(app)

    # Configura o Flask-Limiter para limitar requisições (se não estiver em modo de teste)
    if not testing:
        Limiter(app=app, key_func=get_remote_address, default_limits=["500 per hour"])

    # Inicializa o SocketIO com a app
    socketio.init_app(app)

    # Registra as rotas
    init_routes(app)

    from . import models

    with app.app_context():
        db.create_all()

    return app, socketio
