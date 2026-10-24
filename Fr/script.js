/* ========================================= 
   SKILLBRIDGE - COMPLETE JAVASCRIPT
   ========================================= */

const API = "https://skillbridge-dka3.onrender.com";

/* =========================================
   NAVIGATION
   ========================================= */

function showSection(sectionId) {
    document.querySelectorAll(".section").forEach(section => {
        section.classList.remove("active");
    });

    const selected = document.getElementById(sectionId);

    if (selected) {
        selected.classList.add("active");
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

/* =========================================
   CREATE RESUME
   ========================================= */

function generateResume() {
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const profile = document.getElementById("profile").value.trim();
    const education = document.getElementById("education").value.trim();
    const skills = document.getElementById("skills").value.trim();
    const projects = document.getElementById("projects").value.trim();
    const experience = document.getElementById("experience").value.trim();

    if (!name) {
        alert("Please enter your name.");
        return;
    }

    const preview = document.getElementById("resumePreview");

    preview.innerHTML = `
        <h1>${escapeHTML(name)}</h1>
        <p>
            ${escapeHTML(email)}
            ${email && phone ? " | " : ""}
            ${escapeHTML(phone)}
        </p>
        <h2>Profile</h2>
        <p>${formatText(profile)}</p>
        <h2>Education</h2>
        <p>${formatText(education)}</p>
        <h2>Skills</h2>
        <p>${formatText(skills)}</p>
        <h2>Projects</h2>
        <p>${formatText(projects)}</p>
        <h2>Experience</h2>
        <p>${formatText(experience)}</p>
    `;

    alert("Resume generated successfully! ✅");
}

/* =========================================
   PRINT / SAVE PDF
   ========================================= */

function printResume() {
    const preview = document.getElementById("resumePreview");

    if (!preview.innerHTML.trim()) {
        alert("First generate your resume.");
        return;
    }

    window.print();
}

/* =========================================
   RESUME ANALYZER
   ========================================= */

async function analyzeResume() {
    const fileInput = document.getElementById("resumeFile");
    const result = document.getElementById("analysisResult");

    if (!fileInput.files.length) {
        result.innerHTML = `
            <p class="error">
                Please select a PDF or TXT resume first.
            </p>
        `;
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    result.innerHTML = "<p>Analyzing your resume... ⏳</p>";

    try {
        const response = await fetch(`${API}/api/analyze-resume`, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            result.innerHTML = `
                <p class="error">${escapeHTML(data.error || "Resume analysis failed.")}</p>
            `;
            return;
        }

        const skillsHTML = data.skills?.length
            ? data.skills.map(skill => `<li>✅ ${escapeHTML(skill)}</li>`).join("")
            : "<li>No recognized skills found.</li>";

        const suggestionsHTML = data.suggestions?.length
            ? data.suggestions.map(item => `<li>${escapeHTML(item)}</li>`).join("")
            : "<li>No major suggestions. 🎉</li>";

        const sections = data.sections || {};

        result.innerHTML = `
            <h3>Resume Score: ${Number(data.score) || 0}/100</h3>

            <div class="result-box">
                <h3>Detected Skills</h3>
                <ul>${skillsHTML}</ul>
            </div>

            <div class="result-box">
                <h3>Resume Sections</h3>
                <p>Email: ${sections.email ? "✅" : "❌"}</p>
                <p>Phone: ${sections.phone ? "✅" : "❌"}</p>
                <p>Education: ${sections.education ? "✅" : "❌"}</p>
                <p>Projects: ${sections.projects ? "✅" : "❌"}</p>
                <p>Experience: ${sections.experience ? "✅" : "❌"}</p>
                <p>Skills: ${sections.skills ? "✅" : "❌"}</p>
            </div>

            <div class="result-box">
                <h3>Suggestions</h3>
                <ul>${suggestionsHTML}</ul>
            </div>
        `;

        void logActivity("resume_analyzer");
    } catch (error) {
        result.innerHTML = `
            <p class="error">Could not connect to SkillBridge server.</p>
            <p>Please try again later.</p>
        `;
        console.error(error);
    }
}

/* =========================================
   LEARNING HUB
   ========================================= */

function findLearningResources() {
    const input = document.getElementById("learningSkill");
    const result = document.getElementById("learningResult");

    if (!input || !result) return;

    const skill = input.value.trim();

    if (!skill) {
        result.innerHTML = `
            <p class="warning">Please enter something you want to learn.</p>
        `;
        return;
    }

    const q = encodeURIComponent(skill);

    result.innerHTML = `
        <h2>📚 Learning Resources for "${escapeHTML(skill)}"</h2>
        <p>Explore books, lectures, courses, projects and practice resources.</p>

        <div class="resource-grid">
            <div class="resource-card">
                <h3>📚 Books & eBooks</h3>
                <p>Find books and eBooks related to ${escapeHTML(skill)}.</p>
                <a href="https://books.google.com/books?q=${q}" target="_blank" rel="noopener noreferrer">Find Books</a>
            </div>

            <div class="resource-card">
                <h3>🎥 YouTube Lectures</h3>
                <p>Find lectures, tutorials and complete video courses.</p>
                <a href="https://www.youtube.com/results?search_query=${q}+lecture+tutorial" target="_blank" rel="noopener noreferrer">Watch Lectures</a>
            </div>

            <div class="resource-card">
                <h3>🎓 NPTEL</h3>
                <p>Search NPTEL courses and university lectures.</p>
                <a href="https://www.google.com/search?q=site%3Anptel.ac.in+${q}" target="_blank" rel="noopener noreferrer">Find NPTEL Courses</a>
            </div>

            <div class="resource-card">
                <h3>🆓 Free Courses</h3>
                <p>Find free courses and learning materials.</p>
                <a href="https://www.google.com/search?q=${q}+free+course" target="_blank" rel="noopener noreferrer">Find Free Courses</a>
            </div>

            <div class="resource-card">
                <h3>🎓 Coursera</h3>
                <p>Find structured courses and professional learning.</p>
                <a href="https://www.google.com/search?q=site%3Acoursera.org+${q}+course" target="_blank" rel="noopener noreferrer">Find Courses</a>
            </div>

            <div class="resource-card">
                <h3>🎓 edX</h3>
                <p>Find university and professional courses.</p>
                <a href="https://www.google.com/search?q=site%3Aedx.org+${q}+course" target="_blank" rel="noopener noreferrer">Find Courses</a>
            </div>

            <div class="resource-card">
                <h3>🆓 freeCodeCamp</h3>
                <p>Find free tutorials and technology courses.</p>
                <a href="https://www.google.com/search?q=site%3Afreecodecamp.org+${q}" target="_blank" rel="noopener noreferrer">Find Resources</a>
            </div>

            <div class="resource-card">
                <h3>📖 GeeksforGeeks</h3>
                <p>Find tutorials, explanations and practice.</p>
                <a href="https://www.google.com/search?q=site%3Ageeksforgeeks.org+${q}" target="_blank" rel="noopener noreferrer">Learn on GFG</a>
            </div>

            <div class="resource-card">
                <h3>💻 GitHub Projects</h3>
                <p>Find projects, source code and practical examples.</p>
                <a href="https://github.com/search?q=${q}&type=repositories" target="_blank" rel="noopener noreferrer">Find Projects</a>
            </div>

            <div class="resource-card">
                <h3>🧪 Kaggle</h3>
                <p>Find datasets, notebooks and practical projects.</p>
                <a href="https://www.google.com/search?q=site%3Akaggle.com+${q}" target="_blank" rel="noopener noreferrer">Explore Kaggle</a>
            </div>

            <div class="resource-card">
                <h3>📘 Official Documentation</h3>
                <p>Find official documentation and references.</p>
                <a href="https://www.google.com/search?q=${q}+official+documentation" target="_blank" rel="noopener noreferrer">Find Documentation</a>
            </div>

            <div class="resource-card">
                <h3>📝 Practice</h3>
                <p>Find exercises, questions and practice problems.</p>
                <a href="https://www.google.com/search?q=${q}+practice+questions" target="_blank" rel="noopener noreferrer">Find Practice</a>
            </div>

            <div class="resource-card">
                <h3>🌐 Web Resources</h3>
                <p>Find articles, tutorials, notes and guides.</p>
                <a href="https://www.google.com/search?q=${q}+tutorial+notes" target="_blank" rel="noopener noreferrer">Search Web</a>
            </div>
        </div>
    `;

    void logActivity("learning_hub");
}



/* =========================================
   COVER LETTER
   ========================================= */

async function generateCoverLetter() {
    const name = document.getElementById("coverName").value.trim();
    const role = document.getElementById("coverRole").value.trim();
    const company = document.getElementById("coverCompany").value.trim();
    const skills = document.getElementById("coverSkills").value.trim();
    const result = document.getElementById("coverResult");

    if (!name || !role || !company) {
        result.innerHTML = `
            <p class="warning">
                Please enter your name, job role and company.
            </p>
        `;
        return;
    }

    const formData = new FormData();
    formData.append("name", name);
    formData.append("role", role);
    formData.append("company", company);
    formData.append("skills", skills);

    result.innerHTML = "<p>Generating cover letter... ⏳</p>";

    try {
        const response = await fetch(`${API}/api/cover-letter`, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok || !data.cover_letter) {
            throw new Error(data.error || data.detail || "Could not generate cover letter.");
        }

        result.innerHTML = `
            <div class="result-box">
                <h3>Your Cover Letter</h3>
                <pre>${escapeHTML(data.cover_letter)}</pre>
            </div>

            <button onclick="copyCoverLetter()">
                📋 Copy Cover Letter
            </button>
        `;

        void logActivity("cover_letter");
    } catch (error) {
        result.innerHTML = `
            <p class="error">${escapeHTML(error.message || "Could not connect to SkillBridge server.")}</p>
        `;
        console.error(error);
    }
}

/* =========================================
   COPY COVER LETTER
   ========================================= */

function copyCoverLetter() {
    const text = document.querySelector("#coverResult pre");

    if (!text) return;

    navigator.clipboard.writeText(text.innerText)
        .then(() => alert("Cover letter copied! ✅"))
        .catch(() => alert("Could not copy. Please select and copy the text manually."));
}

/* =========================================
   HTML SAFETY
   ========================================= */

function escapeHTML(text) {
    if (text === null || text === undefined) return "";

    return String(text)
        .replace(/&/g, "&")
        .replace(/</g, "<")
        .replace(/>/g, ">")
        .replace(/"/g, """)
        .replace(/'/g, "'");
}

/* =========================================
   TEXT FORMATTING
   ========================================= */

function formatText(text) {
    if (!text) return "Not provided";

    return escapeHTML(text).replace(/\n/g, "<br>");
}

/* =========================================
   AUTHENTICATION & ACTIVITY TRACKING
   ========================================= */

const TOKEN_KEY = "skillbridge_access_token";

/*
 * Record feature usage for the Admin Dashboard.
 * Requires a logged-in user.
 * If logging fails, the main feature continues working.
 */

async function logActivity(action) {
    const token = sessionStorage.getItem(TOKEN_KEY);

    if (!token) {
        console.warn("Activity not recorded: user is not logged in.");
        return;
    }

    const allowedActions = [
        "resume_analyzer",
        "cover_letter",
        "learning_hub"
    ];

    if (!allowedActions.includes(action)) return;

    try {
        const response = await fetch(
            `${API}/api/activity?action=${encodeURIComponent(action)}`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            console.warn(
                "Activity was not recorded:",
                action,
                response.status
            );
        }
    } catch (error) {
        console.warn("Activity tracking unavailable:", error);
    }
}

/* =========================================
   REGISTER USER
   ========================================= */

async function registerUser(event) {
    event.preventDefault();

    const name = document.getElementById("registerName").value.trim();
    const email = document.getElementById("registerEmail").value.trim();
    const password = document.getElementById("registerPassword").value;
    const message = document.getElementById("authMessage");

    message.textContent = "Creating account...";

    try {
        const response = await fetch(`${API}/api/users`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name,
                email,
                password
            })
        });

        const data = await response.json();

        if (!response.ok || data.success === false) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : (data.message || "Registration failed. Please check your details.")
            );
        }

        message.textContent = "Account created successfully! Please log in.";

        const form = document.getElementById("registerForm");
        if (form) form.reset();

    } catch (error) {
        message.textContent =
            error.message || "Could not connect to SkillBridge server.";
    }
}

