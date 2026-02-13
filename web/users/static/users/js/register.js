// users/static/users/js/register.js
document.addEventListener('DOMContentLoaded', () => {
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirm_password');
    const registerButton = document.getElementById('registerButton');

    function validatePasswords() {
        const pass = passwordInput.value;
        const confirm = confirmInput.value;

        if (confirm.length > 0) {
            if (pass !== confirm) {
                confirmInput.classList.add('is-invalid');
                confirmInput.classList.remove('is-valid');
                registerButton.disabled = true;
            } else {
                confirmInput.classList.remove('is-invalid');
                confirmInput.classList.add('is-valid');
                registerButton.disabled = false;
            }
        } else {
            confirmInput.classList.remove('is-invalid');
            confirmInput.classList.remove('is-valid');
            registerButton.disabled = false; // Allow submission to trigger required check
        }
    }

    passwordInput.addEventListener('input', validatePasswords);
    confirmInput.addEventListener('input', validatePasswords);
});
