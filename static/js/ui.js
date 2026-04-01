const UI = {
    showToast() {
        const toast = document.getElementById('toast');
        toast.className = 'show';
        setTimeout(() => { toast.className = toast.className.replace('show', ''); }, 3000);
    },
    copyText(elementId) {
        const text = document.getElementById(elementId).innerText;
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(UI.showToast);
        } else {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-9999px';
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                UI.showToast();
            } catch (err) {
                alert('복사 실패. 수동으로 복사해주세요.');
            }
            document.body.removeChild(textArea);
        }
    },
    openModal(templateId) {
        const template = allTemplates.find(t => t.id == templateId);
        if (!template) return;
        document.getElementById('modalTitle').innerText = `[${template.id}] ${template.title || template.category}`;
        document.getElementById('modalCategory').innerText = template.category;
        document.getElementById('modalBody').innerText = template.full_content || template.template_text;
        const overlay = document.getElementById('modalOverlay');
        overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    },
    closeModal(event) {
        if (event && event.target !== event.currentTarget) return;
        const overlay = document.getElementById('modalOverlay');
        overlay.classList.remove('open');
        document.body.style.overflow = '';
    },
    onCategoryChange(el) {
        const id = el.value;
        const inputEl = document.getElementById('feedbackInput');

        if (!id) {
            if (inputEl) {
                inputEl.value = '';
                inputEl.readOnly = false;
                const countEl = document.getElementById('charCount');
                if (countEl) countEl.innerText = '0';
            }
            return;
        }

        const template = (window.allTemplates || []).find(t => String(t.id) === String(id));
        if (template) {
            const content = template.full_content || template.template_text;
            if (inputEl) {
                inputEl.value = content;
                inputEl.readOnly = true;
                const countEl = document.getElementById('charCount');
                if (countEl) countEl.innerText = content.length;
            }
        }
    },
    openFeedbackModal() {
        if (!currentLogId) {
            // Check if T is defined, otherwise fallback string
            const msg = (typeof T === 'function') ? T('result.error_default') : 'Error';
            alert(msg);
            return;
        }

        // Populate Select
        const select = document.getElementById('feedbackCategory');
        if (select) {
            const placeholder = (typeof T === 'function') ? T('feedback.modal_placeholder_category') : 'Category...';
            select.innerHTML = `<option value="">${placeholder}</option>`; // Reset
            if (window.allTemplates) {
                // Sort by ID to be neat
                const sorted = [...window.allTemplates].sort((a, b) => Number(a.id) - Number(b.id));
                sorted.forEach(t => {
                    const opt = document.createElement('option');
                    opt.value = t.id;
                    opt.innerText = `[${t.id}] ${t.category}`;
                    select.appendChild(opt);
                });
            }
        }

        const inputEl = document.getElementById('feedbackInput');
        if (inputEl) {
            inputEl.value = '';
            inputEl.readOnly = false;
        }

        const countEl = document.getElementById('charCount');
        if (countEl) countEl.innerText = '0';

        const overlay = document.getElementById('feedbackModalOverlay');
        overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
        setTimeout(() => { if (select) select.focus(); }, 100);
    },
    closeFeedbackModal(event) {
        if (event && event.target !== event.currentTarget) return;
        const overlay = document.getElementById('feedbackModalOverlay');
        overlay.classList.remove('open');
        document.body.style.overflow = '';
    }
};