/**
 * RecruiterFlow - RecruiterBot Frontend Application
 * Interacts with FastAPI backend endpoints:
 * - GET /jobs
 * - GET /jobs/{id}/matches
 * - GET /candidates
 * - GET /candidates/{id}/matches
 * - GET /api/sql-detective/questions
 * - GET /api/sql-detective/run/{id}
 */

// Global State
let allJobs = [];
let allCandidates = [];
let activeJobId = 1;
let activeCandidateId = 1;
let activeQuestionId = 1;
let sqlQuestions = [];

document.addEventListener("DOMContentLoaded", () => {
    setupTabs();
    loadJobs();
    loadCandidates();
    loadSQLDetective();
});

// -----------------------------------------------------------------------------
// Tab Navigation
// -----------------------------------------------------------------------------
function setupTabs() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            const targetViewId = tab.getAttribute("data-target");
            document.querySelectorAll(".view-panel").forEach(panel => {
                panel.classList.remove("active");
            });
            document.getElementById(targetViewId).classList.add("active");
        });
    });
}

// -----------------------------------------------------------------------------
// Part 1: Job Matcher (GET /jobs/{id}/matches)
// -----------------------------------------------------------------------------
async function loadJobs() {
    try {
        const res = await fetch("/jobs");
        allJobs = await res.json();
        renderJobsSidebar(allJobs);
        if (allJobs.length > 0) {
            selectJob(allJobs[0].id);
        }
    } catch (err) {
        console.error("Failed to load jobs:", err);
    }
}

function renderJobsSidebar(jobs) {
    const container = document.getElementById("jobs-sidebar-list");
    container.innerHTML = "";

    jobs.forEach(job => {
        const card = document.createElement("div");
        card.className = `select-card ${job.id === activeJobId ? 'active' : ''}`;
        card.id = `job-card-${job.id}`;
        card.onclick = () => selectJob(job.id);

        card.innerHTML = `
            <div class="select-card-header">
                <span class="select-card-title">${escapeHTML(job.title)}</span>
                <span class="badge-count">${job.min_experience} yrs min</span>
            </div>
            <p class="select-tagline">"${escapeHTML(job.tagline)}"</p>
            <div class="pill-container">
                ${job.required_skills.slice(0, 3).map(s => `<span class="tag-pill skill">${escapeHTML(s)}</span>`).join('')}
            </div>
        `;
        container.appendChild(card);
    });
}

async function selectJob(jobId) {
    activeJobId = jobId;
    document.querySelectorAll("#jobs-sidebar-list .select-card").forEach(c => c.classList.remove("active"));
    const activeCard = document.getElementById(`job-card-${jobId}`);
    if (activeCard) activeCard.classList.add("active");

    const matchesContainer = document.getElementById("job-matches-container");
    matchesContainer.innerHTML = `<div class="empty-state">Computing AI candidate rankings using pure raw SQL...</div>`;

    try {
        const res = await fetch(`/jobs/${jobId}/matches`);
        const data = await res.json();
        renderJobMatches(data);
    } catch (err) {
        matchesContainer.innerHTML = `<div class="empty-state" style="color: var(--accent-rose)">Failed to fetch matches: ${err.message}</div>`;
    }
}

