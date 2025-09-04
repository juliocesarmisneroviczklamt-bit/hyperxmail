from flask import render_template_string
from flask_wtf.csrf import generate_csrf

def get_index_template(api_token):
    """
    Gera o template HTML para a interface web.

    Args:
        api_token (str): Token de API para autenticação.

    Returns:
        str: HTML renderizado.
    """
    html_template = r"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Futuristic Email Sender</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Orbitron', sans-serif; background: linear-gradient(135deg, #0d0d1a 0%, #1a1a2e 100%); display: flex; justify-content: center; align-items: center; min-height: 100vh; overflow: hidden; position: relative; color: #fff; }
            #particles-js { position: absolute; width: 100%; height: 100%; z-index: -1; }
            .container { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 15px; padding: 30px; width: 90%; max-width: 450px; box-shadow: 0 0 20px rgba(0, 255, 255, 0.2); animation: fadeIn 1s ease-out; position: relative; z-index: 1; }
            @keyframes fadeIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
            h1 { color: #00ffcc; text-align: center; font-size: clamp(20px, 5vw, 24px); text-transform: uppercase; letter-spacing: 2px; margin-bottom: 25px; text-shadow: 0 0 10px rgba(0, 255, 204, 0.7); animation: glow 2s infinite alternate; }
            @keyframes glow { from { text-shadow: 0 0 5px rgba(0, 255, 204, 0.7); } to { text-shadow: 0 0 15px rgba(0, 255, 204, 1); } }
            input, textarea { width: 100%; padding: 12px; margin: 10px 0; background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(0, 255, 255, 0.5); border-radius: 8px; color: #fff; font-size: 16px; outline: none; transition: all 0.3s ease; }
            input:focus, textarea:focus { border-color: #00ffcc; box-shadow: 0 0 12px rgba(0, 255, 204, 0.8); }
            input:invalid:focus, textarea:invalid:focus { border-color: #ff3366; box-shadow: 0 0 12px rgba(255, 51, 102, 0.8); }
            textarea { height: 100px; resize: none; }
            button { width: 100%; padding: 12px; background: linear-gradient(45deg, #00ffcc, #007bff); border: none; border-radius: 8px; color: #fff; font-size: 16px; text-transform: uppercase; letter-spacing: 1px; cursor: pointer; transition: all 0.3s ease; margin-top: 10px; }
            button:disabled { background: #666; cursor: not-allowed; opacity: 0.7; }
            button:hover:not(:disabled) { box-shadow: 0 0 20px rgba(0, 255, 255, 0.9); transform: scale(1.05); }
            #attach-button { background: linear-gradient(45deg, #ff3366, #ff6699); }
            #progress-bar { width: 0; height: 5px; background: #00ffcc; border-radius: 5px; margin-top: 10px; transition: width 0.3s ease; }
            #status { text-align: center; margin-top: 15px; font-size: 14px; text-shadow: 0 0 5px rgba(0, 255, 204, 0.5); transition: opacity 0.3s ease; opacity: 0; }
            #status.active { opacity: 1; }
            #email-tags { display: flex; flex-wrap: wrap; gap: 5px; padding: 5px; background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(0, 255, 255, 0.5); border-radius: 8px; margin: 10px 0; }
            .tag { display: flex; align-items: center; background: rgba(0, 255, 255, 0.3); padding: 5px 10px; border-radius: 5px; color: #fff; font-size: 14px; }
            .tag.invalid { background: rgba(255, 51, 102, 0.3); border: 1px solid #ff3366; }
            .tag button { background: none; border: none; color: #fff; font-size: 12px; margin-left: 5px; cursor: pointer; }
            #to-input { border: none; background: none; color: #fff; flex-grow: 1; min-width: 100px; }
            #log-area { margin-top: 20px; max-height: 150px; overflow-y: auto; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 8px; padding: 10px; font-size: 12px; }
            .log-success { color: #00ffcc; }
            .log-error { color: #ff3366; }
            #attachment-input { display: none; }
            .template-bar { display: flex; gap: 10px; margin-bottom: 10px; }
            .template-bar select { flex-grow: 1; background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(0, 255, 255, 0.5); border-radius: 8px; color: #fff; padding: 12px; font-size: 16px; outline: none; }
            .template-bar select option { background: #1a1a2e; color: #fff; }
            .template-bar button { width: auto; padding: 0 20px; font-size: 14px; background: linear-gradient(45deg, #8a2be2, #4b0082); }
            @media (max-width: 480px) { .container { padding: 20px; } input, textarea, button { font-size: 14px; } .template-bar { flex-direction: column; } }
        </style>
        <script src="https://cdn.tiny.cloud/1/no-api-key/tinymce/8/tinymce.min.js" referrerpolicy="origin"></script>
        <script>
            tinymce.init({
                selector: 'textarea#message',
                plugins: 'code table lists image link',
                toolbar: 'undo redo | blocks | bold italic | alignleft aligncenter alignright | indent outdent | bullist numlist | code | table | image | link'
            });
        </script>
    </head>
    <body>
        <div id="particles-js"></div>
        <div class="container">
            <h1>EMAIL TRANSMISSOR</h1>
            <form id="emailForm">
                <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                <div id="email-tags" aria-label="Destinatários">
                    <input type="text" id="to-input" placeholder="Digite o(s) destinatário(s) e pressione Enter (opcional)" aria-label="Adicionar destinatário">
                </div>
                <input type="text" id="subject" placeholder="Assunto" required aria-label="Assunto">
                <input type="text" id="cc" placeholder="CC (separe por vírgulas)" aria-label="Cópia Carbono">
                <input type="text" id="cco" placeholder="CCO (separe por vírgulas)" aria-label="Cópia Oculta">
                <div class="template-bar">
                    <select id="template-select" aria-label="Selecionar Template">
                        <option value="">Carregar um Template</option>
                    </select>
                    <button type="button" id="save-template-button">SALVAR TEMPLATE</button>
                </div>
                <textarea id="message" placeholder="Transmissão (use <img> para imagens. Imagens anexadas podem conter hyperlinks)" required minlength="5" aria-label="Mensagem"></textarea>
                <input type="file" id="csv-input" accept=".csv" aria-label="Escolher CSV com e-mails (opcional)">
                <input type="file" id="attachment-input" multiple accept=".jpg,.jpeg,.png,.pdf" aria-label="Escolher anexos">
                <button type="button" id="attach-button">ANEXAR IMAGEM COM/SEM LINK</button>
                <button type="button" id="preview-button" style="background: linear-gradient(45deg, #ff9a28, #ffcd3c);">PRÉ-VISUALIZAR</button>
                <button type="submit">ENVIAR SINAL</button>
                <div id="progress-bar"></div>
            </form>
            <p id="status"></p>
            <div id="log-area"></div>
        </div>

        <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
        <script>
            particlesJS('particles-js', {
                particles: { number: { value: 80, density: { enable: true, value_area: 800 } }, color: { value: '#00ffcc' }, shape: { type: 'circle' }, opacity: { value: 0.7, random: true }, size: { value: 3, random: true }, move: { enable: true, speed: 2, direction: 'none', random: true } },
                interactivity: { detect_on: 'canvas', events: { onhover: { enable: true, mode: 'repulse' }, onclick: { enable: true, mode: 'push' } }, modes: { repulse: { distance: 150 }, push: { particles_nb: 6 } } }
            });

            const emailTags = document.getElementById('email-tags');
            const toInput = document.getElementById('to-input');
            const emailRegex = /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/;
            let emails = [];
            let attachmentCount = 0;
            let selectedCsvContent = '';
            const API_TOKEN = '{{ api_token }}';

            function addTag(email) {
                if (email && !emails.includes(email)) {
                    const isValid = emailRegex.test(email);
                    const tag = document.createElement('div');
                    tag.className = `tag ${isValid ? '' : 'invalid'}`;
                    tag.innerHTML = `${email} <button type="button" aria-label="Remover">x</button>`;
                    tag.querySelector('button').onclick = () => {
                        emails = emails.filter(e => e !== email);
                        tag.remove();
                        log(`Destinatário removido: ${email}`);
                    };
                    emailTags.insertBefore(tag, toInput);
                    emails.push(email);
                    log(`Destinatário adicionado: ${email} ${isValid ? '(válido)' : '(inválido)'}`);
                }
                toInput.value = '';
            }

            toInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === 'Tab') {
                    e.preventDefault();
                    addTag(toInput.value.trim());
                }
            });

            const form = document.getElementById('emailForm');
            const status = document.getElementById('status');
            const button = form.querySelector('button[type="submit"]');
            const attachButton = document.getElementById('attach-button');
            const csvInput = document.getElementById('csv-input');
            const attachmentInput = document.getElementById('attachment-input');
            const progressBar = document.getElementById('progress-bar');
            const logArea = document.getElementById('log-area');
            const previewButton = document.getElementById('preview-button');

            previewButton.addEventListener('click', () => {
                const content = tinymce.get('message').getContent();
                if (content) {
                    const previewWindow = window.open('', '_blank');
                    previewWindow.document.write(content);
                    previewWindow.document.close();
                    log("Pré-visualização gerada em nova aba.");
                } else {
                    showStatus("Nada para pré-visualizar.", false);
                    log("Tentativa de pré-visualizar com conteúdo vazio.", 'error');
                }
            });

            const saveTemplateButton = document.getElementById('save-template-button');
            const templateSelect = document.getElementById('template-select');
            let templates = [];

            async function loadTemplates() {
                try {
                    const response = await fetch('/templates');
                    if (!response.ok) throw new Error('Falha ao carregar templates');
                    templates = await response.json();

                    templateSelect.innerHTML = '<option value="">Carregar um Template</option>';
                    templates.forEach(template => {
                        const option = document.createElement('option');
                        option.value = template.id;
                        option.textContent = template.name;
                        templateSelect.appendChild(option);
                    });
                    log("Templates carregados com sucesso.");
                } catch (error) {
                    showStatus(error.message, false);
                    log(error.message, 'error');
                }
            }

            saveTemplateButton.addEventListener('click', async () => {
                const name = prompt("Digite o nome para este template:");
                if (!name || !name.trim()) {
                    showStatus("Nome do template inválido.", false);
                    return;
                }

                const content = tinymce.get('message').getContent();
                if (!content) {
                    showStatus("Não há conteúdo para salvar como template.", false);
                    return;
                }

                try {
                    const response = await fetch('/templates', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': document.querySelector('input[name="csrf_token"]').value
                        },
                        body: JSON.stringify({ name: name.trim(), content: content })
                    });

                    const result = await response.json();
                    if (response.ok) {
                        showStatus(result.message, true);
                        log(result.message, 'success');
                        loadTemplates(); // Recarrega a lista de templates
                    } else {
                        throw new Error(result.message || 'Erro desconhecido ao salvar template.');
                    }
                } catch (error) {
                    showStatus(error.message, false);
                    log(error.message, 'error');
                }
            });

            templateSelect.addEventListener('change', () => {
                const selectedId = templateSelect.value;
                if (selectedId) {
                    const selectedTemplate = templates.find(t => t.id === selectedId);
                    if (selectedTemplate) {
                        tinymce.get('message').setContent(selectedTemplate.content);
                        log(`Template "${selectedTemplate.name}" carregado.`);
                    }
                }
            });

            document.addEventListener('DOMContentLoaded', loadTemplates);

            function log(message, type = 'info') {
                const log = document.createElement('div');
                log.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                log.className = type === 'success' ? 'log-success' : type === 'error' ? 'log-error' : '';
                logArea.appendChild(log);
                logArea.scrollTop = logArea.scrollHeight;
            }

            function showStatus(message, success) {
                status.textContent = message;
                status.classList.add('active');
                status.style.color = success ? '#00ffcc' : '#ff3366';
                setTimeout(() => status.classList.remove('active'), 5000);
            }

            function checkFileSize(input) {
                const maxSize = 10 * 1024 * 1024;
                for (let file of input.files) {
                    if (file.size > maxSize) {
                        showStatus(`Erro: O arquivo ${file.name} excede o limite de 10MB.`, false);
                        log(`Arquivo ${file.name} excede o limite de tamanho.`, 'error');
                        input.value = '';
                        return false;
                    }
                }
                return true;
            }

            async function compressAndConvertFile(file) {
                const img = new Image();
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                const maxWidth = 800;

                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        img.src = e.target.result;
                        img.onload = () => {
                            const ratio = Math.min(maxWidth / img.width, 1);
                            canvas.width = img.width * ratio;
                            canvas.height = img.height * ratio;
                            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                            resolve(canvas.toDataURL('image/jpeg', 0.8).split(',')[1]);
                        };
                    };
                    reader.readAsDataURL(file);
                });
            }

            async function prepareAttachment(file) {
                if (file.name.toLowerCase().endsWith('.pdf')) {
                    return new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onload = (e) => resolve(e.target.result.split(',')[1]);
                        reader.readAsDataURL(file);
                    });
                } else {
                    return compressAndConvertFile(file);
                }
            }

            attachButton.addEventListener('click', () => attachmentInput.click());

            attachmentInput.addEventListener('change', () => {
                const files = attachmentInput.files;
                if (files.length === 0) {
                    showStatus("Nenhum anexo selecionado.", false);
                    log("Nenhum anexo selecionado.", 'error');
                    return;
                }
                if (checkFileSize(attachmentInput)) {
                    const messageArea = document.getElementById('message');
                    let currentText = messageArea.value;
                    for (let i = 0; i < files.length; i++) {
                        const file = files[i];
                        if (file.name.toLowerCase().endsWith('.pdf')) {
                            currentText += `\nAnexo: ${file.name}\n`;
                        } else {
                            const cid = `image${attachmentCount + i}`;
                            const url = prompt("Digite a URL para o hyperlink da imagem (deixe em branco para não adicionar link):");
                            if (url && url.trim() !== "") {
                                currentText += `<a href="${url.trim()}" target="_blank"><img src="cid:${cid}" alt="${file.name}"></a>`;
                                log(`Imagem anexada com link para: ${url.trim()}`, 'success');
                            } else {
                                currentText += `<img src="cid:${cid}" alt="${file.name}">`;
                            }
                        }
                    }
                    messageArea.value = currentText;
                    attachmentCount += files.length;
                    log(`Adicionados ${files.length} anexo(s) ao texto.`, 'success');
                }
            });

            csvInput.addEventListener('change', () => {
                if (csvInput.files.length > 0) {
                    const file = csvInput.files[0];
                    const reader = new FileReader();
                    reader.onload = function(event) {
                        selectedCsvContent = event.target.result;
                        log(`CSV selecionado: ${file.name}`, 'success');
                    };
                    reader.readAsText(file);
                } else {
                    selectedCsvContent = '';
                }
            });

            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                tinymce.triggerSave(); // Salva o conteúdo do editor no textarea
                log("Iniciando processo de envio...");

                const subject = document.getElementById('subject').value.trim();
                const cc = document.getElementById('cc').value.trim();
                const cco = document.getElementById('cco').value.trim();
                const message = document.getElementById('message').value.trim();
                const attachmentFiles = attachmentInput.files;
                const csrfToken = document.querySelector('input[name="csrf_token"]').value;

                if (!subject) {
                    showStatus("Erro: Assunto é obrigatório.", false);
                    log("Assunto não preenchido.", 'error');
                    return;
                }
                if (cc && !cc.split(',').every(email => emailRegex.test(email.trim()))) {
                    showStatus("Erro: CC inválido.", false);
                    log("CC inválido.", 'error');
                    return;
                }
                if (cco && !cco.split(',').every(email => emailRegex.test(email.trim()))) {
                    showStatus("Erro: CCO inválido.", false);
                    log("CCO inválido.", 'error');
                    return;
                }
                if (message.length < 5) {
                    showStatus("Erro: Mensagem muito curta.", false);
                    log("Mensagem muito curta.", 'error');
                    return;
                }
                if (!selectedCsvContent && emails.length === 0) {
                    showStatus("Erro: Nenhum destinatário ou CSV fornecido.", false);
                    log("Nenhum destinatário ou CSV fornecido.", 'error');
                    return;
                }

                const attachments = [];
                if (attachmentFiles.length > 0 && checkFileSize(attachmentInput)) {
                    log(`Preparando ${attachmentFiles.length} anexo(s)...`);
                    progressBar.style.width = '0%';
                    const filePromises = Array.from(attachmentFiles).map(async (file, index) => {
                        const base64Data = await prepareAttachment(file);
                        progressBar.style.width = `${((index + 1) / attachmentFiles.length) * 100}%`;
                        log(`Arquivo ${file.name} preparado.`);
                        return { name: file.name, data: base64Data };
                    });
                    attachments.push(...await Promise.all(filePromises));
                }

                button.disabled = true;
                button.textContent = "Transmitindo...";
                showStatus("", true);

                const payload = { 
                    subject: subject, 
                    cc: cc, 
                    bcc: cco, 
                    message: message, 
                    attachments: attachments, 
                    csvContent: selectedCsvContent,
                    manualEmails: emails 
                };

                try {
                    log(`Token usado: ${API_TOKEN}`);
                    log("Enviando ao servidor...");
                    const response = await fetch('/send_email', {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            'Authorization': API_TOKEN,
                            'X-CSRF-Token': csrfToken
                        },
                        body: JSON.stringify(payload)
                    });
                    const result = await response.json();

                    if (response.ok) {
                        showStatus(result.message, true);
                        log(`Sucesso: ${result.message}`, 'success');
                    } else {
                        showStatus(result.message || 'Erro desconhecido no servidor.', false);
                        log(`Erro: ${result.message || 'Resposta inválida do servidor.'}`, 'error');
                    }
                } catch (error) {
                    showStatus(`Erro na conexão: ${error.message}`, false);
                    log(`Erro na conexão: ${error.message}`, 'error');
                }

                button.disabled = false;
                button.textContent = "ENVIAR SINAL";
                progressBar.style.width = '0%';
                log("Processo concluído.");
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, api_token=api_token, csrf_token=generate_csrf())