/* =========================================
   CAREERMATE - COMPLETE JAVASCRIPT
   ========================================= */

const API = "https://skillbridge-dka3.onrender.com";

/* =========================================
   NAVIGATION
   ========================================= */

function showSection(sectionId) {

    const sections = document.querySelectorAll(".section");

    sections.forEach(section => {
        section.classList.remove("active");
    });

    const selected = document.getElementById(sectionId);

    if (selected) {
        selected.classList.add("active");
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
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

    const preview =
        document.getElementById("resumePreview");

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

    const fileInput =
        document.getElementById("resumeFile");

    const result =
        document.getElementById("analysisResult");

    if (!fileInput.files.length) {

        result.innerHTML = `
            <p class="error">
                Please select a PDF or TXT resume first.
            </p>
        `;

        return;
    }

    const file = fileInput.files[0];

    const formData = new FormData();

    formData.append("file", file);

    result.innerHTML = `
        <p>Analyzing your resume... ⏳</p>
    `;

    try {

        const response = await fetch(
            `${API}/api/analyze-resume`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (data.error) {

            result.innerHTML = `
                <p class="error">
                    ${escapeHTML(data.error)}
                </p>
            `;

            return;
        }

        let skillsHTML = "";

        if (data.skills && data.skills.length > 0) {

            skillsHTML = data.skills
                .map(skill =>
                    `<li>✅ ${escapeHTML(skill)}</li>`
                )
                .join("");

        } else {

            skillsHTML =
                "<li>No recognized skills found.</li>";
        }


        let suggestionsHTML = "";

        if (data.suggestions && data.suggestions.length > 0) {

            suggestionsHTML = data.suggestions
                .map(item =>
                    `<li>${escapeHTML(item)}</li>`
                )
                .join("");

        } else {

            suggestionsHTML =
                "<li>No major suggestions. 🎉</li>";
        }


        result.innerHTML = `

            <h3>Resume Score: ${data.score}/100</h3>

            <div class="result-box">

                <h3>Detected Skills</h3>

                <ul>
                    ${skillsHTML}
                </ul>

            </div>

            <div class="result-box">

                <h3>Resume Sections</h3>

                <p>
                    Email:
                    ${data.sections.email ? "✅" : "❌"}
                </p>

                <p>
                    Phone:
                    ${data.sections.phone ? "✅" : "❌"}
                </p>

                <p>
                    Education:
                    ${data.sections.education ? "✅" : "❌"}
                </p>

                <p>
                    Projects:
                    ${data.sections.projects ? "✅" : "❌"}
                </p>

                <p>
                    Experience:
                    ${data.sections.experience ? "✅" : "❌"}
                </p>

                <p>
                    Skills:
                    ${data.sections.skills ? "✅" : "❌"}
                </p>

            </div>

            <div class="result-box">

                <h3>Suggestions</h3>

                <ul>
                    ${suggestionsHTML}
                </ul>

            </div>
        `;

    } catch (error) {

        result.innerHTML = `
            <p class="error">
                Could not connect to CareerMate server.
            </p>

            <p>
                Make sure the FastAPI server is running.
            </p>
        `;

        console.error(error);
    }
}


/* =========================================
   LEARNING HUB
   ========================================= */

function findLearningResources() {

    const input =
        document.getElementById("learningSkill");

    const result =
        document.getElementById("learningResult");

    if (!input || !result) {
        return;
    }

    const skill = input.value.trim();

    if (!skill) {

        result.innerHTML = `
            <p class="warning">
                Please enter something you want to learn.
            </p>
        `;

        return;
    }

    const q = encodeURIComponent(skill);

    result.innerHTML = `

        <h2>
            📚 Learning Resources for
            "${escapeHTML(skill)}"
        </h2>

        <p>
            Explore books, lectures, courses,
            projects and practice resources.
        </p>


        <div class="resource-grid">


            <!-- GOOGLE BOOKS -->

            <div class="resource-card">

                <h3>📚 Books & eBooks</h3>

                <p>
                    Find books and eBooks related to
                    ${escapeHTML(skill)}.
                </p>

                <a
                    href="https://books.google.com/books?q=${q}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Find Books
                </a>

            </div>


            <!-- YOUTUBE -->

            <div class="resource-card">

                <h3>🎥 YouTube Lectures</h3>

                <p>
                    Find lectures, tutorials and
                    complete video courses.
                </p>

                <a
                    href="https://www.youtube.com/results?search_query=${q}+lecture+tutorial"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Watch Lectures
                </a>

            </div>


            <!-- NPTEL -->

            <div class="resource-card">

                <h3>🎓 NPTEL</h3>

                <p>
                    Search NPTEL courses and
                    university lectures.
                </p>

                <a
                    href="https://www.google.com/search?q=site%3Anptel.ac.in+${q}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Find NPTEL Courses
                </a>

            </div>


            <!-- FREE COURSES -->

            <div class="resource-card">

                <h3>🆓 Free Courses</h3>

                <p>
                    Find free courses and learning
                    materials.
                </p>

                <a
                    href="https://www.google.com/search?q=${q}+free+course"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Find Free Courses
                </a>

            </div>


            <!-- COURSERA -->

            <div class="resource-card">

                <h3>🎓 Coursera</h3>

                <p>
                    Find structured courses and
                    professional learning.
                </p>

                <a
                    href="https://www.google.com/search?q=site%3Acoursera.org+${q}+course"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Find Courses
                </a>

            </div>


            <!-- EDX -->

            <div class="resource-card">

                <h3>🎓 edX</h3>

                <p>
                    Find university and professional
                    courses.
                </p>

                <a
                    href="https://www.google.com/search?q=site%3Aedx.org+${q}+course"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Find edX Courses
                </a>

            </div>


            <!-- FREECODECAMP -->

            <div class="resource-card">

                <h3>🆓 freeCodeCamp</h3>

                <p>
                    Find free tutorials and
                    technology courses.
                </p>

                <a
                    href="https://www.google.com/search?q=site%3Afreecodecamp.org+${q}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Find Resources
                </a>

            </div>


            <!-- GEEKSFORGEEKS -->

            <div class="resource-card">

                <h3>📖 GeeksforGeeks</h3>

                <p>
                    Find tutorials, explanations
                    and practice.
                </p>

                <a
                    href="https://www.google.com/search?q=site%3Ageeksforgeeks.org+${q}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Learn on GFG
                </a>

            </div>


            <!-- GITHUB -->

            <div class="resource-card">

                <h3>💻 GitHub Projects</h3>

                <p>
                    Find projects, source code
                    and practical examples.
                </p>

                <a
                    href="https://github.com/search?q=${q}&type=repositories"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Find Projects
                </a>

            </div>


            <!-- KAGGLE -->

            <div class="resource-card">

                <h3>🧪 Kaggle</h3>

                <p>
                    Find datasets, notebooks
                    and practical projects.
                </p>

                <a
                    href="https://www.google.com/search?q=site%3Akaggle.com+${q}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Explore Kaggle
                </a>

            </div>


            <!-- DOCUMENTATION -->

            <div class="resource-card">

                <h3>📘 Official Documentation</h3>

                <p>
                    Find official documentation
                    and references.
                </p>

                <a
                    href="https://www.google.com/search?q=${q}+official+documentation"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Find Documentation
                </a>

            </div>


            <!-- PRACTICE -->

            <div class="resource-card">

                <h3>📝 Practice</h3>

                <p>
                    Find exercises, questions
                    and practice problems.
                </p>

                <a
                    href="https://www.google.com/search?q=${q}+practice+questions"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Find Practice
                </a>

            </div>


            <!-- WEB RESOURCES -->

            <div class="resource-card">

                <h3>🌐 Web Resources</h3>

                <p>
                    Find articles, tutorials,
                    notes and guides.
                </p>

                <a
                    href="https://www.google.com/search?q=${q}+tutorial+notes"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Search Web
                </a>

            </div>

        </div>
    `;
}


/* =========================================
   COVER LETTER
   ========================================= */

async function generateCoverLetter() {

    const name =
        document.getElementById("coverName").value.trim();

    const role =
        document.getElementById("coverRole").value.trim();

    const company =
        document.getElementById("coverCompany").value.trim();

    const skills =
        document.getElementById("coverSkills").value.trim();

    const result =
        document.getElementById("coverResult");


    if (!name || !role || !company) {

        result.innerHTML = `
            <p class="warning">
                Please enter your name, job role
                and company.
            </p>
        `;

        return;
    }


    const formData = new FormData();

    formData.append("name", name);
    formData.append("role", role);
    formData.append("company", company);
    formData.append("skills", skills);


    result.innerHTML =
        "<p>Generating cover letter... ⏳</p>";


    try {

        const response = await fetch(
            `${API}/api/cover-letter`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();


        result.innerHTML = `

            <div class="result-box">

                <h3>Your Cover Letter</h3>

                <pre>${escapeHTML(
                    data.cover_letter
                )}</pre>

            </div>

            <button onclick="copyCoverLetter()">
                📋 Copy Cover Letter
            </button>
        `;

    } catch (error) {

        result.innerHTML = `
            <p class="error">
                Could not connect to CareerMate server.
            </p>
        `;

        console.error(error);
    }
}


/* =========================================
   COPY COVER LETTER
   ========================================= */

function copyCoverLetter() {

    const text =
        document.querySelector("#coverResult pre");

    if (!text) {
        return;
    }

    navigator.clipboard.writeText(
        text.innerText
    );

    alert("Cover letter copied! ✅");
}


/* =========================================
   HTML SAFETY
   ========================================= */

function escapeHTML(text) {

    if (!text) {
        return "";
    }

    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


/* =========================================
   TEXT FORMATTING
   ========================================= */

function formatText(text) {

    if (!text) {
        return "Not provided";
    }

    return escapeHTML(text)
        .replace(/\n/g, "<br>");
}



const TOKEN_KEY = "skillbridge_access_token";

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
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Registration failed.");
        }

        message.textContent = "Account created successfully! Please log in.";
        document.getElementById("registerForm").reset();
    } catch (error) {
        message.textContent = error.message || "Could not connect to the server.";
    }
}

async function loginUser(event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const message = document.getElementById("authMessage");

    message.textContent = "Logging in...";

    try {
        const response = await fetch(`${API}/api/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Login failed.");
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
        document.getElementById("loginForm").reset();
        message.textContent = "";
    } catch (error) {
        message.textContent = error.message || "Could not connect to the server.";
    }
}

function showAppContent() {
    document.getElementById("authSection").style.display = "none";
    document.getElementById("appContent").style.display = "block";
}

function logoutUser() {
    sessionStorage.removeItem(TOKEN_KEY);

    document.getElementById("appContent").style.display = "none";
    document.getElementById("authSection").style.display = "block";
    document.getElementById("authMessage").textContent = "You have logged out.";
}

async function checkLoginSession() {
    const token = sessionStorage.getItem(TOKEN_KEY);

    if (!token) {
        document.getElementById("authSection").style.display = "block";
        document.getElementById("appContent").style.display = "none";
        return;
    }

    try {
        const response = await fetch(`${API}/api/me`, {
            headers: { Authorization: `Bearer ${token}` }
        });

        if (response.ok) {
            showAppContent();
        } else {
            sessionStorage.removeItem(TOKEN_KEY);
            document.getElementById("authSection").style.display = "block";
            document.getElementById("appContent").style.display = "none";
        }
    } catch (error) {
        document.getElementById("authSection").style.display = "block";
        document.getElementById("appContent").style.display = "none";
        document.getElementById("authMessage").textContent =
            "Could not connect to SkillBridge. Please try again.";
    }
}

document.addEventListener("DOMContentLoaded", checkLoginSession);



async function registerUser(event) {
    event.preventDefault();

    const message = document.getElementById("authMessage");

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
                    : "Registration failed. Please check your details."
            );
        }

        message.textContent = "Account created! Please log in.";
        document.getElementById("registerForm").reset();

    } catch (error) {
        message.textContent = error.message || "Could not connect to server.";
    }
}