function renderJobMatches(data) {
    const job = data.job;
    const matches = data.matches;

    // Update banner
    const banner = document.getElementById("job-active-banner");
    banner.innerHTML = `
        <div class="target-info">
            <h2>${escapeHTML(job.title)}</h2>
            <p><strong>Tagline:</strong> "${escapeHTML(job.tagline)}" &bull; <strong>Min Experience:</strong> ${job.min_experience} years</p>
            <div class="pill-container" style="margin-top: 8px;">
                ${job.required_skills.map(s => `<span class="tag-pill skill">Req: ${escapeHTML(s)}</span>`).join('')}
                ${job.culture_keywords.map(k => `<span class="tag-pill culture">Culture: ${escapeHTML(k)}</span>`).join('')}
            </div>
        </div>
        <div style="text-align: right">
            <span class="badge-count" style="font-size: 13px; padding: 6px 14px;">15 Evaluated</span>
        </div>
    `;

    const container = document.getElementById("job-matches-container");
    container.innerHTML = "";

    matches.forEach(m => {
        const cand = m.candidate;
        const b = m.breakdown;
        const card = document.createElement("div");
        card.className = `match-card ${m.rank === 1 ? 'rank-1' : ''}`;

        let availClass = 'avail-notlooking';
        if (cand.availability === 'Immediate') availClass = 'avail-immediate';
        if (cand.availability === '2 weeks') availClass = 'avail-2weeks';

        card.innerHTML = `
            <div class="match-header">
                <div class="match-identity">
                    <div class="rank-badge">${m.rank === 1 ? '👑' : '#' + m.rank}</div>
                    <div class="match-name-group">
                        <h3>${escapeHTML(cand.name)}</h3>
                        <p>${cand.experience_years} years experience &bull; <span class="tag-pill ${availClass}">${cand.availability}</span></p>
                    </div>
                </div>
                <div class="score-display">
                    <div class="score-number">${m.score.toFixed(1)}%</div>
                    <div class="score-sublabel">Match Score</div>
                </div>
            </div>

            <div class="breakdown-strip">
                <div class="breakdown-item">
                    <span class="breakdown-label">Skills (50%)</span>
                    <span class="breakdown-val">${b.skills_score} / 50</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Experience (25%)</span>
                    <span class="breakdown-val">${b.experience_score} / 25</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Culture (15%)</span>
                    <span class="breakdown-val">${b.culture_score} / 15</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Availability (10%)</span>
                    <span class="breakdown-val">${b.availability_score} / 10</span>
                </div>
            </div>

            <div class="skills-fit-row">
                <div class="fit-label">Skill Coverage:</div>
                <div class="pill-container">
                    ${m.matched_skills.map(s => `<span class="skill-match-pill matched">✓ ${escapeHTML(s)}</span>`).join('')}
                    ${m.missing_skills.map(s => `<span class="skill-match-pill missing">✕ ${escapeHTML(s)}</span>`).join('')}
                </div>
            </div>

            <div class="reason-box">
                <strong>Match Analysis:</strong> ${escapeHTML(m.reason)}
            </div>

            <div class="quirk-quote">
                <strong>Character Quirk:</strong> "${escapeHTML(cand.quirk)}"
            </div>
        `;
        container.appendChild(card);
    });
}

// -----------------------------------------------------------------------------
// Part 1: Reverse Matching (GET /candidates/{id}/matches)
// -----------------------------------------------------------------------------
async function loadCandidates() {
    try {
        const res = await fetch("/candidates");
        allCandidates = await res.json();
        renderCandidatesSidebar(allCandidates);
        if (allCandidates.length > 0) {
            selectCandidate(allCandidates[0].id);
        }
    } catch (err) {
        console.error("Failed to load candidates:", err);
    }
}

function renderCandidatesSidebar(candidates) {
    const container = document.getElementById("candidates-sidebar-list");
    container.innerHTML = "";

    candidates.forEach(cand => {
        const card = document.createElement("div");
        card.className = `select-card ${cand.id === activeCandidateId ? 'active' : ''}`;
        card.id = `candidate-card-${cand.id}`;
        card.onclick = () => selectCandidate(cand.id);

        let availClass = 'avail-notlooking';
        if (cand.availability === 'Immediate') availClass = 'avail-immediate';
        if (cand.availability === '2 weeks') availClass = 'avail-2weeks';

        card.innerHTML = `
            <div class="select-card-header">
                <span class="select-card-title">${escapeHTML(cand.name)}</span>
                <span class="tag-pill ${availClass}">${cand.availability}</span>
            </div>
            <div class="select-card-meta">${cand.experience_years} years experience</div>
            <div class="pill-container">
                ${cand.skills.slice(0, 3).map(s => `<span class="tag-pill skill">${escapeHTML(s)}</span>`).join('')}
            </div>
        `;
        container.appendChild(card);
    });
}

