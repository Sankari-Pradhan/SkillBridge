
const API = "https://skillbridge-dka3.onrender.com";

document.getElementById("registerForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = document.getElementById("registerMessage");
    message.textContent = "Creating account...";

    try {
        const response = await fetch(`${API}/api/users`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: document.getElementById("registerName").value.trim(),
                email: document.getElementById("registerEmail").value.trim(),
                password: document.getElementById("registerPassword").value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : "Could not create account."
            );
        }

        message.textContent = "Account created! Redirecting to login...";
        document.getElementById("registerForm").reset();

        setTimeout(() => {
            window.location.href = "/";
        }, 1500);

    } catch (error) {
        message.textContent = error.message || "Unable to connect to server.";
    }
});
