"""Módulo de inicialização da aplicação Flask (Application Factory).

Este módulo contém a factory `create_app` que é responsável por criar e
configurar a instância da aplicação Flask, juntamente com todas as suas
extensões, como SQLAlchemy, SocketIO, e CSRFProtect.

A utilização do padrão de factory permite criar múltiplas instâncias da
aplicação com diferentes configurações, o que é especialmente útil para
testes.
"""
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
from .routes import init_routes

# Instâncias das extensões Flask.
# São inicializadas aqui para serem importadas em outros módulos sem causar
# importações circulares. A vinculação com a aplicação (`.init_app()`)
# ocorre dentro da factory `create_app`.
socketio = SocketIO()
db = SQLAlchemy()
migrate = Migrate()

def create_app(testing=False):
    """Cria e configura uma instância da aplicação Flask.

    Esta função segue o padrão de Application Factory. Ela configura a aplicação
    a partir de um objeto de configuração, inicializa as extensões do Flask,
    registra as rotas e prepara a aplicação para ser executada.

    Args:
        testing (bool, optional): Se True, a aplicação é configurada para o
            ambiente de testes. Isso inclui desabilitar o CSRF e usar um
            banco de dados em memória. Defaults to False.

    Returns:
        tuple[Flask, SocketIO]: Uma tupla contendo a instância da aplicação
            Flask (`app`) e a instância do SocketIO (`socketio`) configuradas.
    """
    app = Flask(__name__)

    # Carrega as configurações a partir da classe Config
    app.config.from_object(Config)

    if testing:
        # Sobrescreve configurações para o modo de teste
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Desabilita CSRF para testes
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Usa banco de dados em memória
        app.config['TEMPLATES_FILE_PATH'] = 'test_templates.json'

    # Define a chave secreta para segurança do CSRF e sessões
    app.secret_key = Config.SECRET_KEY

    # Inicializa a proteção CSRF
    CSRFProtect(app)

    # Inicializa o SQLAlchemy e o Flask-Migrate com a aplicação
    db.init_app(app)
    migrate.init_app(app, db)

    # Configura o limitador de requisições, exceto em modo de teste
    if not testing:
        Limiter(app=app, key_func=get_remote_address, default_limits=["500 per hour"])

    # Inicializa o SocketIO com a aplicação
    socketio.init_app(app)

    # Registra as rotas da aplicação
    init_routes(app)

    # Importa os modelos para que o SQLAlchemy e o Alembic os reconheçam
    from . import models

    return app, socketio
