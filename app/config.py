from decouple import config
import os

class Config:
    """
    Configurações centralizadas para a aplicação.
    """
    # Chave secreta para o Flask (necessária para CSRF e sessões)
    SECRET_KEY = config('SECRET_KEY', default=os.urandom(24).hex())

    # Configurações do Banco de Dados
    SQLALCHEMY_DATABASE_URI = config('SQLALCHEMY_DATABASE_URI', default='sqlite:///tracking.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Credenciais e configurações de e-mail
    EMAIL_SENDER = config('EMAIL_SENDER')
    EMAIL_PASSWORD = config('EMAIL_PASSWORD')
    SMTP_SERVER = config('SMTP_SERVER', default='smtp.office365.com')
    SMTP_PORT = config('SMTP_PORT', default=587, cast=int)

    # Limites de envio
    EMAILS_PER_HOUR = config('EMAILS_PER_HOUR', default=500, cast=int)
    SECONDS_PER_EMAIL = 3600 / EMAILS_PER_HOUR

    # Chave da API do TinyMCE
    TINYMCE_API_KEY = config('TINYMCE_API_KEY', default='no-api-key')

    # Tamanho máximo do anexo (em bytes)
    MAX_ATTACHMENT_SIZE = config('MAX_ATTACHMENT_SIZE', default=10 * 1024 * 1024, cast=int)

    # Configurações de segurança dos cookies
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
