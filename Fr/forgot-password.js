```javascript
const resetForm = document.getElementById("resetForm");
const sendOtpBtn = document.getElementById("sendOtpBtn");
const message = document.getElementById("message");

function showMessage(text, success = false) {
    message.textContent = text;
    message.style.color = success ? "green" : "crimson";
}

async function apiRequest(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.detail || "Something went wrong.");
    }

    return result;
}

sendOtpBtn.addEventListener("click", async () => {
    const email = document.getElementById("email").value.trim();

    if (!email) {
        showMessage("Please enter your email address.");
        return;
    }

    sendOtpBtn.disabled = true;
    sendOtpBtn.textContent = "Sending OTP...";

    try {
        const result = await apiRequest(
            "/api/forgot-password/send-otp",
            { email }
        );

        showMessage(result.message, true);
    } catch (error) {
        showMessage(error.message);
    } finally {
        sendOtpBtn.disabled = false;
        sendOtpBtn.textContent = "Send OTP";
    }
});

resetForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const otp = document.getElementById("otp").value.trim();
    const newPassword =
        document.getElementById("newPassword").value;
    const confirmPassword =
        document.getElementById("confirmPassword").value;

    if (newPassword !== confirmPassword) {
        showMessage("Passwords do not match.");
        return;
    }

    if (newPassword.length < 8) {
        showMessage("Password must be at least 8 characters.");
        return;
    }

    const submitButton = resetForm.querySelector(
        'button[type="submit"]'
    );

    submitButton.disabled = true;
    submitButton.textContent = "Resetting...";

    try {
        const result = await apiRequest(
            "/api/forgot-password/reset",
            {
                email,
                otp,
                new_password: newPassword
            }
        );

        showMessage(result.message, true);
        resetForm.reset();

        setTimeout(() => {
            window.location.href = "/";
        }, 1500);
    } catch (error) {
        showMessage(error.message);
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Reset Password";
    }
});
```