async function selectCandidate(candidateId) {
    activeCandidateId = candidateId;
    document.querySelectorAll("#candidates-sidebar-list .select-card").forEach(c => c.classList.remove("active"));
    const activeCard = document.getElementById(`candidate-card-${candidateId}`);
    if (activeCard) activeCard.classList.add("active");

    const matchesContainer = document.getElementById("candidate-matches-container");
    matchesContainer.innerHTML = `<div class="empty-state">Computing best fitting job openings for candidate...</div>`;

    try {
        const res = await fetch(`/candidates/${candidateId}/matches`);
        const data = await res.json();
        renderCandidateMatches(data);
    } catch (err) {
        matchesContainer.innerHTML = `<div class="empty-state" style="color: var(--accent-rose)">Failed to fetch matches: ${err.message}</div>`;
    }
}

function renderCandidateMatches(data) {
    const cand = data.candidate;
    const matches = data.matches;

    // Update banner
    let availClass = 'avail-notlooking';
    if (cand.availability === 'Immediate') availClass = 'avail-immediate';
    if (cand.availability === '2 weeks') availClass = 'avail-2weeks';

    const banner = document.getElementById("candidate-active-banner");
    banner.innerHTML = `
        <div class="target-info">
            <h2>${escapeHTML(cand.name)}</h2>
            <p>${cand.experience_years} years experience &bull; <span class="tag-pill ${availClass}">${cand.availability}</span></p>
            <div class="quirk-quote" style="margin-top: 8px;">
                <strong>Quirk:</strong> "${escapeHTML(cand.quirk)}"
            </div>
        </div>
        <div style="text-align: right">
            <span class="badge-count" style="font-size: 13px; padding: 6px 14px;">${data.total_jobs_evaluated} Open Roles</span>
        </div>
    `;

    const container = document.getElementById("candidate-matches-container");
    container.innerHTML = "";

    matches.forEach(m => {
        const job = m.job;
        const b = m.breakdown;
        const card = document.createElement("div");
        card.className = `match-card ${m.rank === 1 ? 'rank-1' : ''}`;

        card.innerHTML = `
            <div class="match-header">
                <div class="match-identity">
                    <div class="rank-badge">${m.rank === 1 ? '👑' : '#' + m.rank}</div>
                    <div class="match-name-group">
                        <h3>${escapeHTML(job.title)}</h3>
                        <p>Min ${job.min_experience} yrs &bull; "${escapeHTML(job.tagline)}"</p>
                    </div>
                </div>
                <div class="score-display">
                    <div class="score-number">${m.score.toFixed(1)}%</div>
                    <div class="score-sublabel">Match Fit</div>
                </div>
            </div>

            <div class="breakdown-strip">
                <div class="breakdown-item">
                    <span class="breakdown-label">Skills (50%)</span>
                    <span class="breakdown-val">${b.skills_score} / 50</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Experience (25%)</span>
                    <span class="breakdown-val">${b.experience_score} / 25</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Culture (15%)</span>
                    <span class="breakdown-val">${b.culture_score} / 15</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Availability (10%)</span>
                    <span class="breakdown-val">${b.availability_score} / 10</span>
                </div>
            </div>

            <div class="skills-fit-row">
                <div class="fit-label">Required Skills Covered:</div>
                <div class="pill-container">
                    ${m.matched_skills.map(s => `<span class="skill-match-pill matched">✓ ${escapeHTML(s)}</span>`).join('')}
                    ${m.missing_skills.map(s => `<span class="skill-match-pill missing">✕ ${escapeHTML(s)}</span>`).join('')}
                </div>
            </div>

            <div class="reason-box">
                <strong>Why this is a fit:</strong> ${escapeHTML(m.reason)}
            </div>
        `;
        container.appendChild(card);
    });
}

