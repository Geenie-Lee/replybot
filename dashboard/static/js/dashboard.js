let currentPage = 1;
let pageSize = 10;
let currentLang = localStorage.getItem('dashboard_lang') || 'ko';

const rawMessages = (window.dashboardConfig && window.dashboardConfig.messages) || {};
const translations = {
    ko: (rawMessages.ko && rawMessages.ko.dashboard) || {},
    en: (rawMessages.en && rawMessages.en.dashboard) || {}
};

const SIDEBAR_STATE_KEY = 'sidebar_collapsed';

document.addEventListener('DOMContentLoaded', async function () {
    const langSelect = document.getElementById('langSelect');
    if (langSelect) langSelect.value = currentLang;

    // --- Sidebar Persistence Logic ---
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const storedState = localStorage.getItem(SIDEBAR_STATE_KEY);
    // Default to collapsed (true) if not set, otherwise parse boolean
    const isCollapsed = storedState === null ? true : storedState === 'true';

    // Apply initial state
    if (sidebar) {
        if (isCollapsed) {
            sidebar.classList.add('collapsed');
            if (sidebarToggle) {
                sidebarToggle.classList.remove('fa-chevron-left');
                sidebarToggle.classList.add('fa-chevron-right');
            }
        } else {
            sidebar.classList.remove('collapsed');
            if (sidebarToggle) {
                sidebarToggle.classList.remove('fa-chevron-right');
                sidebarToggle.classList.add('fa-chevron-left');
            }
        }

        // Remove the hardcoded transition:none inline style applied to HTML tags
        // to restore normal smooth CSS animation functionality for subsequent toggles.
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                sidebar.style.transition = '';
            });
        });
    }

    // Default Date Filter Removed
    // const startDateEl = document.getElementById('filterStartDate');
    // const endDateEl = document.getElementById('filterEndDate');

    // if (startDateEl) startDateEl.value = formatDate(yesterday);
    // if (endDateEl) endDateEl.value = formatDate(today);

    // Only initialize Dashboard-specific logic if we are on the dashboard page
    if (document.getElementById('trendChart')) {
        changeLanguage(currentLang);
        loadDashboardStats();

        // Load templates first to ensure IDs are mapped to Categories
        await loadFullTemplates();
        loadFilters();
        loadLogs(currentPage);
    } else {
        // For other pages (like users.html) that share dashboard.js
        // We might need to initialize translations if they use client-side i18n from this file
        // But users.html seems to use server-side. 
        // We can optionally run changeLanguage if needed, but safe to skip for now to stop errors.
        if (typeof window.toggleAccordion === 'undefined') {
            // ensure global functions are set if not already?
        }
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            const isNowCollapsed = sidebar.classList.toggle('collapsed');

            // Save state
            localStorage.setItem(SIDEBAR_STATE_KEY, isNowCollapsed);

            // Update icon
            if (isNowCollapsed) {
                this.classList.remove('fa-chevron-left');
                this.classList.add('fa-chevron-right');
            } else {
                this.classList.remove('fa-chevron-right');
                this.classList.add('fa-chevron-left');
            }

            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 300);
        });
    }

    // Event listener for template select
    const templateSelect = document.getElementById('manualTemplateSelect');
    if (templateSelect) {
        templateSelect.addEventListener('change', function () {
            const selectedId = this.value;
            const contentDiv = document.getElementById('templateContentPreview');
            const answerInput = document.getElementById('manualAnswerInput');

            if (selectedId && window.allTemplates) {
                const tmpl = window.allTemplates.find(t => String(t.id) === String(selectedId));
                if (tmpl) {
                    contentDiv.textContent = tmpl.answer;
                    // Pre-fill the editable textarea
                    answerInput.value = tmpl.answer;
                } else {
                    contentDiv.textContent = '';
                    answerInput.value = '';
                }
            } else {
                contentDiv.textContent = '';
                // answerInput.value = ''; // Don't clear if they just deselected? Or yes? 
                // Usually selecting "Select Category..." means clear.
                answerInput.value = '';
            }
        });
    }
});

