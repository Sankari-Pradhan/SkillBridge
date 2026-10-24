
const API = "https://skillbridge-dka3.onrender.com";

const registerForm = document.getElementById("registerForm");
const verifyOtpForm = document.getElementById("verifyOtpForm");
const message = document.getElementById("registerMessage");

const nameInput = document.getElementById("registerName");
const emailInput = document.getElementById("registerEmail");
const passwordInput = document.getElementById("registerPassword");
const otpInput = document.getElementById("registerOTP");

const sendOtpBtn = document.getElementById("sendOtpBtn");
const verifyOtpBtn = document.getElementById("verifyOtpBtn");
const resendOtpBtn = document.getElementById("resendOtpBtn");

function showMessage(text, isError = false) {
    if (!message) return;

    message.textContent = text;
    message.style.color = isError ? "#dc2626" : "#15803d";
}

async function apiRequest(endpoint, payload) {
    const response = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            typeof data.detail === "string"
                ? data.detail
                : "Request failed. Please try again."
        );
    }

    return data;
}

function getRegistrationData() {
    return {
        name: nameInput.value.trim(),
        email: emailInput.value.trim().toLowerCase(),
        password: passwordInput.value
    };
}

// Step 1: Send OTP
if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!registerForm.reportValidity()) return;

        sendOtpBtn.disabled = true;
        showMessage("Sending OTP to your email...");

        try {
            const data = await apiRequest(
                "/api/register/send-otp",
                getRegistrationData()
            );

            registerForm.hidden = true;
            verifyOtpForm.hidden = false;

            showMessage(data.message || "OTP sent. Check your email.");

            if (otpInput) otpInput.focus();
        } catch (error) {
            showMessage(error.message || "Could not send OTP.", true);
        } finally {
            sendOtpBtn.disabled = false;
        }
    });
}

// Step 2: Verify OTP and create account
if (verifyOtpForm) {
    verifyOtpForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const otp = otpInput.value.trim();

        if (!/^\d{6}$/.test(otp)) {
            showMessage("Enter the 6-digit OTP.", true);
            return;
        }

        verifyOtpBtn.disabled = true;
        showMessage("Verifying OTP...");

        try {
            const data = await apiRequest(
                "/api/register/verify-otp",
                {
                    email: emailInput.value.trim().toLowerCase(),
                    otp: otp
                }
            );

            showMessage(
                data.message ||
                "Account created successfully. Redirecting to login..."
            );

            verifyOtpForm.reset();

            setTimeout(() => {
                window.location.href = "/";
            }, 1500);
        } catch (error) {
            showMessage(
                error.message || "OTP verification failed.",
                true
            );
        } finally {
            verifyOtpBtn.disabled = false;
        }
    });
}

// Resend OTP
if (resendOtpBtn) {
    resendOtpBtn.addEventListener("click", async () => {
        resendOtpBtn.disabled = true;
        showMessage("Requesting a new OTP...");

        try {
            const data = await apiRequest(
                "/api/register/send-otp",
                getRegistrationData()
            );

            otpInput.value = "";

            showMessage(
                data.message || "New OTP sent. Check your email."
            );
        } catch (error) {
            showMessage(
                error.message || "Could not resend OTP.",
                true
            );
        } finally {
            resendOtpBtn.disabled = false;
        }
    });
}
