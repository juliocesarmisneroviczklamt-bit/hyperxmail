"""Modelos de banco de dados da aplicação.

Este módulo define as tabelas do banco de dados usando o SQLAlchemy ORM.
Os modelos representam as entidades centrais da aplicação: campanhas de e-mail,
os e-mails individuais enviados, e os eventos de rastreamento (aberturas e cliques).

- Campaign: Representa uma campanha de e-mail marketing.
- Email: Representa um e-mail individual enviado como parte de uma campanha.
- Open: Registra um evento de abertura de um e-mail.
- Click: Registra um evento de clique em um link dentro de um e-mail.
"""
from . import db
from datetime import datetime

class Campaign(db.Model):
    """Representa uma campanha de e-mail.

    Uma campanha agrupa um conjunto de e-mails enviados com o mesmo assunto
    e mensagem.

    Attributes:
        id (int): A chave primária da campanha.
        subject (str): O assunto dos e-mails da campanha.
        message (str): O corpo da mensagem (conteúdo HTML) dos e-mails.
        created_at (datetime): O timestamp de quando a campanha foi criada.
        emails (relationship): Relacionamento com os e-mails individuais
            desta campanha.
    """
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    emails = db.relationship('Email', backref='campaign', lazy=True)

class Email(db.Model):
    """Representa um e-mail individual enviado em uma campanha.

    Cada registro de e-mail está associado a uma campanha e a um destinatário
    específico. O ID é um UUID para permitir o rastreamento único e anônimo.

    Attributes:
        id (str): A chave primária, um UUID de 36 caracteres.
        campaign_id (int): Chave estrangeira para a tabela `Campaign`.
        recipient (str): O endereço de e-mail do destinatário.
        sent_at (datetime): O timestamp de quando o e-mail foi enviado.
        opens (relationship): Relacionamento com os eventos de abertura deste e-mail.
        clicks (relationship): Relacionamento com os eventos de clique deste e-mail.
    """
    id = db.Column(db.String(36), primary_key=True)  # Usando UUIDs como IDs
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    opens = db.relationship('Open', backref='email', lazy=True)
    clicks = db.relationship('Click', backref='email', lazy=True)

class Open(db.Model):
    """Registra um evento de abertura de e-mail.

    Cada vez que o pixel de rastreamento em um e-mail é carregado, um registro
    desta classe é criado.

    Attributes:
        id (int): A chave primária do registro de abertura.
        email_id (str): Chave estrangeira para o e-mail que foi aberto.
        opened_at (datetime): O timestamp do evento de abertura.
    """
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('email.id'), nullable=False)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)

class Click(db.Model):
    """Registra um evento de clique em um link de e-mail.

    Quando um usuário clica em um link rastreável em um e-mail, um registro
    desta classe é criado, armazenando a URL original de destino.

    Attributes:
        id (int): A chave primária do registro de clique.
        email_id (str): Chave estrangeira para o e-mail onde o clique ocorreu.
        url (str): A URL original para a qual o usuário foi redirecionado.
        clicked_at (datetime): O timestamp do evento de clique.
    """
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('email.id'), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
