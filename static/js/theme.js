(function () {
    // 1. Get saved theme
    const savedTheme = localStorage.getItem('replybot_theme') || 'mono';

    // 2. Apply to document immediately to prevent flash
    document.documentElement.setAttribute('data-theme', savedTheme);

    // 3. Expose change function globally
    window.changeTheme = function (theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('replybot_theme', theme);
    };

    // 4. Update UI when DOM is ready
    window.addEventListener('DOMContentLoaded', () => {
        const select = document.getElementById('themeSelect');
        if (select) {
            select.value = savedTheme;
        }
    });
})();
