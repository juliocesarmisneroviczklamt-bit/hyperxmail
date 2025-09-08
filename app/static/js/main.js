document.addEventListener('DOMContentLoaded', () => {
    tinymce.init({
        selector: 'textarea#message',
        plugins: 'code table lists image link',
        toolbar: 'undo redo | blocks | bold italic | alignleft aligncenter alignright | indent outdent | bullist numlist | code | table | image | link'
    });

    particlesJS('particles-js', {
        "particles": {
            "number": { "value": 60, "density": { "enable": true, "value_area": 800 } },
            "color": { "value": "#3498db" },
            "shape": { "type": "circle" },
            "opacity": { "value": 0.5, "random": true },
            "size": { "value": 3, "random": true },
            "line_linked": { "enable": false },
            "move": { "enable": true, "speed": 2, "direction": "none", "random": true, "straight": false, "out_mode": "out" }
        },
        "interactivity": {
            "detect_on": "canvas",
            "events": { "onhover": { "enable": true, "mode": "repulse" }, "onclick": { "enable": true, "mode": "push" } },
            "modes": { "repulse": { "distance": 100, "duration": 0.4 }, "push": { "particles_nb": 4 } }
        },
        "retina_detect": true
    });

    feather.replace();

    const emailRegex = /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/i;

    function validateEmailList(input) {
        const emails = input.value.split(',').map(e => e.trim()).filter(e => e);
        if (emails.length === 0) {
            input.classList.remove('valid', 'invalid');
            return;
        }

        const allValid = emails.every(email => emailRegex.test(email));

        if (allValid) {
            input.classList.add('valid');
            input.classList.remove('invalid');
        } else {
            input.classList.add('invalid');
            input.classList.remove('valid');
        }
    }

    const toInput = document.getElementById('to-input');
    const emailTags = document.getElementById('email-tags');
    let emails = [];
    let attachmentCount = 0;
    let selectedCsvContent = '';

    function addTag(email) {
        if (email && !emails.includes(email)) {
            const isValid = emailRegex.test(email);
            const tag = document.createElement('div');
            tag.className = `tag ${isValid ? '' : 'invalid'}`;
            tag.innerHTML = `${email} <button type="button" aria-label="Remover"><i data-feather="x"></i></button>`;
            tag.querySelector('button').onclick = () => {
                emails = emails.filter(e => e !== email);
                tag.remove();
                log(`Destinatário removido: ${email}`);
            };
            emailTags.insertBefore(tag, toInput);
            feather.replace();
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
    const csvInput = document.getElementById('csv-input');
    const ccInput = document.getElementById('cc');
    const ccoInput = document.getElementById('cco');
    const attachmentInput = document.getElementById('attachment-input');
    const progressBar = document.getElementById('progress-bar');
    const logArea = document.getElementById('log-area');
    const previewButton = document.getElementById('preview-button');

    ccInput.addEventListener('input', () => validateEmailList(ccInput));
    ccoInput.addEventListener('input', () => validateEmailList(ccoInput));

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
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
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

    loadTemplates();

    const socket = io();

    socket.on('connect', () => {
        log('Conectado ao servidor de progresso.');
    });

    socket.on('progress', (data) => {
        const percent = (data.sent / data.total) * 100;
        progressBar.style.width = percent + '%';
        log(`Email enviado para ${data.email} (${data.sent}/${data.total})`, 'success');
    });

    socket.on('task_error', (data) => {
        showStatus(`Erro no envio: ${data.message}`, false);
        log(`Erro no envio: ${data.message}`, 'error');
        button.disabled = false;
        button.textContent = "ENVIAR SINAL";
    });

    socket.on('disconnect', () => {
        log('Desconectado do servidor de progresso.');
    });

    function log(message, type = 'info') {
        const log = document.createElement('div');
        log.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        log.className = type === 'success' ? 'log-success' : type === 'error' ? 'log-error' : '';
        logArea.appendChild(log);
        logArea.scrollTop = logArea.scrollHeight;
    }

    function showStatus(message, success) {
        status.textContent = message;
        status.style.color = success ? 'var(--success)' : 'var(--error)';
        status.classList.add('active');
        status.addEventListener('animationend', () => {
            status.classList.remove('active');
        }, { once: true });
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

    csvInput.addEventListener('change', () => {
        const label = document.getElementById('csv-label');
        if (csvInput.files.length > 0) {
            label.textContent = `CSV: ${csvInput.files[0].name}`;
            const file = csvInput.files[0];
            const reader = new FileReader();
            reader.onload = function(event) {
                selectedCsvContent = event.target.result;
                log(`CSV selecionado: ${file.name}`, 'success');
            };
            reader.readAsText(file);
        } else {
            label.textContent = 'Select CSV with emails (optional)';
            selectedCsvContent = '';
        }
    });

    attachmentInput.addEventListener('change', () => {
        const label = document.getElementById('attachment-label');
        const files = attachmentInput.files;
        if (files.length > 0) {
            label.textContent = `${files.length} file(s) selected`;
        } else {
            label.textContent = 'Attach Files (PDF, JPG, PNG)';
        }

        if (files.length === 0) {
            showStatus("Nenhum anexo selecionado.", false);
            log("Nenhum anexo selecionado.", 'error');
            return;
        }
        if (checkFileSize(attachmentInput)) {
            const messageArea = tinymce.get('message');
            let currentContent = messageArea.getContent();
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                if (file.name.toLowerCase().endsWith('.pdf')) {
                    currentContent += `<p>Anexo: ${file.name}</p>`;
                } else {
                    const cid = `image${attachmentCount + i}`;
                    const url = prompt("Digite a URL para o hyperlink da imagem (deixe em branco para não adicionar link):");
                    if (url && url.trim() !== "") {
                        currentContent += `<p><a href="${url.trim()}" target="_blank"><img src="cid:${cid}" alt="${file.name}"></a></p>`;
                        log(`Imagem anexada com link para: ${url.trim()}`, 'success');
                    } else {
                        currentContent += `<p><img src="cid:${cid}" alt="${file.name}"></p>`;
                    }
                }
            }
            messageArea.setContent(currentContent);
            attachmentCount += files.length;
            log(`Adicionados ${files.length} anexo(s) ao texto.`, 'success');
        }
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        tinymce.triggerSave();
        log("Iniciando processo de envio...");

        const subject = document.getElementById('subject').value.trim();
        const cc = document.getElementById('cc').value.trim();
        const cco = document.getElementById('cco').value.trim();
        const message = document.getElementById('message').value.trim();
        const attachmentFiles = document.getElementById('attachment-input').files;
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

        button.disabled = true;
        button.textContent = "Transmitindo...";
        progressBar.style.width = '0%';
        showStatus("", true);

        const attachments = [];
        if (attachmentFiles.length > 0 && checkFileSize(attachmentInput)) {
            log(`Preparando ${attachmentFiles.length} anexo(s)...`);
            const filePromises = Array.from(attachmentFiles).map(async (file, index) => {
                const base64Data = await prepareAttachment(file);
                progressBar.style.width = `${((index + 1) / attachmentFiles.length) * 50}%`; // Halfway for preparation
                log(`Arquivo ${file.name} preparado.`);
                return { name: file.name, data: base64Data };
            });
            attachments.push(...await Promise.all(filePromises));
        }

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
            log("Enviando ao servidor...");
            const response = await fetch('/send_email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // LINHA CORRIGIDA ABAIXO
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (response.ok) {
                showStatus(result.message, true);
                log(`Sucesso: ${result.message}`, 'success');
            } else {
                throw new Error(result.message || 'Erro desconhecido no servidor.');
            }
        } catch (error) {
            showStatus(`Erro: ${error.message}`, false);
            log(`Erro na conexão: ${error.message}`, 'error');
        } finally {
            button.disabled = false;
            button.textContent = "ENVIAR BROADCAST"; // Revertido para o texto original do botão
            progressBar.style.width = '0%';
            log("Processo concluído.");
        }
    });
});
