let currentLang = localStorage.getItem('replybot_lang') || 'ko';

function getNested(obj, path) {
    return path.split('.').reduce((o, i) => (o ? o[i] : null), obj);
}
const T = (key) => getNested(i18n[currentLang], key);

function changeLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('replybot_lang', lang);
    const t = i18n[lang];
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = getNested(t, key);
        if (val) el.textContent = val;
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const val = getNested(t, key);
        if (val) el.placeholder = val;
    });
    loadStats();
    loadTemplates();
}

async function loadStats() {
    try {
        const data = await API.getStats();

        /* Robust update for Total Templates */
        const totalEl = document.getElementById('totalTemplates');
        if (totalEl) {
            const total = data.total_templates || (data.summary ? data.summary.total : 0);
            totalEl.innerText = total;
        }

        /* Robust update for Server Status */
        const statusEl = document.getElementById('serverStatus');
        if (statusEl) {
            statusEl.innerText = T('stats.stat_ok');
            statusEl.style.color = '#059669';
        }

        /* Robust update for Feedback Rate */
        const fbRateEl = document.getElementById('feedbackRate');
        if (fbRateEl && data.feedback_rate !== undefined) {
            fbRateEl.innerText = data.feedback_rate.toFixed(1) + '%';
        }

    } catch (e) {
        console.error(e);
        const statusEl = document.getElementById('serverStatus');
        if (statusEl) {
            statusEl.innerText = T('stats.stat_error');
            statusEl.style.color = '#dc2626';
        }
    }
}

async function loadTemplates() {
    try {
        const data = await API.getTemplates();
        allTemplates = data.templates;
        const container = document.getElementById('templatesContainer');
        if (container) {
            container.innerHTML = data.templates.map(t => `
            <div class='template-card'>
                <div class='template-title'>[${t.id}] ${t.title}</div>
                <div style='margin-bottom:8px;'><span class='template-tag'>${t.category}</span></div>
                <div style='font-size:0.9rem; color:var(--text-secondary); margin-bottom: 1rem; flex-grow: 1;'>${t.template_text.substring(0, 60)}...</div>
                <button class='view-btn' onclick='UI.openModal("${t.id}")'>
                    <i class='fas fa-eye'></i> <span data-i18n='result.btn_view'>${T('result.btn_view')}</span>
                </button>
            </div>`).join('');
        }
    } catch (e) { console.error(e); }
}

