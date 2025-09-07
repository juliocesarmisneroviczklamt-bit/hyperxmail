# HyperXMail: Ferramenta de E-mail Marketing e Rastreamento de Campanhas

HyperXMail é uma aplicação web robusta construída com Flask, projetada para o envio de e-mails em massa, gerenciamento de campanhas e rastreamento detalhado de interações. É uma solução ideal para desenvolvedores e pequenas equipes que precisam de uma ferramenta de e-mail marketing auto-hospedada e personalizável.

## Funcionalidades

- **Envio de E-mail em Massa**: Envie e-mails para um grande número de destinatários usando um servidor SMTP configurado.
- **Rastreamento de Campanhas**: Monitore o desempenho de suas campanhas com rastreamento de aberturas e cliques.
- **Relatórios Detalhados**: Visualize relatórios por campanha, incluindo taxas de abertura e de cliques.
- **Editor Rich Text**: Componha e-mails em HTML usando um editor WYSIWYG integrado.
- **Gerenciamento de Templates**: Salve e carregue templates de e-mail para agilizar a criação de campanhas.
- **Suporte a Anexos**: Envie anexos nos formatos JPG, PNG e PDF (limite de 10MB por arquivo).
- **Imagens Embutidas**: Incorpore imagens diretamente no corpo do e-mail usando `cid` para uma melhor experiência do usuário.
- **Upload de CSV**: Importe listas de destinatários facilmente a partir de arquivos CSV.
- **Segurança**:
  - **Proteção CSRF**: Integrado com Flask-WTF para prevenir ataques de Cross-Site Request Forgery.
  - **Sanitização de Entradas**: Todas as entradas do usuário, incluindo nomes de arquivos de anexos, são sanitizadas para prevenir ataques de Cross-Site Scripting (XSS).
  - **Limitação de Taxa**: Limita o número de requisições para proteger contra abuso.

## Arquitetura da Aplicação

A aplicação segue uma arquitetura modular baseada no padrão de fábrica de aplicações Flask.

- **Backend**:
  - **Flask**: O micro-framework principal que gerencia as rotas, requisições e a lógica da aplicação.
  - **SQLAlchemy & Flask-SQLAlchemy**: ORM para a interação com o banco de dados.
  - **Flask-Migrate**: Gerencia as migrações do esquema do banco de dados, permitindo atualizações seguras.
  - **SocketIO & Flask-SocketIO**: Fornece comunicação em tempo real via WebSockets para relatar o progresso do envio de e-mails.
  - **Asyncio**: Utilizado para gerenciar tarefas de envio de e-mail de forma concorrente.

- **Frontend**:
  - **HTML5 / CSS3**: Estrutura e estilo da interface do usuário.
  - **JavaScript (Vanilla)**: Manipulação do DOM, interações do usuário e comunicação com o backend via `fetch` e WebSockets.
  - **TinyMCE**: Editor de texto rico para a composição de e-mails.

- **Banco de Dados**:
  - Utiliza SQLite por padrão para desenvolvimento, mas pode ser facilmente configurado para usar outros bancos de dados suportados pelo SQLAlchemy (ex: PostgreSQL, MySQL).

## Instalação

Siga os passos abaixo para configurar e executar o ambiente de desenvolvimento local.

**Pré-requisitos**:
- Python 3.8+
- Um servidor SMTP (ex: Gmail, SendGrid, etc.)

**1. Clone o Repositório**
```bash
git clone <URL_DO_REPOSITORIO>
cd hyperxmail
```

**2. Crie e Ative um Ambiente Virtual**
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

**3. Instale as Dependências**
```bash
pip install -r requirements.txt
```

## Configuração

A aplicação utiliza um arquivo `.env` para gerenciar as variáveis de ambiente.

**1. Crie o arquivo `.env`**
Copie o exemplo abaixo e crie um arquivo chamado `.env` na raiz do projeto.

```env
# Chave secreta para a aplicação Flask (mude para um valor seguro)
SECRET_KEY='uma-chave-super-secreta-e-longa'

# URI do Banco de Dados (padrão para SQLite)
SQLALCHEMY_DATABASE_URI='sqlite:///app.db'

# Configurações do Servidor SMTP
EMAIL_SENDER='seu-email@dominio.com'
EMAIL_PASSWORD='sua-senha-de-app-ou-normal'
SMTP_SERVER='smtp.seu-provedor.com'
SMTP_PORT=587
```

**2. Configure as Variáveis**
- `SECRET_KEY`: Uma string longa e aleatória usada para proteger sessões e cookies.
- `SQLALCHEMY_DATABASE_URI`: A string de conexão para o banco de dados. O padrão `sqlite:///app.db` cria um arquivo de banco de dados SQLite na raiz do projeto.
- `EMAIL_SENDER`: O endereço de e-mail que será usado como remetente.
- `EMAIL_PASSWORD`: A senha para a conta de e-mail. Para serviços como o Gmail, pode ser necessário gerar uma "Senha de App".
- `SMTP_SERVER`: O endereço do seu servidor SMTP.
- `SMTP_PORT`: A porta do seu servidor SMTP (geralmente 587 para TLS ou 465 para SSL).

## Execução da Aplicação

**1. Aplique as Migrações do Banco de Dados**
Com o ambiente virtual ativado, execute o seguinte comando para criar as tabelas do banco de dados:
```bash
flask db upgrade
```
Este comando aplica a migração mais recente do banco de dados. Você deve executá-lo sempre que houver novas migrações.

**2. Inicie o Servidor de Desenvolvimento**
```bash
python main.py
```
A aplicação estará disponível em `http://127.0.0.1:5000`.

**Aviso**: O servidor de desenvolvimento do Flask não é recomendado para produção. Para implantação em produção, utilize um servidor WSGI robusto como Gunicorn ou uWSGI.

## Melhorias Futuras

- **Otimização de I/O**: A função de envio de e-mails (`send_email_task`) atualmente utiliza a biblioteca síncrona `smtplib`. Para melhorar o desempenho e aproveitar totalmente o `asyncio`, a implementação pode ser migrada para uma biblioteca SMTP assíncrona, como a `aiosmtplib`.
- **Validação de Anexos**: A validação do tipo de anexo atualmente se baseia na extensão do arquivo. Uma abordagem mais segura seria inspecionar os "magic numbers" do arquivo para verificar seu tipo MIME real.
- **Testes Unitários**: Expandir a suíte de testes para cobrir todas as funcionalidades críticas, incluindo o envio de e-mails, manipulação de anexos e as novas rotas de templates.
