/* =========================================
   SKILLBRIDGE - COMPLETE JAVASCRIPT
   ========================================= */

const API = "https://skillbridge-dka3.onrender.com";
const TOKEN_KEY = "skillbridge_access_token";

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
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    } else {
        console.warn("Section not found:", sectionId);
    }
}

/* =========================================
   HTML SAFETY HELPERS
   ========================================= */

function escapeHTML(text) {
    if (text === null || text === undefined) {
        return "";
    }

    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatText(text) {
    if (!text) return "Not provided";

    return escapeHTML(text).replace(/\r?\n/g, "<br>");
}

function getValue(id) {
    return document.getElementById(id)?.value?.trim() || "";
}

/* =========================================
   RESUME PHOTO UPLOAD AND PREVIEW
   ========================================= */

let resumePhotoData = "";

document.addEventListener("DOMContentLoaded", () => {
    const photoInput = document.getElementById("resumePhoto");
    const photoPreview = document.getElementById("resumePhotoPreview");

    if (photoInput && photoPreview) {
        photoInput.addEventListener("change", function () {
            const file = this.files && this.files[0];

            if (!file) {
                resumePhotoData = "";
                photoPreview.removeAttribute("src");
                photoPreview.style.display = "none";
                return;
            }

            if (!file.type.startsWith("image/")) {
                alert("Please select an image file.");
                this.value = "";
                return;
            }

            if (file.size > 5 * 1024 * 1024) {
                alert("Photo size must be less than 5 MB.");
                this.value = "";
                return;
            }

            const reader = new FileReader();

            reader.onload = event => {
                resumePhotoData = event.target.result;
                photoPreview.src = resumePhotoData;
                photoPreview.style.display = "block";
            };

            reader.onerror = () => {
                alert("Could not read the selected photo.");
            };

            reader.readAsDataURL(file);
        });
    }

    loadResumeData();
    loadProfile();
    checkLoginSession();
});


/* =========================================
   RESUME BUILDER
   ========================================= */

function generateResume() {
    const fields = {
        name: getValue("name"),
        email: getValue("email"),
        phone: getValue("phone"),
        location: getValue("location"),
        linkedin: getValue("linkedin"),
        profile: getValue("profile"),
        education: getValue("education"),
        skills: getValue("skills"),
        experience: getValue("experience"),
        projects: getValue("projects"),
        certifications: getValue("certifications"),
        achievements: getValue("achievements"),
        additional: getValue("additional")
    };

    if (!fields.name) {
        alert("Please enter your name.");
        document.getElementById("name")?.focus();
        return;
    }

    const preview = document.getElementById("resumePreview");

    if (!preview) {
        alert("Resume preview area was not found.");
        return;
    }

    const section = (title, value) => {
        if (!value) return "";

        return `
            <section class="resume-section">
                <h2>${escapeHTML(title)}</h2>
                <p>${formatText(value)}</p>
            </section>
        `;
    };

    const template =
        document.getElementById("resumeTemplate")?.value || "modern";

    const color =
        document.getElementById("resumeColor")?.value || "#2563eb";

    const font =
        document.getElementById("resumeFont")?.value || "Arial";

    const fontSize =
        document.getElementById("resumeFontSize")?.value || "14px";

    const allowedFonts = {
        "Arial": "Arial, sans-serif",
        "Georgia": "Georgia, serif",
        "Verdana": "Verdana, sans-serif",
        "Tahoma": "Tahoma, sans-serif",
        "Roboto": "Roboto, Arial, sans-serif",
        "Times New Roman": '"Times New Roman", serif'
    };

    const allowedSizes = ["12px", "14px", "16px"];

    preview.className = `resume-document template-${template}`;
    preview.style.setProperty("--resume-color", color);
    preview.style.fontFamily = allowedFonts[font] || "Arial, sans-serif";
    preview.style.fontSize = allowedSizes.includes(fontSize)
        ? fontSize
        : "14px";

    const photo = document.getElementById("resumePhotoPreview");
    const photoHTML = resumePhotoData
        ? `<img class="resume-photo"
                src="${resumePhotoData}"
                alt="Profile photo">`
        : (photo?.src && photo.style.display !== "none"
            ? `<img class="resume-photo"
                    src="${escapeHTML(photo.src)}"
                    alt="Profile photo">`
            : "");

    preview.innerHTML = `
        <article class="generated-resume">
            <header class="resume-header">
                ${photoHTML}
                <div>
                    <h1>${escapeHTML(fields.name)}</h1>
                    <p class="resume-contact">
                        ${[
                            fields.email,
                            fields.phone,
                            fields.location
                        ].filter(Boolean).map(escapeHTML).join(" | ")}
                    </p>
                    ${fields.linkedin
                        ? `<p>${escapeHTML(fields.linkedin)}</p>`
                        : ""}
                </div>
            </header>

            ${section("Professional Profile", fields.profile)}
            ${section("Education", fields.education)}
            ${section("Skills", fields.skills)}
            ${section("Work Experience / Internship", fields.experience)}
            ${section("Projects", fields.projects)}
            ${section("Certifications", fields.certifications)}
            ${section("Achievements", fields.achievements)}
            ${section("Additional Information", fields.additional)}
        </article>
    `;

    applyResumeTemplate();
    customizeResume();
    saveResumeData(false);

    preview.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

/* Update preview when the profile photo changes */
document.getElementById("resumePhoto")?.addEventListener("change", event => {
    const file = event.target.files?.[0];
    const image = document.getElementById("resumePhotoPreview");

    if (!file || !image) return;

    if (!file.type.startsWith("image/")) {
        alert("Please select an image file.");
        event.target.value = "";
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        alert("Photo size must be less than 5 MB.");
        event.target.value = "";
        return;
    }

    const reader = new FileReader();

    reader.onload = event => {
        resumePhotoData = event.target.result;
        image.src = resumePhotoData;
        image.style.display = "block";
    };

    reader.onerror = () => alert("Could not read the selected photo.");

    reader.readAsDataURL(file);
});

/* =========================================
   RESUME TEMPLATES
   ========================================= */

function applyResumeTemplate() {
    const preview = document.getElementById("resumePreview");
    const selector = document.getElementById("resumeTemplate");

    if (!preview) return;

    const templates = [
        "modern",
        "professional",
        "minimal",
        "creative",
        "classic",
        "elegant"
    ];

    const selected = selector?.value || "modern";

    templates.forEach(template => {
        preview.classList.remove(`template-${template}`);
    });

    const validTemplate = templates.includes(selected)
        ? selected
        : "modern";

    preview.classList.add(`template-${validTemplate}`);
}

/* =========================================
   RESUME CUSTOMIZATION
   ========================================= */

function customizeResume() {
    const preview = document.getElementById("resumePreview");

    if (!preview) return;

    const color = document.getElementById("resumeColor")?.value;
    const font = document.getElementById("resumeFont")?.value;
    const fontSize = document.getElementById("resumeFontSize")?.value;

    if (color && /^#[0-9a-f]{6}$/i.test(color)) {
        preview.style.setProperty("--resume-color", color);
    }

    const allowedFonts = {
        "Arial": "Arial, sans-serif",
        "Georgia": "Georgia, serif",
        "Roboto": "Roboto, Arial, sans-serif",
        "Times New Roman": '"Times New Roman", serif'
    };

    if (font && allowedFonts[font]) {
        preview.style.fontFamily = allowedFonts[font];
    }

    if (fontSize) {
        const size = Number(fontSize);

        if (size >= 10 && size <= 20) {
            preview.style.fontSize = `${size}px`;
        }
    }
}

/* =========================================
   SAVE AND LOAD RESUME DATA
   ========================================= */


function saveResumeData(showMessage = true) {
    const ids = [
        "name",
        "email",
        "phone",
        "location",
        "linkedin",
        "profile",
        "education",
        "skills",
        "projects",
        "experience",
        "certifications",
        "achievements",
        "additional"
    ];

    const resumeData = {};

    ids.forEach(id => {
        const input = document.getElementById(id);

        if (input) {
            resumeData[id] = input.value;
        }
    });

    // Save resume photo
    if (resumePhotoData) {
        resumeData.resumePhotoData = resumePhotoData;
    }

    try {
        localStorage.setItem(
            "skillbridge_resume_data",
            JSON.stringify(resumeData)
        );

        if (showMessage) {
            alert("Resume saved on this device.");
        }
    } catch (error) {
        console.error("Could not save resume:", error);

        if (showMessage) {
            alert(
                "Could not save resume. The photo may be too large " +
                "for browser storage."
            );
        }
    }
}


function loadResumeData() {
    try {
        const saved = localStorage.getItem("skillbridge_resume_data");

        if (!saved) return;

        const resumeData = JSON.parse(saved);

        Object.entries(resumeData).forEach(([id, value]) => {
            // Restore resume photo
            if (id === "resumePhotoData") {
                resumePhotoData =
                    typeof value === "string" ? value : "";

                const photoPreview =
                    document.getElementById("resumePhotoPreview");

                if (photoPreview && resumePhotoData) {
                    photoPreview.src = resumePhotoData;
                    photoPreview.style.display = "block";
                }

                return;
            }

            // Restore all resume fields, including new fields
            const input = document.getElementById(id);

            if (input && typeof value === "string") {
                input.value = value;
            }
        });

    } catch (error) {
        console.error("Could not load saved resume:", error);
    }
}

function resetResume() {
    if (!confirm("Are you sure you want to reset your resume?")) {
        return;
    }

    const ids = [
        "name",
        "email",
        "phone",
        "location",
        "linkedin",
        "profile",
        "education",
        "skills",
        "projects",
        "experience",
        "certifications",
        "achievements",
        "additional"
    ];

    ids.forEach(id => {
        const input = document.getElementById(id);

        if (input) {
            input.value = "";
        }
    });

    // Reset resume photo
    resumePhotoData = "";

    const photoInput = document.getElementById("resumePhoto");
    const photoPreview = document.getElementById("resumePhotoPreview");

    if (photoInput) {
        photoInput.value = "";
    }

    if (photoPreview) {
        photoPreview.removeAttribute("src");
        photoPreview.style.display = "none";
    }

    // Clear resume preview
    const preview = document.getElementById("resumePreview");

    if (preview) {
        preview.innerHTML = "";

        preview.className = preview.className
            .split(/\s+/)
            .filter(name => !name.startsWith("template-"))
            .join(" ");

        preview.style.removeProperty("--resume-color");
        preview.style.removeProperty("font-family");
        preview.style.removeProperty("font-size");
    }

    // Reset customization controls
    ["resumeTemplate", "resumeColor", "resumeFont", "resumeFontSize"]
        .forEach(id => {
            const control = document.getElementById(id);

            if (control) {
                control.selectedIndex = 0;
            }
        });

    // Remove saved resume data
    localStorage.removeItem("skillbridge_resume_data");

    alert("Resume has been reset successfully!");
}

/* =========================================
   PRINT / SAVE RESUME AS PDF
   ========================================= */

function printResume() {
    const preview = document.getElementById("resumePreview");

    if (!preview || !preview.innerText.trim()) {
        alert("Please generate your resume first.");
        return;
    }

    const photo = preview.querySelector(".resume-photo");

    if (photo && !photo.complete) {
        photo.onload = () => window.print();
        photo.onerror = () => window.print();
        return;
    }

    window.print();
}

/* =========================================
   RESUME ANALYZER
   TXT ANALYSIS
   ========================================= */



async function extractResumeText(file) {
    const extension = file.name.split(".").pop().toLowerCase();

    if (extension === "txt") {
        return await file.text();
    }

    if (extension === "pdf") {
        if (typeof pdfjsLib === "undefined") {
            throw new Error("PDF reader load হয়নি। Internet connection পরীক্ষা করো।");
        }

        const buffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({
            data: new Uint8Array(buffer)
        }).promise;

        let fullText = "";

        for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
            const page = await pdf.getPage(pageNumber);
            const content = await page.getTextContent();

            fullText += content.items
                .map(item => item.str || "")
                .join(" ") + "\n";
        }

        if (!fullText.trim()) {
            throw new Error(
                "PDF থেকে text পাওয়া যায়নি। এটি scanned PDF হলে OCR প্রয়োজন।"
            );
        }

        return fullText;
    }

    throw new Error("শুধুমাত্র PDF অথবা TXT file upload করো।");
}





async function analyzeResume() {
    const fileInput = document.getElementById("analyzerFile");
    const result = document.getElementById("analyzerResult");
    const jobInput = document.getElementById("jobDescription");

    if (!fileInput || !result) {
        console.error("Resume Analyzer HTML elements not found.");
        return;
    }

    const file = fileInput.files[0];

    if (!file) {
        result.textContent = "Please upload your resume first.";
        return;
    }

    if (!file.name.toLowerCase().endsWith(".txt")) {
        result.textContent =
            "This version supports TXT files only. PDF support requires a PDF parser.";
        return;
    }

    if (file.size > 2 * 1024 * 1024) {
        result.textContent = "Please upload a TXT file smaller than 2 MB.";
        return;
    }

    result.textContent = "Analyzing your resume...";

    try {
         const text = await extractResumeText(file);
        const content = text.toLowerCase();

        if (!content.trim()) {
            result.textContent = "The uploaded file is empty.";
            return;
        }

        const sections = {
            "Education": /\beducation\b|\bdegree\b|\bcollege\b|\buniversity\b/.test(content),
            "Skills": /\bskills?\b|\btechnologies\b/.test(content),
            "Projects": /\bprojects?\b/.test(content),
            "Experience": /\bexperience\b|\binternship\b|\bemployment\b/.test(content),
            "Contact Information": /@|\bphone\b|\bmobile\b/.test(content),
            "Certifications": /\bcertifications?\b|\bcertificates?\b/.test(content)
        };

        const skillList = [
            "python", "java", "javascript", "html", "css", "sql",
            "c++", "machine learning", "data science", "excel",
            "react", "node.js", "git", "aws", "fastapi"
        ];

        const detectedSkills = skillList.filter(skill =>
            content.includes(skill)
        );

        const total = Object.keys(sections).length;
        const present = Object.values(sections).filter(Boolean).length;
        const score = Math.round((present / total) * 100);

        result.replaceChildren();

        const heading = document.createElement("h3");
        heading.textContent = "Resume Analysis Report";
        result.appendChild(heading);

        const scoreHeading = document.createElement("h2");
        scoreHeading.textContent = `Basic Section Score: ${score}/100`;
        result.appendChild(scoreHeading);

        const note = document.createElement("p");
        note.textContent =
            "This score checks for common resume sections only. It is not an official ATS score or a prediction of hiring success.";
        result.appendChild(note);

        const sectionHeading = document.createElement("h3");
        sectionHeading.textContent = "Section Check";
        result.appendChild(sectionHeading);

        const sectionList = document.createElement("ul");

        Object.entries(sections).forEach(([name, found]) => {
            const li = document.createElement("li");
            li.textContent = `${found ? "✅" : "⚠️"} ${name}: ${found ? "Found" : "Missing"}`;
            sectionList.appendChild(li);
        });

        result.appendChild(sectionList);

        const skillHeading = document.createElement("h3");
        skillHeading.textContent = "Detected Skills";
        result.appendChild(skillHeading);

        const skillText = document.createElement("p");
        skillText.textContent = detectedSkills.length
            ? detectedSkills.join(", ")
            : "No matching skills detected.";
        result.appendChild(skillText);

        const suggestionHeading = document.createElement("h3");
        suggestionHeading.textContent = "Suggestions";
        result.appendChild(suggestionHeading);

        const suggestions = document.createElement("ul");
        Object.entries(sections)
            .filter(([, found]) => !found)
            .forEach(([name]) => {
                const li = document.createElement("li");
                li.textContent = `Consider adding a ${name} section if relevant.`;
                suggestions.appendChild(li);
            });

        [
            "Use clear headings and consistent formatting.",
            "Check spelling, dates and contact details.",
            "Describe your contribution and results in project entries."
        ].forEach(tip => {
            const li = document.createElement("li");
            li.textContent = tip;
            suggestions.appendChild(li);
        });

        result.appendChild(suggestions);

        const jobText = jobInput?.value.trim().toLowerCase() || "";

        if (jobText) {
            const words = jobText.match(/\b[a-z][a-z+#.-]{2,}\b/g) || [];
            const stopWords = new Set([
                "the", "and", "for", "with", "you", "our", "are",
                "will", "this", "that", "from", "your", "have",
                "has", "who", "job", "role", "work"
            ]);

            const keywords = [...new Set(words)].filter(word =>
                !stopWords.has(word)
            );

            const matched = keywords.filter(word => content.includes(word));
            const missing = keywords.filter(word => !content.includes(word));

            const jobHeading = document.createElement("h3");
            jobHeading.textContent = "Job Description Keyword Comparison";
            result.appendChild(jobHeading);

            const jobResult = document.createElement("p");
            jobResult.textContent =
                `Matched keywords: ${matched.length}. Keywords to review: ${missing.length}.`;
            result.appendChild(jobResult);

            const missingText = document.createElement("p");
            missingText.textContent =
                "Keywords not detected: " + (missing.slice(0, 25).join(", ") || "None");
            result.appendChild(missingText);
        }

        window.lastResumeAnalysis = {
            filename: file.name,
            score,
            sections,
            detectedSkills
        };

        const downloadButton = document.createElement("button");
        downloadButton.type = "button";
        downloadButton.textContent = "Download Analysis Report";
        downloadButton.addEventListener("click", downloadAnalysisReport);
        result.appendChild(downloadButton);

        if (typeof logActivity === "function") {
            void logActivity("resume_analyzer");
        }

    } catch (error) {
        console.error("Resume analysis failed:", error);
        result.textContent = "Unable to analyze the file. Please try again.";
    }
}


/* =========================================
   DOWNLOAD ANALYSIS REPORT
   ========================================= */

function downloadAnalysisReport() {
    const report = window.lastResumeAnalysis;

    if (!report) {
        alert("Analyze a TXT resume first.");
        return;
    }

    const lines = [
        "SkillBridge - Resume Analysis Report",
        `Filename: ${report.filename}`,
        `Basic Section Score: ${report.score}/100`,
        "",
        "Sections:"
    ];

    Object.entries(report.sections).forEach(([name, found]) => {
        lines.push(`${name}: ${found ? "Found" : "Missing"}`);
    });

    lines.push(
        "",
        "Detected Skills:",
        report.detectedSkills.join(", ") || "None detected",
        "",
        "Note: This is a basic section-presence score, not an ATS score."
    );

    const blob = new Blob(
        [lines.join("\n")],
        { type: "text/plain;charset=utf-8" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "skillbridge-resume-analysis.txt";
    link.click();

    URL.revokeObjectURL(url);
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
            <p class="warning">
                Please enter something you want to learn.
            </p>
        `;
        return;
    }

    const q = encodeURIComponent(skill);

    const resources = [
        [
            "📚 Books & eBooks",
            "Find books and eBooks related to this topic.",
            `https://books.google.com/books?q=${q}`,
            "Find Books"
        ],
        [
            "🎥 YouTube Lectures",
            "Find lectures and complete video courses.",
            `https://www.youtube.com/results?search_query=${q}+lecture+tutorial`,
            "Watch Lectures"
        ],
        [
            "🎓 NPTEL",
            "Search NPTEL courses and university lectures.",
            `https://www.google.com/search?q=site%3Anptel.ac.in+${q}`,
            "Find NPTEL Courses"
        ],
        [
            "🆓 Free Courses",
            "Find free courses and learning materials.",
            `https://www.google.com/search?q=${q}+free+course`,
            "Find Free Courses"
        ],
        [
            "🎓 Coursera",
            "Find structured courses and professional learning.",
            `https://www.google.com/search?q=site%3Acoursera.org+${q}+course`,
            "Find Courses"
        ],
        [
            "🎓 edX",
            "Find university and professional courses.",
            `https://www.google.com/search?q=site%3Aedx.org+${q}+course`,
            "Find Courses"
        ],
        [
            "🆓 freeCodeCamp",
            "Find free tutorials and technology courses.",
            `https://www.google.com/search?q=site%3Afreecodecamp.org+${q}`,
            "Find Resources"
        ],
        [
            "📖 GeeksforGeeks",
            "Find tutorials and practice resources.",
            `https://www.google.com/search?q=site%3Ageeksforgeeks.org+${q}`,
            "Learn on GFG"
        ],
        [
            "💻 GitHub Projects",
            "Find projects and source code.",
            `https://github.com/search?q=${q}&type=repositories`,
            "Find Projects"
        ],
        [
            "🧪 Kaggle",
            "Find datasets and practical projects.",
            `https://www.google.com/search?q=site%3Akaggle.com+${q}`,
            "Explore Kaggle"
        ],
        [
            "📘 Documentation",
            "Find official documentation and references.",
            `https://www.google.com/search?q=${q}+official+documentation`,
            "Find Documentation"
        ],
        [
            "📝 Practice",
            "Find exercises and practice problems.",
            `https://www.google.com/search?q=${q}+practice+questions`,
            "Find Practice"
        ],
        [
            "🌐 Web Resources",
            "Find articles, tutorials, notes and guides.",
            `https://www.google.com/search?q=${q}+tutorial+notes`,
            "Search Web"
        ]
    ];

    result.innerHTML = `
        <h2>
            📚 Learning Resources for "${escapeHTML(skill)}"
        </h2>

        <p>
            Explore books, lectures, courses, projects and practice resources.
        </p>

        <div class="resource-grid">

            ${resources.map(([title, description, url, label]) => `
                <div class="resource-card">
                    <h3>${escapeHTML(title)}</h3>

                    <p>${escapeHTML(description)}</p>

                    <a
                        href="${url}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        ${escapeHTML(label)}
                    </a>
                </div>
            `).join("")}

        </div>
    `;

    void logActivity("learning_hub");
}

/* =========================================
   PROFILE
   Saves data in this browser
   ========================================= */

function saveProfile() {
    const profile = {
        name: getValue("profileName"),
        email: getValue("profileEmail"),
        education: getValue("profileEducation"),
        skills: getValue("profileSkills")
    };

    if (!profile.name) {
        alert("Please enter your name.");
        return;
    }

    try {
        localStorage.setItem(
            "skillbridge_profile",
            JSON.stringify(profile)
        );

        const message = document.getElementById("profileMessage");

        if (message) {
            message.textContent = "Profile saved in this browser.";
            message.className = "success";
        }

    } catch (error) {
        alert("Unable to save your profile in this browser.");
        console.error(error);
    }
}

function loadProfile() {
    try {
        const stored = localStorage.getItem("skillbridge_profile");

        if (!stored) return;

        const profile = JSON.parse(stored);

        const fields = {
            profileName: profile.name,
            profileEmail: profile.email,
            profileEducation: profile.education,
            profileSkills: profile.skills
        };

        Object.entries(fields).forEach(([id, value]) => {
            const element = document.getElementById(id);

            if (element && typeof value === "string") {
                element.value = value;
            }
        });

    } catch (error) {
        console.error("Could not load profile:", error);
    }
}

/* =========================================
   ACTIVITY TRACKING
   ========================================= */

async function logActivity(action) {
    const token = sessionStorage.getItem(TOKEN_KEY);

    if (!token) return;

    const allowedActions = [
        "resume_analyzer",
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
   REGISTRATION
   Requires matching backend endpoint
   ========================================= */

async function registerUser(event) {
    event.preventDefault();

    const name = getValue("registerName");
    const email = getValue("registerEmail");

    const password =
        document.getElementById("registerPassword")?.value || "";

    const message = document.getElementById("authMessage");

    if (message) {
        message.textContent = "Creating account...";
        message.className = "";
    }

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

        const data = await response.json().catch(() => ({}));

        if (!response.ok || data.success === false) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : (
                        data.message ||
                        "Registration failed. Please check your details."
                    )
            );
        }

        if (message) {
            message.textContent =
                "Account created successfully! Please log in.";

            message.className = "success";
        }

        document.getElementById("registerForm")?.reset();

    } catch (error) {
        if (message) {
            message.textContent =
                error.message ||
                "Could not connect to SkillBridge server.";

            message.className = "error";
        }
    }
}

/* =========================================
   LOGIN
   Requires /api/login and /api/me
   ========================================= */

async function loginUser(event) {
    event.preventDefault();

    const email = getValue("loginEmail");

    const password =
        document.getElementById("loginPassword")?.value || "";

    const message = document.getElementById("authMessage");

    if (message) {
        message.textContent = "Logging in...";
        message.className = "";
    }

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

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : "Login failed. Please check your credentials."
            );
        }

        if (!data.access_token) {
            throw new Error(
                "The server did not return an access token."
            );
        }

        sessionStorage.setItem(
            TOKEN_KEY,
            data.access_token
        );

        const meResponse = await fetch(`${API}/api/me`, {
            headers: {
                Authorization: `Bearer ${data.access_token}`
            }
        });

        if (!meResponse.ok) {
            sessionStorage.removeItem(TOKEN_KEY);

            throw new Error(
                "Could not verify your login. Please try again."
            );
        }

        showAppContent();

        document.getElementById("loginForm")?.reset();

        if (message) {
            message.textContent = "";
        }

        showSection("home");
        loadProfile();
        loadResumeData();

    } catch (error) {
        if (message) {
            message.textContent =
                error.message ||
                "Could not connect to SkillBridge server.";

            message.className = "error";
        }
    }
}