// --- Sidebar Accordion Logic ---
window.toggleAccordion = function (btn) {
    // Auto-expand sidebar if collapsed
    const sidebar = document.querySelector('.sidebar');
    if (sidebar.classList.contains('collapsed')) {
        sidebar.classList.remove('collapsed');
        const toggle = document.getElementById('sidebarToggle');
        if (toggle) {
            toggle.classList.remove('fa-chevron-right');
            toggle.classList.add('fa-chevron-left');
        }
    }

    const content = btn.nextElementSibling;
    const icon = btn.querySelector('.fa-chevron-right, .fa-chevron-down');

    if (content.classList.contains('open')) {
        content.classList.remove('open');
        if (icon) {
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-right');
        }
        btn.classList.remove('active');
    } else {
        // Close other open accordions if we want auto-collapse (optional, usually good UX)
        // document.querySelectorAll('.accordion-content.open').forEach(el => {
        //     if(el !== content) {
        //        el.classList.remove('open');
        //        el.previousElementSibling.classList.remove('active');
        //     }
        // });

        // Remove active state from other main menu items (like Dashboard)
        document.querySelectorAll('.nav-menu > a.active').forEach(a => a.classList.remove('active'));

        content.classList.add('open');
        if (icon) {
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-down');
        }
        btn.classList.add('active');
    }
};

let currentLogIdForFeedback = null;
window.allTemplates = [];

async function loadFullTemplates() {
    try {
        const response = await fetch('/dashboard/api/templates');
        const data = await response.json();
        if (data.success) {
            window.allTemplates = data.templates;
        }
    } catch (e) {
        console.error("Failed to load templates", e);
    }
}

function openManualModal(logId) {
    currentLogIdForFeedback = logId;
    const modal = document.getElementById('manualFeedbackModal');
    const select = document.getElementById('manualTemplateSelect');
    const answerInput = document.getElementById('manualAnswerInput');
    const preview = document.getElementById('templateContentPreview');

    // Reset
    select.innerHTML = '<option value="">Select Category...</option>';
    answerInput.value = '';
    preview.textContent = '';

    // Populate Select
    if (window.allTemplates) {
        window.allTemplates.forEach(t => {
            const option = document.createElement('option');
            option.value = t.id;
            // Show Category (and maybe ID)
            option.textContent = `[${t.id}] ${t.category}`;
            select.appendChild(option);
        });
    }

    modal.style.display = 'flex';
}

function closeManualModal() {
    document.getElementById('manualFeedbackModal').style.display = 'none';
    currentLogIdForFeedback = null;
}

async function submitManualFeedback() {
    if (!currentLogIdForFeedback) return;

    const templateId = document.getElementById('manualTemplateSelect').value;
    const manualAnswer = document.getElementById('manualAnswerInput').value;

    if (!templateId) {
        alert("Please select a category (template).");
        return;
    }

    if (!manualAnswer.trim()) {
        alert("Please enter an answer.");
        return;
    }

    const userId = (window.dashboardConfig && window.dashboardConfig.currentUser) || 'unknown';

    try {
        const response = await fetch('/dashboard/api/save_feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                log_id: currentLogIdForFeedback,
                template_id: templateId,
                manual_answer: manualAnswer,
                user_id: userId
            })
        });
        const result = await response.json();
        if (result.success) {
            alert("Saved successfully!");
            closeManualModal();
            loadLogs(currentPage); // Reload logs
        } else {
            alert("Failed to save: " + (result.error || 'Unknown error'));
        }
    } catch (e) {
        console.error(e);
        alert("Error saving feedback.");
    }
}

function changeLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('dashboard_lang', lang);

    // Update data-i18n elements
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) {
            el.textContent = translations[lang][key];
        }
    });

    updateDate();

    // Re-render components if data exists
    // Note: We might need to store last fetched data to re-render without fetching, 
    // but for simplicity, we rely on the fact that charts/tables will be updated on next fetch or we can trigger re-render if needed.
    // However, chart instances need to be destroyed to update labels basically.
    // For now, let's just update pagination text if it exists.
    const pageInfo = document.getElementById('pageInfo');
    if (pageInfo && pageInfo.dataset.current && pageInfo.dataset.total) {
        // We'll store state in dataset to re-translate
        const current = pageInfo.dataset.current;
        const total = pageInfo.dataset.total;
        pageInfo.textContent = translations[lang].page_info.replace('{current}', current).replace('{total}', total);
    }
}

let currentFeedbackFilter = 'all';

async function loadFilters() {
    try {
        const response = await fetch('/dashboard/api/filters');
        const result = await response.json();
        if (result.success) {
            const preds = result.data.predicted_ids;
            const users = result.data.user_ids;

            const predSelect = document.getElementById('filterPredictedId');
            if (predSelect) {
                predSelect.innerHTML = '<option value="">All</option>';
                preds.forEach(id => {
                    const opt = document.createElement('option');
                    opt.value = id;
                    const formatted = formatTemplateDisplay(id);
                    opt.textContent = formatted;
                    predSelect.appendChild(opt);
                });
            }

            const userSelect = document.getElementById('filterUserId');
            if (userSelect) {
                userSelect.innerHTML = '<option value="">All</option>';
                users.forEach(uid => {
                    const opt = document.createElement('option');
                    opt.value = uid;
                    opt.textContent = uid;
                    userSelect.appendChild(opt);
                });
            }
        }
    } catch (e) { console.error(e); }
}

function setFeedbackFilter(val) {
    currentFeedbackFilter = val;
    document.getElementById('filterFeedback').value = val;

    // Update styles
    const map = { 'all': 'btn_all', 'feedback': 'btn_feedback', 'none': 'btn_none' };

    Object.keys(map).forEach(imgKey => {
        const btn = document.getElementById(map[imgKey]);
        if (!btn) return;

        if (imgKey === val) {
            btn.classList.add('active');
            btn.style.background = '#3b82f6';
            btn.style.color = 'white';
        } else {
            btn.classList.remove('active');
            btn.style.background = '#f1f5f9';
            btn.style.color = '#64748b';
        }
    });
}

function searchLogs() {
    currentPage = 1;
    loadLogs(currentPage);
}

