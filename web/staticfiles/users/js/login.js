// users/static/users/js/login.js
document.addEventListener('DOMContentLoaded', () => {
    const usernameInput = document.getElementById('id_username');
    const passwordInput = document.getElementById('id_password');
    const userSection = document.getElementById('userSection');
    const passwordSection = document.getElementById('passwordSection');
    const nextButton = document.getElementById('nextButton');
    const loginForm = document.getElementById('loginForm');

    let isPasswordVisible = false;

    // Initial check
    toggleNextButton();

    usernameInput.addEventListener('input', toggleNextButton);

    // Enter key handling
    usernameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (!nextButton.disabled) handleNext();
        }
    });

    passwordInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (passwordInput.value.trim() !== "") {
                loginForm.submit();
            }
        }
    });

    nextButton.addEventListener('click', handleNext);

    function toggleNextButton() {
        if (!isPasswordVisible) {
            nextButton.disabled = usernameInput.value.trim() === "";
        }
    }

    function handleNext() {
        if (!isPasswordVisible) {
            // Switch to password view
            passwordSection.classList.remove('d-none');
            passwordSection.classList.add('animate-fade-in');

            passwordInput.focus();

            nextButton.innerText = "Iniciar Sesión";
            isPasswordVisible = true;
        } else {
            // Submit form
            if (passwordInput.value.trim() !== "") {
                nextButton.disabled = true;
                nextButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Verificando...';
                loginForm.submit();
            } else {
                passwordInput.classList.add('is-invalid');
                passwordInput.focus();

                // Remove invalid state on input
                passwordInput.addEventListener('input', () => {
                    passwordInput.classList.remove('is-invalid');
                }, { once: true });
            }
        }
    }
});