/* =========================================
   SHOW APP CONTENT
   ========================================= */

function showAppContent() {
    const authSection = document.getElementById("authSection");
    const appContent = document.getElementById("appContent");

    if (authSection) {
        authSection.style.display = "none";
    }

    if (appContent) {
        appContent.style.display = "block";
    }
}

/* =========================================
   LOGOUT
   ========================================= */

function logoutUser() {
    sessionStorage.removeItem(TOKEN_KEY);

    const appContent = document.getElementById("appContent");
    const authSection = document.getElementById("authSection");
    const message = document.getElementById("authMessage");

    if (appContent) {
        appContent.style.display = "none";
    }

    if (authSection) {
        authSection.style.display = "block";
    }

    if (message) {
        message.textContent = "You have logged out.";
        message.className = "success";
    }

    const passwordInput = document.getElementById("loginPassword");

    if (passwordInput) {
        passwordInput.value = "";
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
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
        if (authSection) {
            authSection.style.display = "block";
        }

        if (appContent) {
            appContent.style.display = "none";
        }

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
            loadProfile();
            loadResumeData();

        } else {
            sessionStorage.removeItem(TOKEN_KEY);

            if (authSection) {
                authSection.style.display = "block";
            }

            if (appContent) {
                appContent.style.display = "none";
            }
        }

    } catch (error) {
        if (authSection) {
            authSection.style.display = "block";
        }

        if (appContent) {
            appContent.style.display = "none";
        }

        if (message) {
            message.textContent =
                "Could not connect to SkillBridge. Please try again.";

            message.className = "error";
        }
    }
}

/* =========================================
   PASSWORD VISIBILITY
   Optional helper
   ========================================= */

function togglePassword(inputId, button) {
    const passwordInput = document.getElementById(inputId);

    if (!passwordInput) return;

    const isHidden = passwordInput.type === "password";

    passwordInput.type = isHidden ? "text" : "password";

    if (button) {
        button.setAttribute(
            "aria-label",
            isHidden ? "Hide password" : "Show password"
        );
    }
}



function logout() {
    // Remove the login token
    sessionStorage.removeItem(TOKEN_KEY);

    // Hide all app content and navigation inside appContent
    const appContent = document.getElementById("appContent");
    if (appContent) {
        appContent.style.display = "none";
    }

    // Show the login section
    const authSection = document.getElementById("authSection");
    if (authSection) {
        authSection.style.display = "block";
    }

    // Display logout message
    const message = document.getElementById("authMessage");
    if (message) {
        message.textContent = "You have logged out.";
        message.className = "";
    }

    window.scrollTo(0, 0);
}
