let userActivityChartInstance = null;
let userTemplateChartInstance = null;

function renderUserCharts(userStats, userTemplateStats) {
    // 1. User Activity Chart
    const ctx1 = document.getElementById('userActivityChart').getContext('2d');
    const userLabels = userStats.map(u => u.user_id);
    const userCounts = userStats.map(u => u.count);

    if (userActivityChartInstance) userActivityChartInstance.destroy();

    userActivityChartInstance = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: userLabels,
            datasets: [{
                label: 'Total Generated Logs',
                data: userCounts,
                backgroundColor: 'rgba(59, 130, 246, 0.6)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { labels: { color: '#cbd5e1' } }
            }
        }
    });

    // 2. User-Template Stacked Bar Chart
    const ctx2 = document.getElementById('userTemplateChart').getContext('2d');

    const uniqueTemplates = [...new Set(userTemplateStats.map(i => i.predicted_template_id))];
    const templateUsage = {};
    userTemplateStats.forEach(i => {
        templateUsage[i.predicted_template_id] = (templateUsage[i.predicted_template_id] || 0) + i.usage_count;
    });
    const topTemplates = Object.entries(templateUsage)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 7)
        .map(e => parseInt(e[0]));

    const datasets = topTemplates.map((tid, index) => {
        const data = userLabels.map(uid => {
            const entry = userTemplateStats.find(x => x.user_id === uid && x.predicted_template_id === tid);
            return entry ? entry.usage_count : 0;
        });
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];
        return {
            label: `Template ${tid}`,
            data: data,
            backgroundColor: colors[index % colors.length]
        };
    });

    if (userTemplateChartInstance) userTemplateChartInstance.destroy();

    userTemplateChartInstance = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: userLabels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true,
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    stacked: true,
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { labels: { color: '#cbd5e1' } }
            }
        }
    });
}