async function findTemplate() {
    const queryEl = document.getElementById('queryInput');
    if (!queryEl) return;

    const query = queryEl.value.trim();
    if (!query) return alert(T('result.empty_query'));

    const resultDiv = document.getElementById('searchResult');
    if (resultDiv) {
        resultDiv.innerHTML = `<div style='text-align:center; padding:2rem;'><i class='fas fa-spinner fa-spin'></i> ${T('stats.stat_checking')}</div>`;
    }

    try {
        const result = await API.findTemplate(query);
        if (result.success && resultDiv) {
            currentLogId = result.log_id;
            const topTemplates = result.top_templates || [result.template];

            // Layout Construction
            let gridHtml = '<div class="results-grid-container fade-in-up">';

            // 1. Top Layer: Rank 1 (Full Width)
            if (topTemplates.length > 0) {
                const tpl1 = topTemplates[0];
                gridHtml += `
                <div class="result-card-new result-card-top group">
                    <div class="flex justify-between items-start" style="display:flex; justify-content:space-between; margin-bottom:1rem;">
                        <h4 class="rank-badge-title">
                            <i class="fas fa-crown" style="color:var(--crown-color);"></i> 
                            <span class="text-gradient-silver">추천 답변 (1순위)</span>
                            <span class="rank-id">ID: ${tpl1.id}</span>
                        </h4>
                        <div class="flex gap-2" style="display:flex; gap:0.5rem;">
                            <button class="btn-copy-sm" onclick="UI.copyText('content-1')">
                                <i class="far fa-copy"></i> 복사
                            </button>
                            <button class="btn-manual-sm" onclick="UI.openFeedbackModal()">
                                <i class="fas fa-edit"></i> 답변선택
                            </button>
                        </div>
                    </div>
                    <div class="result-meta">
                        <span><strong style="color:var(--text-primary);">제목:</strong> ${tpl1.title}</span>
                        <span><strong style="color:var(--text-primary);">카테고리:</strong> <span class="meta-tag">${tpl1.category}</span></span>
                    </div>
                    <pre id="content-1" class="result-content-pre">${tpl1.content || tpl1.template_text}</pre>
                </div>`;
            }

            // 2. Bottom Layer: Rank 2 & 3 (Grid Split)
            if (topTemplates.length > 1) {
                gridHtml += '<div class="results-grid-bottom">';

                // Rank 2
                const tpl2 = topTemplates[1];
                gridHtml += `
                <div class="result-card-new result-card-sub group">
                    <div class="flex justify-between items-start" style="display:flex; justify-content:space-between; margin-bottom:1rem;">
                        <h4 class="rank-badge-title">
                            <span style="background:#ffffff; color:#000000; border:1px solid #000000; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.875rem; font-weight:700;">2</span>
                            <span class="text-gradient-silver">추천 답변 (2순위)</span>
                            <span class="rank-id">ID: ${tpl2.id}</span>
                        </h4>
                        <div class="flex gap-2" style="display:flex; gap:0.5rem;">
                            <button class="btn-copy-sm" onclick="UI.copyText('content-2')">
                                <i class="far fa-copy"></i> 복사
                            </button>
                        </div>
                    </div>
                    <div class="result-meta">
                        <span><strong style="color:var(--text-primary);">제목:</strong> ${tpl2.title}</span>
                        <span><strong style="color:var(--text-primary);">카테고리:</strong> <span class="meta-tag">${tpl2.category}</span></span>
                    </div>
                    <pre id="content-2" class="result-content-pre" style="max-height:300px;">${tpl2.content || tpl2.template_text}</pre>
                </div>`;

                // Rank 3 (if exists)
                if (topTemplates.length > 2) {
                    const tpl3 = topTemplates[2];
                    gridHtml += `
                    <div class="result-card-new result-card-sub group">
                        <div class="flex justify-between items-start" style="display:flex; justify-content:space-between; margin-bottom:1rem;">
                            <h4 class="rank-badge-title">
                                <span style="background:#ffffff; color:#000000; border:1px solid #000000; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.875rem; font-weight:700;">3</span>
                                <span class="text-gradient-silver">추천 답변 (3순위)</span>
                                <span class="rank-id">ID: ${tpl3.id}</span>
                            </h4>
                            <div class="flex gap-2" style="display:flex; gap:0.5rem;">
                                <button class="btn-copy-sm" onclick="UI.copyText('content-3')">
                                    <i class="far fa-copy"></i> 복사
                                </button>
                            </div>
                        </div>
                        <div class="result-meta">
                            <span><strong style="color:var(--text-primary);">제목:</strong> ${tpl3.title}</span>
                            <span><strong style="color:var(--text-primary);">카테고리:</strong> <span class="meta-tag">${tpl3.category}</span></span>
                        </div>
                        <pre id="content-3" class="result-content-pre" style="max-height:300px;">${tpl3.content || tpl3.template_text}</pre>
                    </div>`;
                }

                gridHtml += '</div>'; // End Bottom Layer Grid
            }

            gridHtml += '</div>'; // End Main Container
            resultDiv.innerHTML = gridHtml;
        }
    } catch (e) { if (resultDiv) resultDiv.innerHTML = T('stats.stat_error'); }
}

async function submitFeedback() {
    const categoryEl = document.getElementById('feedbackCategory');
    const contentEl = document.getElementById('feedbackInput');
    if (!categoryEl || !contentEl) return;

    const templateId = categoryEl.value;
    const content = contentEl.value.trim();

    // Get display text for legacy compatibility
    const selectedOption = categoryEl.options[categoryEl.selectedIndex];
    const categoryText = selectedOption ? selectedOption.innerText : '';

    if (!templateId) return alert('카테고리를 선택해주세요.');
    if (!content) return alert('답변 내용을 입력해주세요.');

    try {
        const result = await API.submitFeedback({
            log_id: currentLogId,
            template_id: templateId,
            manual_category: categoryText, // Legacy support
            manual_answer: content
        });
        if (result.success) {
            alert(T('feedback.success_msg') || "저장되었습니다.");
            UI.closeFeedbackModal(null);
        } else {
            alert((T('feedback.error_msg') || "오류가 발생했습니다.") + (result.error ? '\n' + result.error : ''));
        }
    } catch (e) { console.error(e); }
}

/* Feedback Limit */
let MAX_FEEDBACK_LENGTH = 500;
function initFeedbackSettings() {
    if (typeof SERVER_CONFIG !== 'undefined' && SERVER_CONFIG.feedback && SERVER_CONFIG.feedback.max_length) {
        MAX_FEEDBACK_LENGTH = SERVER_CONFIG.feedback.max_length;
    }
    const maxCharEl = document.getElementById('maxCharCount');
    if (maxCharEl) maxCharEl.innerText = MAX_FEEDBACK_LENGTH;
}
function checkFeedbackLength(el) {
    let val = el.value;
    if (val.length > MAX_FEEDBACK_LENGTH) {
        val = val.substring(0, MAX_FEEDBACK_LENGTH);
        el.value = val;
    }
    const countEl = document.getElementById('charCount');
    if (countEl) countEl.innerText = val.length;
}

function checkQueryLength(el) {
    const maxLength = 300;
    let val = el.value;
    if (val.length > maxLength) {
        val = val.substring(0, maxLength);
        el.value = val;
    }
    const countEl = document.getElementById('queryCharCount');
    if (countEl) countEl.innerText = `${val.length} / ${maxLength}`;
}

window.onload = function () {
    changeLanguage(currentLang);
    initFeedbackSettings();
};
