const API = {
    async getStats() {
        const res = await fetch('/api/stats');
        return await res.json();
    },
    async getTemplates() {
        const res = await fetch('/api/templates');
        return await res.json();
    },
    async findTemplate(query, signal) {
        const res = await fetch('/api/find_template', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
            signal: signal
        });
        return await res.json();
    },
    async submitFeedback(data) {
        const res = await fetch('/api/submit_feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await res.json();
    }
};