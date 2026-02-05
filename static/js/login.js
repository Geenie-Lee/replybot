function getNested(obj, path) {
    return path.split('.').reduce((o, i) => (o ? o[i] : null), obj);
}

function changeLanguage(lang) {
    localStorage.setItem('replybot_lang', lang);
    const t = i18n[lang];

    // Text Content Update
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = getNested(t, key);
        if (val) el.textContent = val;
    });

    // Placeholder Update
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const val = getNested(t, key);
        if (val) el.placeholder = val;
    });
}

function toggleRegisterModal() {
    const modal = document.getElementById('registerModal');
    if (modal.classList.contains('hidden')) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    } else {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

function toggleResetModal() {
    const modal = document.getElementById('resetModal');
    if (modal.classList.contains('hidden')) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    } else {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

// Note: window.onload logic will need to remain in the HTML or be adapted to read server-side variables initiated in the HTML.
// We'll keep the variable initialization in the HTML and call this script.

async function handleSetPassword(event) {
    event.preventDefault();
    const form = event.target;
    // form.user_id might be disabled/readonly but value should be accessible if not disabled. 
    // It is readonly, so it submits.
    const user_id = form.user_id.value;
    const password = form.password.value;
    const confirm = document.getElementById('setPwConfirm').value;

    if (password !== confirm) {
        alert('비밀번호가 일치하지 않습니다.');
        return false;
    }

    try {
        const response = await fetch('/set_initial_password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user_id, password: password })
        });
        const result = await response.json();

        if (result.success) {
            alert(result.message);
            window.location.href = '/login';
        } else {
            alert(result.error);
        }
    } catch (e) {
        console.error(e);
        alert('Error setting password.');
    }
    return false;
}

async function handleRegister(event) {
    event.preventDefault();

    const form = event.target;
    // Basic Client-side Validation
    const password = form.password.value;
    const confirmPassword = form.confirm_password.value;

    if (password !== confirmPassword) {
        const currentLang = localStorage.getItem('replybot_lang') || 'ko';
        let msg = '비밀번호가 일치하지 않습니다.';
        if (typeof i18n !== 'undefined' && i18n[currentLang]) {
            msg = getNested(i18n[currentLang], 'login.msg_password_mismatch') || msg;
        }
        alert(msg);
        return false;
    }

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Clear previous errors
    const errorDiv = document.getElementById('registerError');
    if (errorDiv) {
        errorDiv.style.display = 'none';
        errorDiv.innerText = '';
    }

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert(result.message || 'Registration successful.');
            toggleRegisterModal();
            form.reset();
        } else {
            // Show error in modal
            if (errorDiv) {
                errorDiv.innerText = result.error || 'Registration failed.';
                errorDiv.style.display = 'block';
            } else {
                alert(result.error);
            }
        }
    } catch (e) {
        console.error('Registration error:', e);
        if (errorDiv) {
            errorDiv.innerText = 'System Error: ' + e.message;
            errorDiv.style.display = 'block';
        }
    }
    return false;
}

function validateRegisterForm() {
    // Deprecated but kept for compatibility references if any
    return true;
}