/* =========================================
   LOGIN USER
   ========================================= */

async function loginUser(event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const message = document.getElementById("authMessage");

    message.textContent = "Logging in...";

    try {
        const response = await fetch(`${API}/api/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : "Login failed. Please check your credentials."
            );
        }

        if (!data.access_token) {
            throw new Error("The server did not return an access token.");
        }

        sessionStorage.setItem(TOKEN_KEY, data.access_token);

        const meResponse = await fetch(`${API}/api/me`, {
            headers: {
                Authorization: `Bearer ${data.access_token}`
            }
        });

        if (!meResponse.ok) {
            sessionStorage.removeItem(TOKEN_KEY);
            throw new Error("Could not verify your login. Please try again.");
        }

        showAppContent();

        const loginForm = document.getElementById("loginForm");
        if (loginForm) loginForm.reset();

        message.textContent = "";

    } catch (error) {
        message.textContent =
            error.message || "Could not connect to SkillBridge server.";
    }
}

/* =========================================
   SHOW APP AFTER LOGIN
   ========================================= */

function showAppContent() {
    const authSection = document.getElementById("authSection");
    const appContent = document.getElementById("appContent");

    if (authSection) authSection.style.display = "none";
    if (appContent) appContent.style.display = "block";
}

/* =========================================
   LOGOUT USER
   ========================================= */

function logoutUser() {
    sessionStorage.removeItem(TOKEN_KEY);

    const appContent = document.getElementById("appContent");
    const authSection = document.getElementById("authSection");
    const message = document.getElementById("authMessage");

    if (appContent) appContent.style.display = "none";
    if (authSection) authSection.style.display = "block";
    if (message) message.textContent = "You have logged out.";
}

/* =========================================
   CHECK LOGIN SESSION
   ========================================= */

async function checkLoginSession() {
    const token = sessionStorage.getItem(TOKEN_KEY);

    const authSection = document.getElementById("authSection");
    const appContent = document.getElementById("appContent");
    const message = document.getElementById("authMessage");

    if (!token) {
        if (authSection) authSection.style.display = "block";
        if (appContent) appContent.style.display = "none";
        return;
    }

    try {
        const response = await fetch(`${API}/api/me`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (response.ok) {
            showAppContent();
        } else {
            sessionStorage.removeItem(TOKEN_KEY);

            if (authSection) authSection.style.display = "block";
            if (appContent) appContent.style.display = "none";
        }
    } catch (error) {
        if (authSection) authSection.style.display = "block";
        if (appContent) appContent.style.display = "none";

        if (message) {
            message.textContent =
                "Could not connect to SkillBridge. Please try again.";
        }
    }
}

/* =========================================
   INITIALIZE
   ========================================= */

document.addEventListener("DOMContentLoaded", checkLoginSession);