async function loadLogs(page) {
    try {
        const startDate = document.getElementById('filterStartDate')?.value || '';
        const endDate = document.getElementById('filterEndDate')?.value || '';
        const predictedId = document.getElementById('filterPredictedId')?.value || '';
        const userId = document.getElementById('filterUserId')?.value || '';
        const feedbackStatus = currentFeedbackFilter;
        const queryText = document.getElementById('filterQuery')?.value || '';

        const params = new URLSearchParams({
            page: page,
            page_size: pageSize,
            start_date: startDate,
            end_date: endDate,
            predicted_id: predictedId,
            user_id: userId,
            feedback_status: feedbackStatus,
            query_text: queryText
        });

        const response = await fetch(`/dashboard/api/logs?${params.toString()}`);
        const result = await response.json();

        if (result.success) {
            renderLogs(result.data.logs);
            updatePagination(result.data);
        }
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatTemplateDisplay(id) {
    if (!id) return '-';
    if (window.allTemplates && window.allTemplates.length) {
        const found = window.allTemplates.find(t => t.id == id);
        if (found) return `[${found.id}] ${found.category}`;
    }
    return `[${id}]`;
}

function renderLogs(logs) {
    const tbody = document.getElementById('logsTableBody');
    if (!logs.length) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;">${translations[currentLang].msg_no_logs}</td></tr>`;
        return;
    }

    tbody.innerHTML = logs.map(log => `
        <tr class="log-row" onclick="toggleLogDetail(${log.id}, this)" style="cursor: pointer;">
            <td style="text-align: right;">${log.id}</td>
            <td style="text-align: center;">${log.request_time}</td>
            <td title="${escapeHtml(log.query_text)}"><div class="truncate">${escapeHtml(log.query_text)}</div></td>
            <td style="text-align: left;">${formatTemplateDisplay(log.predicted_template_id)}</td>
            <td>${log.user_id || '-'}</td>
            <td style="text-align: center;">${log.manual_answer ? `<span class="status-badge success">${translations[currentLang].feedback_badge}</span>` : '-'}</td>
        </tr>
        <tr id="detail-${log.id}" class="log-detail-row" style="display: none;">
            <td colspan="6">
                <div class="log-detail-content">
                    <div class="detail-section">
                        <h4>${translations[currentLang].detail_query_full}</h4>
                        <div class="detail-box">${escapeHtml(log.query_text)}</div>
                    </div>
                    
                    <div class="detail-grid">
                        <div class="detail-section">
                            <h4>${translations[currentLang].detail_ranks}</h4>
                            <ul>
                                <li><strong>Rank 1:</strong> ${formatTemplateDisplay(log.rank1_id)}</li>
                                <li><strong>Rank 2:</strong> ${formatTemplateDisplay(log.rank2_id)}</li>
                                <li><strong>Rank 3:</strong> ${formatTemplateDisplay(log.rank3_id)}</li>
                            </ul>
                        </div>
                        <div class="detail-section">
                            <h4>${translations[currentLang].detail_extracted}</h4>
                            <ul>
                                <li><strong>Client IP:</strong> ${log.client_ip || '-'}</li>
                                <li><strong>Process Time:</strong> ${log.processing_time ? log.processing_time.toFixed(4) + 's' : '-'}</li>
                                <li><strong>Customer #:</strong> ${log.customer_number || '-'}</li>
                            </ul>
                        </div>
                    </div>

                    ${log.manual_answer ? `
                    <div class="detail-section feedback-section">
                        <h4>${translations[currentLang].detail_feedback_content}</h4>
                        <div class="detail-box feedback">
                            <div><strong>Category:</strong> ${escapeHtml(log.manual_category || '-')}</div>
                            <div style="margin-top:0.5rem; white-space:pre-wrap;">${escapeHtml(log.manual_answer)}</div>
                        </div>
                    </div>
                    ` : ``}
                </div>
            </td>
        </tr>
    `).join('');
}

function toggleLogDetail(id, trElem) {
    const detailRow = document.getElementById(`detail-${id}`);
    const isVisible = detailRow && detailRow.style.display === 'table-row';

    // Close ALL detail rows
    document.querySelectorAll('.log-detail-row').forEach(row => {
        row.style.display = 'none';
    });

    // Reset ALL Row Selections
    document.querySelectorAll('.log-row').forEach(row => {
        row.classList.remove('selected-log-row');
        row.style.background = '';
    });

    // If it was NOT visible before, open it and select row
    if (!isVisible) {
        if (detailRow) detailRow.style.display = 'table-row';
        if (trElem) {
            trElem.classList.add('selected-log-row');
        }
    }
}

function updatePagination(data) {
    currentPage = data.page;
    const pageInfo = document.getElementById('pageInfo');

    // Store for translation
    pageInfo.dataset.current = data.page;
    pageInfo.dataset.total = data.total_pages;

    pageInfo.textContent = translations[currentLang].page_info
        .replace('{current}', data.page)
        .replace('{total}', data.total_pages);

    document.getElementById('prevBtn').disabled = data.page === 1;
    document.getElementById('nextBtn').disabled = data.page === data.total_pages || data.total_pages === 0;
}

function changePage(delta) {
    loadLogs(currentPage + delta);
}

function changePageSize(size) {
    pageSize = parseInt(size);
    currentPage = 1;
    loadLogs(currentPage);
}

function updateDate() {
    const now = new Date();
    const locale = currentLang === 'ko' ? 'ko-KR' : 'en-US';
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    const dateEl = document.getElementById('currentDate');
    if (dateEl) {
        dateEl.textContent = now.toLocaleDateString(locale, options);
    }
}

async function loadDashboardStats() {
    try {
        const response = await fetch('/dashboard/api/stats');
        const data = await response.json();

        if (data.success) {
            renderStats(data.stats, data.template_map);
            renderCharts(data.stats, data.template_map);
        } else {
            console.error('Failed to load stats:', data.error);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function renderStats(stats, templateMap) {
    const summary = stats.summary;
    document.getElementById('totalQueries').textContent = summary.total.toLocaleString();

    // Total Templates
    const totalTemplates = templateMap ? Object.keys(templateMap).length : 0;
    const totalTemplatesEl = document.getElementById('totalTemplates');
    if (totalTemplatesEl) {
        totalTemplatesEl.textContent = totalTemplates.toLocaleString() + '개';
    }

    // Feedback Rate: 5.8% (Count건)
    const feedbackRateEl = document.getElementById('feedbackRate');
    if (feedbackRateEl) {
        if (summary.total > 0) {
            feedbackRateEl.textContent = `${stats.feedback_rate.toFixed(1)}% (${summary.feedback_count}건)`;
        } else {
            feedbackRateEl.textContent = '0% (0건)';
        }
    }


}

let trendChartInstance = null;
let templateChartInstance = null;
let userActivityChartInstance = null;
let userTemplateChartInstance = null;

// Theme Configuration Helper
function getThemeConfig() {
    const theme = document.documentElement.getAttribute('data-theme') || 'mono';
    const isDark = theme === 'blueblackp';

    if (theme === 'blueblackp') {
        return {
            text: '#e2e8f0', // slate-200
            line: '#a5b4fc', // indigo-300
            grid: 'rgba(255, 255, 255, 0.1)',
            cardBg: '#1e293b',
            pieColors: ['#818cf8', '#6366f1', '#4f46e5', '#4338ca', '#3730a3'],
            barBg: '#818cf8',
            barBorder: '#6366f1',
            heatmap: {
                bgHigh: '#4f46e5',
                bgMid: '#6366f1',
                bgLow: '#1e1b4b',
                textHigh: '#ffffff',
                textLow: '#94a3b8',
                border: '#334155', // slate-700
                headerBg: '#0f172a' // slate-900
            }
        };
    } else if (theme === 'whitegrayo') {
        return {
            text: '#1e293b', // slate-800
            line: '#f97316', // orange-500
            grid: 'rgba(0, 0, 0, 0.05)',
            cardBg: '#ffffff',
            pieColors: ['#fb923c', '#f97316', '#ea580c', '#c2410c', '#9a3412'],
            barBg: '#ffedd5',
            barBorder: '#fb923c',
            heatmap: {
                bgHigh: '#ea580c',
                bgMid: '#fb923c',
                bgLow: '#fff7ed',
                textHigh: '#ffffff',
                textLow: '#1e293b',
                border: '#cbd5e1',
                headerBg: '#f8fafc'
            }
        };
    } else if (theme === 'whitegrayb') {
        return {
            text: '#1e293b', // slate-800
            line: '#014DFF', // Primary Accent
            grid: 'rgba(0, 0, 0, 0.05)',
            cardBg: '#ffffff', // Card Background Updated to White
            pieColors: ['#60a5fa', '#94a3b8', '#93c5fd', '#cbd5e1', '#bfdbfe'],
            barBg: '#bfdbfe',
            barBorder: '#014DFF',
            heatmap: {
                bgHigh: '#60a5fa',
                bgMid: '#cbd5e1',
                bgLow: '#f8fafc',
                textHigh: '#ffffff',
                textLow: '#1e293b',
                border: '#e2e8f0', // Matches theme border
                headerBg: '#F5F4FA' // Content Area BG
            }
        };
    } else {
        // Mono (Default)
        return {
            text: '#000000',
            line: '#000000',
            grid: 'rgba(0, 0, 0, 0.05)',
            cardBg: '#ffffff',
            pieColors: ['#6b7280', '#9ca3af', '#cbd5e1', '#e2e8f0', '#f8fafc'],
            barBg: ['#374151', '#4b5563', '#6b7280', '#9ca3af', '#d1d5db'],
            barBorder: '#000000',
            heatmap: {
                bgHigh: '#171717',
                bgMid: '#737373',
                bgLow: '#e5e5e5',
                textHigh: '#ffffff',
                textLow: '#000000',
                border: '#000000',
                headerBg: '#ffffff'
            }
        };
    }
}

function renderCharts(stats, templateMap) {
    // Destroy existing charts if they exist to allow updates
    if (trendChartInstance) trendChartInstance.destroy();
    if (templateChartInstance) templateChartInstance.destroy();

    const theme = getThemeConfig();

    // Trend Chart
    const trendCtx = document.getElementById('trendChart').getContext('2d');
    const trendGradient = trendCtx.createLinearGradient(0, 0, 0, 400);
    // Adjust gradient based on theme? kept simple for now
    trendGradient.addColorStop(0, 'rgba(15, 23, 42, 0.5)');
    trendGradient.addColorStop(1, 'rgba(15, 23, 42, 0.05)');

    // Custom plugin to draw values on lines
    const drawTrendValues = {
        id: 'drawTrendValues',
        afterDatasetsDraw(chart) {
            const { ctx } = chart;
            ctx.save();
            chart.data.datasets.forEach((dataset, i) => {
                const meta = chart.getDatasetMeta(i);
                if (!meta.hidden) {
                    meta.data.forEach((element, index) => {
                        const data = dataset.data[index];
                        if (data !== null && data !== undefined && data > 0) {
                            ctx.fillStyle = theme.text;
                            ctx.font = 'bold 11px Inter';
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'bottom';
                            const x = element.x;
                            const y = element.y;
                            ctx.fillText(data, x, y - 8);
                        }
                    });
                }
            });
            ctx.restore();
        }
    };

    trendChartInstance = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: stats.daily_trend.map(item => {
                const d = new Date(item.date);
                const year = d.getFullYear();
                const month = String(d.getMonth() + 1).padStart(2, '0');
                const day = String(d.getDate()).padStart(2, '0');
                return `${year}.${month}.${day}`;
            }),
            datasets: [{
                label: translations[currentLang].label_daily_queries,
                data: stats.daily_trend.map(item => item.count),
                borderColor: theme.line,
                backgroundColor: 'rgba(0,0,0,0)',
                fill: false,
                tension: 0,
                pointBackgroundColor: theme.cardBg,
                pointBorderColor: theme.line,
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: { top: 20, right: 0, left: 0 }
            },
            // Chart.js 3+ Legend
            plugins: {
                legend: {
                    display: false
                }
            },
            // Chart.js 2.x Legend
            legend: {
                display: false
            },
            scales: {
                y: { beginAtZero: true, grid: { color: theme.grid }, ticks: { color: theme.text } },
                x: {
                    type: 'category',
                    grid: { color: theme.grid, offset: false },
                    offset: false,
                    ticks: {
                        color: theme.text,
                        maxRotation: 0,
                        align: 'inner'
                    }
                }
            }
        },
        plugins: [drawTrendValues]
    });

    // Template Chart
    const templateCtx = document.getElementById('templateChart').getContext('2d');
    const pieColors = theme.pieColors;

    templateChartInstance = new Chart(templateCtx, {
        type: 'doughnut',
        data: {
            labels: stats.top_templates.map(t => {
                const category = (templateMap && templateMap[t.predicted_template_id]) || '';
                return `[${t.predicted_template_id}] ${category}`;
            }),
            datasets: [{
                data: stats.top_templates.map(t => t.count),
                backgroundColor: pieColors,
                borderColor: theme.cardBg,
                borderWidth: 2
            }]
        },
        plugins: [{
            id: 'segmentLabels',
            afterDatasetsDraw(chart) {
                const { ctx } = chart;
                chart.data.datasets.forEach((dataset, i) => {
                    const meta = chart.getDatasetMeta(i);
                    const total = dataset.data.reduce((acc, curr) => acc + curr, 0);

                    meta.data.forEach((element, index) => {
                        // Only draw if visible and has value
                        if (!element.hidden && dataset.data[index] > 0) {
                            const value = dataset.data[index];
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) + '%' : '0%';

                            const { x, y } = element.tooltipPosition();

                            ctx.save();
                            ctx.fillStyle = theme.text;
                            ctx.font = 'bold 11px "Inter", sans-serif';
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';

                            ctx.fillText(`${value}`, x, y - 7);
                            ctx.fillText(`(${percentage})`, x, y + 7);
                            ctx.restore();
                        }
                    });
                });
            }
        }],
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: theme.text, boxWidth: 12 }
                }
            }
        }
    });

    // User Activity Chart - 1. Electric Blue
    if (stats.user_stats && document.getElementById('userActivityChart')) {
        if (userActivityChartInstance) userActivityChartInstance.destroy();
        const uaCtx = document.getElementById('userActivityChart').getContext('2d');
        const uaGradient = uaCtx.createLinearGradient(0, 0, 0, 300);
        uaGradient.addColorStop(0, 'rgba(15, 23, 42, 0.8)');
        uaGradient.addColorStop(1, 'rgba(15, 23, 42, 0.2)');

        userActivityChartInstance = new Chart(uaCtx, {
            type: 'bar',
            data: {
                labels: stats.user_stats.map(u => u.user_id),
                datasets: [{
                    label: 'Logs Generated',
                    data: stats.user_stats.map(u => u.count),
                    backgroundColor: theme.barBg,
                    borderColor: theme.barBorder,
                    borderWidth: 0
                }]
            },
            plugins: [{
                id: 'uaLabels',
                afterDatasetsDraw(chart) {
                    const { ctx } = chart;
                    chart.data.datasets.forEach((dataset, i) => {
                        const meta = chart.getDatasetMeta(i);
                        meta.data.forEach((bar, index) => {
                            const value = dataset.data[index];
                            if (value > 0) {
                                ctx.save();
                                ctx.fillStyle = theme.text;
                                ctx.font = 'bold 11px "Inter", sans-serif';
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'bottom';
                                ctx.fillText(value, bar.x, bar.y - 4);
                                ctx.restore();
                            }
                        });
                    });
                }
            }],
            options: {
                layout: { padding: { top: 25 } },
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: theme.grid },
                        ticks: { color: theme.text }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: theme.text }
                    }
                }
            }
        });
    }

    // User-Template Heatmap (Top 5 Users)
    if (stats.user_template_stats) {
        // Destroy Chart if exists and hide canvas
        if (userTemplateChartInstance) {
            userTemplateChartInstance.destroy();
            userTemplateChartInstance = null;
        }
        const canvas = document.getElementById('userTemplateChart');
        if (canvas) canvas.style.display = 'none';

        // 1. Get Top 5 Users
        const topUsers = [...stats.user_stats]
            .sort((a, b) => b.count - a.count)
            .slice(0, 5)
            .map(u => u.user_id);

        if (topUsers.length === 0) return;

        // 2. Get Relevant Templates & Max Count
        const relevantStats = stats.user_template_stats.filter(s => topUsers.includes(s.user_id));
        const templateIds = Array.from(new Set(relevantStats.map(s => s.predicted_template_id))).sort((a, b) => a - b);

        let maxCount = 0;
        const matrixMap = {}; // { "userId-tmplId": count }
        relevantStats.forEach(s => {
            matrixMap[`${s.user_id}-${s.predicted_template_id}`] = s.usage_count;
            if (s.usage_count > maxCount) maxCount = s.usage_count;
        });

        // 3. Create Container
        let container = document.getElementById('userTemplateHeatmap');
        if (!container) {
            container = document.createElement('div');
            container.id = 'userTemplateHeatmap';
            container.style.width = '100%';
            container.style.height = '300px';
            container.style.overflow = 'auto';
            if (canvas && canvas.parentNode) canvas.parentNode.appendChild(container);
        }
        container.innerHTML = '';
        container.style.display = 'block';

        // 4. Build Table CSS
        // 4. Build Table CSS
        const tableStyle = `
            width: 100%; 
            border-collapse: collapse; 
            font-size: 0.8rem;
            color: ${theme.heatmap.textLow};
            border: 2px solid ${theme.heatmap.border};
            font-family: inherit;
        `;
        const thStyle = `
            padding: 8px; 
            position: sticky; 
            top: 0; 
            background: ${theme.heatmap.headerBg}; 
            color: ${theme.heatmap.textLow};
            z-index: 10;
            text-align: center;
            border-bottom: 2px solid ${theme.heatmap.border};
            border-right: 1px solid ${theme.heatmap.border};
            font-weight: 700;
        `;
        const tdIdStyle = `
            padding: 8px;
            position: sticky;
            left: 0;
            background: ${theme.heatmap.headerBg};
            z-index: 5;
            text-align: left;
            border-right: 2px solid ${theme.heatmap.border};
            border-bottom: 1px solid ${theme.heatmap.border};
            font-weight: 700;
            color: ${theme.heatmap.textLow};
            width: 30%;
            white-space: normal;
            line-height: 1.2;
        `;

        // 5. Build HTML
        const diagBg = `linear-gradient(to top right, ${theme.heatmap.headerBg} 49%, ${theme.heatmap.border} 49%, ${theme.heatmap.border} 51%, ${theme.heatmap.headerBg} 51%)`;
        let html = `<table style="${tableStyle}"><thead><tr>
            <th style="${thStyle}; left:0; z-index:20; width:30%; padding:0; background: ${diagBg}; position: relative; min-width: 120px;">
                <div style="position: absolute; top: 4px; right: 8px; font-size: 0.8rem;">User</div>
                <div style="position: absolute; bottom: 4px; left: 8px; font-size: 0.8rem;">템플릿</div>
            </th>`;
        topUsers.forEach(u => {
            html += `<th style="${thStyle}">${u}</th>`;
        });
        html += '</tr></thead><tbody>';

        templateIds.forEach(tid => {
            const category = (templateMap && templateMap[tid]) || '';
            html += `<tr><td style="${tdIdStyle}" title="${category}">[${tid}] ${category}</td>`;
            topUsers.forEach(uid => {
                const count = matrixMap[`${uid}-${tid}`] || 0;
                let bg = theme.heatmap.bgLow;
                let color = '#999';

                if (count > 0) {
                    const ratio = maxCount > 0 ? (count / maxCount) : 0;
                    if (ratio > 0.8) bg = theme.heatmap.bgHigh;
                    else if (ratio > 0.4) bg = theme.heatmap.bgMid;
                    // else use default low

                    color = (ratio > 0.4) ? theme.heatmap.textHigh : theme.heatmap.textLow;
                }

                html += `<td style="background:${bg}; color:${color}; text-align:center; padding:6px; border:1px solid ${theme.heatmap.border};">${count > 0 ? count : '-'}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table>';

        container.innerHTML = html;
    }
}

// Server Health Check
let healthCheckFailures = 0;
const MAX_FAILURES = 3;

async function checkServerHealth() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

        const response = await fetch('/dashboard/api/health', {
            signal: controller.signal,
            headers: { 'Cache-Control': 'no-cache' }
        });
        clearTimeout(timeoutId);

        if (response.ok) {
            const data = await response.json();

            // 1. Session Check (Priority)
            if (data.success && data.logged_in === false) {
                // Session expired or invalid
                alert("세션이 만료되었습니다. 재 접속 바랍니다.");
                window.location.href = '/login';
                return;
            }

            healthCheckFailures = 0;
        } else {
            handleHealthFailure();
        }
    } catch (error) {
        console.error('Health Check Failed:', error);
        handleHealthFailure();
    }
}

function handleHealthFailure() {
    healthCheckFailures++;
    if (healthCheckFailures >= 5) { // MAX_FAILURES = 5
        alert("서버와의 연결이 끊어졌습니다. 재 접속 바랍니다.");
        window.location.href = '/login';
    }
}

// Start health check every 10 seconds
setInterval(checkServerHealth, 10000);