// -----------------------------------------------------------------------------
// Part 2: SQL Detective Challenge Live Playground
// -----------------------------------------------------------------------------
async function loadSQLDetective() {
    try {
        const res = await fetch("/api/sql-detective/questions");
        sqlQuestions = await res.json();
        renderSQLQuestionsSidebar(sqlQuestions);
        if (sqlQuestions.length > 0) {
            selectSQLQuestion(sqlQuestions[0].id);
        }
    } catch (err) {
        console.error("Failed to load SQL Detective questions:", err);
    }
}

function renderSQLQuestionsSidebar(questions) {
    const container = document.getElementById("sql-sidebar-list");
    container.innerHTML = "";

    questions.forEach(q => {
        const card = document.createElement("div");
        card.className = `query-card ${q.id === activeQuestionId ? 'active' : ''}`;
        card.id = `sql-q-card-${q.id}`;
        card.onclick = () => selectSQLQuestion(q.id);

        card.innerHTML = `
            <div class="query-card-title">${escapeHTML(q.title)}</div>
            <div class="query-card-desc">${escapeHTML(q.description.substring(0, 75))}...</div>
        `;
        container.appendChild(card);
    });
}

function selectSQLQuestion(qId) {
    activeQuestionId = qId;
    document.querySelectorAll("#sql-sidebar-list .query-card").forEach(c => c.classList.remove("active"));
    const activeCard = document.getElementById(`sql-q-card-${qId}`);
    if (activeCard) activeCard.classList.add("active");

    const q = sqlQuestions.find(item => item.id === qId);
    if (!q) return;

    document.getElementById("sql-detail-title").textContent = q.title;
    document.getElementById("sql-detail-desc").textContent = q.description;
    document.getElementById("sql-code-display").textContent = q.sql;

    // Reset table output
    document.getElementById("sql-results-table-container").innerHTML = `
        <div class="empty-state">Click <strong>"Execute SQL Live"</strong> to run this query against SQLite!</div>
    `;
}

async function executeCurrentSQL() {
    const tableContainer = document.getElementById("sql-results-table-container");
    tableContainer.innerHTML = `<div class="empty-state">Running SQL query against in-memory SQLite engine...</div>`;

    try {
        const res = await fetch(`/api/sql-detective/run/${activeQuestionId}`);
        const data = await res.json();

        if (data.error) {
            tableContainer.innerHTML = `<div class="empty-state" style="color: var(--accent-rose)">${data.error}</div>`;
            return;
        }

        renderSQLTable(data);
    } catch (err) {
        tableContainer.innerHTML = `<div class="empty-state" style="color: var(--accent-rose)">Execution failed: ${err.message}</div>`;
    }
}

function renderSQLTable(data) {
    const tableContainer = document.getElementById("sql-results-table-container");
    const { columns, rows, row_count } = data;

    if (!rows || rows.length === 0) {
        tableContainer.innerHTML = `<div class="empty-state">Query executed successfully. 0 rows returned.</div>`;
        return;
    }

    let html = `
        <div style="margin-bottom: 10px; font-size: 12px; color: var(--text-dim);">
            Execution success &bull; <strong style="color: #6ee7b7">${row_count} rows returned</strong>
        </div>
        <div class="table-wrapper">
            <table class="data-table">
                <thead>
                    <tr>
                        ${columns.map(col => `<th>${escapeHTML(col)}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(row => `
                        <tr>
                            ${columns.map(col => `<td>${escapeHTML(String(row[col] ?? 'NULL'))}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    tableContainer.innerHTML = html;
}

// -----------------------------------------------------------------------------
// Utilities
// -----------------------------------------------------------------------------
function escapeHTML(str) {
    if (typeof str !== 'string') return str;
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
