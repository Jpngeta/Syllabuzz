document.addEventListener("DOMContentLoaded", function () {
    /** 📝 Handles form submission **/
    async function handleSubmit(event, endpoint) {
        event.preventDefault();

        const formData = new FormData(event.target);
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error("Failed to submit form.");
            }

            const result = await response.json();
            if (result.success) {
                window.location.href = result.redirect;
            } else {
                showAlert(result.message, "error");
            }
        } catch (error) {
            console.error("Submission Error:", error);
            showAlert("An error occurred. Please try again.", "error");
        }
    }

    /** 📌 Attaches form handlers dynamically **/
    function attachFormHandler(selector, endpoint) {
        const form = document.querySelector(selector);
        if (form) {
            form.addEventListener("submit", (e) => handleSubmit(e, endpoint));
        }
    }

    attachFormHandler("#login-form", "/");
    attachFormHandler("#signup-form", "/signup");
    attachFormHandler("#forgot-password-form", "/forgot-password");

    /** 🔑 Handles reset password with validation **/
    const resetPasswordForm = document.querySelector("#reset-password");
    if (resetPasswordForm) {
        resetPasswordForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const newPassword = document.getElementById("new-password").value;
            const confirmPassword = document.getElementById("confirm-password").value;

            if (!newPassword || !confirmPassword) {
                showAlert("Please fill in both password fields.", "error");
                return;
            }

            if (newPassword !== confirmPassword) {
                showAlert("Passwords do not match", "error");
                return;
            }

            const token = this.dataset.token;
            if (!token) {
                showAlert("Invalid reset token.", "error");
                return;
            }

            handleSubmit(e, `/reset-password/${token}`);
        });
    }

    /** ⏳ Smooth Flash Message Fade-out **/
    const flashMessages = document.getElementById("flash-messages");
    if (flashMessages) {
        setTimeout(() => {
            flashMessages.style.opacity = "0";
            setTimeout(() => flashMessages.remove(), 500);
        }, 3000);
    }

    function applyTheme(theme) {
        document.documentElement.classList.toggle("dark", theme === "dark");
        localStorage.setItem("theme", theme);
        
        // Fix for input text visibility when theme changes
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (theme === 'dark') {
                input.style.color = '#f0f0f0'; // Light text for dark theme
            } else {
                input.style.color = '#333'; // Dark text for light theme
            }
        });
    }

    /** 🚀 Shows Dynamic Alerts **/
    function showAlert(message, type = "info") {
        const alertBox = document.createElement("div");
        alertBox.textContent = message;
        alertBox.className = `alert-box ${type}`;
        
        // Ensure only one alert at a time
        const existingAlert = document.querySelector(".alert-box");
        if (existingAlert) {
            existingAlert.remove();
        }

        document.body.appendChild(alertBox);

        setTimeout(() => {
            alertBox.style.opacity = "0";
            setTimeout(() => alertBox.remove(), 500);
        }, 3000);
    }
});
