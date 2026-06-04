/**
 * RunawayScout — Conversational Research Studio Frontend Logic
 * Coordinates stages from query entry to questions, blueprint, and streaming execution.
 */

let currentSessionId = null;
let currentQuestions = [];
let currentAnswers = {};
let currentVectors = [];
let currentAssumptions = [];
let outputFormat = 'pdf';
let activeEventSource = null;
let researchStartTime = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSessionsHistory();
    restoreSettings();
    loadMainPageKeyStatus();
    fetch('/api/debug/ping').catch(()=>{});
});

// --- State Transitions ---

function resetToQuery() {
    hideAllSteps();
    document.getElementById('step-query').classList.remove('hidden');
    // Re-enable the init button in case it was left disabled
    const btn = document.getElementById('btnInitResearch');
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon"><polygon points="5 3 19 12 5 21 5 3"/></svg> Analyze & Plan';
    }
    setStatus('Ready');
}

function resetToClarifications() {
    hideAllSteps();
    document.getElementById('step-clarification').classList.remove('hidden');
    setStatus('Ready');
}

function hideAllSteps() {
    const steps = ['step-query', 'step-clarification', 'step-blueprint', 'step-progress', 'step-results'];
    steps.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    });
}

function setStatus(text, colorClass = '') {
    const badge = document.getElementById('statusBadge');
    if (badge) {
        badge.innerHTML = `<span class="status-dot"></span> ${text}`;
        badge.className = `header-status ${colorClass}`;
    }
}

// --- Step 1: Initial Query ---

async function initiateResearch() {
    const query = document.getElementById('researchQuery').value.trim();
    const context = document.getElementById('researchContext').value.trim();
    outputFormat = document.getElementById('exportFormat').value;

    if (!query) {
        shakeElement('researchQuery');
        return;
    }

    const btn = document.getElementById('btnInitResearch');
    const originalBtnHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner-sm"></div> Planning...';
    setStatus('Analyzing Query...', 'busy');

    try {
        const res = await fetch('/api/research/plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, context })
        });
        const data = await res.json();
        
        if (!data.success) {
            handleApiError(data.error, 'Failed to plan research');
            btn.disabled = false;
            btn.innerHTML = originalBtnHTML;
            setStatus('Ready');
            return;
        }

        currentSessionId = data.session_id;
        currentQuestions = data.questions || [];
        currentAssumptions = data.assumptions || [];
        
        renderAssumptions(currentAssumptions);
        renderClarificationQuestions(currentQuestions);
        document.getElementById('clarificationNote').value = '';
        hideAllSteps();
        document.getElementById('step-clarification').classList.remove('hidden');
        btn.disabled = false;
        btn.innerHTML = originalBtnHTML;
        setStatus('Clarifying Bounds');

    } catch (err) {
        handleApiError(err.message, 'Error');
        btn.disabled = false;
        btn.innerHTML = originalBtnHTML;
        setStatus('Ready');
    }
}

// --- Step 2: Clarification Rendering ---

function renderAssumptions(assumptions) {
    const panel = document.getElementById('assumptionsPanel');
    const list = document.getElementById('assumptionsList');
    if (!panel || !list) return;

    list.innerHTML = '';
    if (!assumptions || assumptions.length === 0) {
        panel.classList.add('hidden');
        return;
    }

    assumptions.forEach(item => {
        const li = document.createElement('li');
        li.innerText = item;
        list.appendChild(li);
    });
    panel.classList.remove('hidden');
}

function renderClarificationQuestions(questions) {
    const container = document.getElementById('questionsContainer');
    container.innerHTML = '';
    currentAnswers = {};

    if (!questions || questions.length === 0) {
        container.innerHTML = '<p class="card-desc">No clarification needed. Press generate blueprint to continue.</p>';
        return;
    }

    questions.forEach(q => {
        currentAnswers[q.id] = q.default || '';
        
        const qDiv = document.createElement('div');
        qDiv.className = 'question-item';

        const qTitle = document.createElement('h4');
        qTitle.innerText = q.question;
        qDiv.appendChild(qTitle);

        if (q.type === 'select' || q.type === 'multi-select') {
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'choice-options';

            q.options.forEach(opt => {
                const btn = document.createElement('button');
                btn.className = 'choice-btn';
                btn.innerText = opt;
                if (opt === q.default) btn.classList.add('selected');

                btn.onclick = () => {
                    if (q.type === 'select') {
                        optionsDiv.querySelectorAll('.choice-btn').forEach(b => b.classList.remove('selected'));
                        btn.classList.add('selected');
                        currentAnswers[q.id] = opt;
                    } else {
                        // Multi-select toggle
                        btn.classList.toggle('selected');
                        const selected = Array.from(optionsDiv.querySelectorAll('.choice-btn.selected')).map(b => b.innerText);
                        currentAnswers[q.id] = selected;
                    }
                };

                optionsDiv.appendChild(btn);
            });
            qDiv.appendChild(optionsDiv);
        } else {
            // Text input
            const txt = document.createElement('input');
            txt.type = 'text';
            txt.className = 'input';
            txt.value = q.default || '';
            txt.placeholder = 'Type your answer here...';
            txt.onchange = () => {
                currentAnswers[q.id] = txt.value.trim();
            };
            qDiv.appendChild(txt);
        }

        container.appendChild(qDiv);
    });
}

function collectClarificationAnswers() {
    return Object.keys(currentAnswers).map(qid => {
        const questionObj = currentQuestions.find(q => q.id === qid);
        return {
            question_id: qid,
            question_text: questionObj ? questionObj.question : '',
            answer: currentAnswers[qid]
        };
    });
}

async function askFollowupQuestions() {
    const answersList = collectClarificationAnswers();
    const userNote = document.getElementById('clarificationNote').value.trim();

    if (!userNote && answersList.length === 0) {
        shakeElement('clarificationNote');
        return;
    }

    const btn = document.getElementById('btnAskFollowup');
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner-sm"></div> Asking...';
    setStatus('Clarifying Further...', 'busy');

    try {
        const res = await fetch('/api/research/clarify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                answers: answersList,
                user_note: userNote
            })
        });
        const data = await res.json();

        btn.disabled = false;
        btn.innerHTML = originalHTML;

        if (!data.success) {
            handleApiError(data.error, 'Failed to ask follow-up questions');
            setStatus('Clarifying Bounds');
            return;
        }

        currentQuestions = data.questions || [];
        currentAssumptions = data.assumptions || [];
        renderAssumptions(currentAssumptions);
        renderClarificationQuestions(currentQuestions);
        document.getElementById('clarificationNote').value = '';
        setStatus('Follow-Ups Ready');

        if (currentQuestions.length === 0) {
            showToast('The parser thinks the scope is clear. You can generate the blueprint now.', 'success');
        }
    } catch (err) {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
        handleApiError(err.message, 'Error');
        setStatus('Clarifying Bounds');
    }
}

async function submitClarifications() {
    const answersList = collectClarificationAnswers();
    const userNote = document.getElementById('clarificationNote').value.trim();
    if (userNote) {
        answersList.push({
            question_id: 'user_clarification_note',
            question_text: 'Additional clarification after reviewing parser questions',
            answer: userNote
        });
    }

    // Disable the blueprint button to prevent double clicks
    const blueprintBtns = document.querySelectorAll('#step-clarification .btn-primary');
    blueprintBtns.forEach(b => { b.disabled = true; b.innerHTML = '<div class="spinner-sm"></div> Generating...'; });
    setStatus('Generating Blueprint...', 'busy');

    try {
        const res = await fetch('/api/research/refine', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                answers: answersList,
                output_format: outputFormat
            })
        });
        const data = await res.json();

        if (!data.success) {
            handleApiError(data.error, 'Failed to refine prompt');
            blueprintBtns.forEach(b => { b.disabled = false; b.innerHTML = 'Generate Research Blueprint'; });
            setStatus('Clarifying Bounds');
            return;
        }
        blueprintBtns.forEach(b => { b.disabled = false; b.innerHTML = 'Generate Research Blueprint'; });

        document.getElementById('refinedPrompt').value = data.refined_prompt;
        currentVectors = data.vectors || [];
        renderVectorsBlueprint(currentVectors);

        hideAllSteps();
        document.getElementById('step-blueprint').classList.remove('hidden');
        setStatus('Blueprint Ready');

    } catch (err) {
        handleApiError(err.message, 'Error');
        blueprintBtns.forEach(b => { b.disabled = false; b.innerHTML = 'Generate Research Blueprint'; });
        setStatus('Clarifying Bounds');
    }
}

// --- Step 3: Vectors Blueprint Rendering ---

function renderVectorsBlueprint(vectors) {
    const list = document.getElementById('vectorsList');
    list.innerHTML = '';

    vectors.forEach(v => {
        const item = document.createElement('div');
        item.className = 'vector-item';

        const info = document.createElement('div');
        info.className = 'vector-info';
        info.innerHTML = `<h5>${escapeHtml(v.topic)}</h5><p>${escapeHtml(v.description)}</p>`;

        const badge = document.createElement('span');
        badge.className = `vector-badge ${v.priority || 'medium'}`;
        badge.innerText = v.priority || 'medium';

        item.appendChild(info);
        item.appendChild(badge);
        list.appendChild(item);
    });
}

// --- Step 4: Streaming Execution ---

async function startVectorResearch() {
    researchStartTime = Date.now();
    // Disable the start button to prevent multiple SSE streams
    const startBtns = document.querySelectorAll('#step-blueprint .btn-primary');
    startBtns.forEach(b => { b.disabled = true; });

    // Save the edited refinedPrompt textarea before starting the research stream
    const refinedPromptVal = document.getElementById('refinedPrompt').value;
    try {
        await fetch('/api/research/save_prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                refined_prompt: refinedPromptVal
            })
        });
    } catch (err) {
        console.error('Failed to save refined prompt:', err);
    }

    hideAllSteps();
    document.getElementById('step-progress').classList.remove('hidden');
    setStatus('Researching...', 'busy');

    // Reset progress bar
    document.getElementById('studioProgressBar').style.width = '0%';
    document.getElementById('progressStatusText').innerText = 'Initializing Research Agent...';

    const tracker = document.getElementById('activeVectorsTracker');
    tracker.innerHTML = '';

    // Render tracker rows for all vectors
    currentVectors.forEach(v => {
        const row = document.createElement('div');
        row.className = 'tracker-vector-row';
        row.id = `tracker-vector-${v.id}`;
        row.innerHTML = `
            <div class="tracker-title-container">
                <span class="tracker-status-indicator"></span>
                <strong>${escapeHtml(v.topic)}</strong>
            </div>
            <div class="tracker-sources-scraped" id="tracker-stats-${v.id}">Pending...</div>
        `;
        tracker.appendChild(row);
    });

    // Establish Server-Sent Events stream
    const eventSource = new EventSource(`/api/research/stream/${currentSessionId}`);
    activeEventSource = eventSource;

    eventSource.addEventListener('status', (e) => {
        const payload = JSON.parse(e.data);
        document.getElementById('progressStatusText').innerText = payload.message;
        updateProgressBar(payload.step, payload.total);
        updateStatusDashboard(payload);
    });

    eventSource.addEventListener('progress', (e) => {
        const payload = JSON.parse(e.data);
        document.getElementById('progressStatusText').innerText = payload.message;
        updateProgressBar(payload.step, payload.total);
        updateStatusDashboard(payload);

        if (payload.vector) {
            const row = document.getElementById(`tracker-vector-${payload.vector.id}`);
            if (row) {
                row.classList.add('running');
                document.getElementById(`tracker-stats-${payload.vector.id}`).innerText = 'Scraping sources...';
            }
        }
    });

    eventSource.addEventListener('vector_done', (e) => {
        const payload = JSON.parse(e.data);
        const vid = payload.vector.id;
        const row = document.getElementById(`tracker-vector-${vid}`);
        if (row) {
            row.className = 'tracker-vector-row done';
            const sourcesCount = payload.result.sources ? payload.result.sources.length : 0;
            document.getElementById(`tracker-stats-${vid}`).innerText = `Completed (${sourcesCount} sources analyzed)`;
        }
        updateProgressBar(payload.step, payload.total);
        updateStatusDashboard(payload);
    });

    eventSource.addEventListener('done', (e) => {
        const payload = JSON.parse(e.data);
        eventSource.close();

        if (payload.status === 'incomplete_fallback') {
            showToast('AI synthesis failed, but a fallback report was generated from saved data.', 'warning');
            setStatus('Partial Output Saved', 'warning');
        } else {
            setStatus('Research Complete', 'success');
        }
        loadSessionsHistory();

        // Show report step
        displayResearchReport(payload.synthesis, payload.sources);
    });

    eventSource.addEventListener('error', (e) => {
        let msg = 'Research stopped before final AI synthesis.';
        try {
            const payload = JSON.parse(e.data);
            msg = payload.message || msg;
            if (payload.output_file_path || payload.output_folder) {
                showToast('Partial output was saved. Check session history.', 'warning');
            }
        } catch(err) {}

        eventSource.close();
        showToast(msg, 'warning');
        setStatus('Partial Output Saved', 'warning');
        loadSessionsHistory();
    });

    eventSource.onerror = (err) => {
        console.error('SSE connection error:', err);
        eventSource.close();
        showToast('Research stream connection closed unexpectedly.', 'error');
        setStatus('Error', 'error');
    };
}

function updateProgressBar(step, total) {
    const pct = Math.min(Math.round((step / total) * 100), 100);
    document.getElementById('studioProgressBar').style.width = `${pct}%`;
}

function updateStatusDashboard(payload) {
    if (!payload) return;
    
    // Update source count
    const sourceCountEl = document.getElementById('dashboardSourceCount');
    if (sourceCountEl && payload.source_count !== undefined) {
        sourceCountEl.innerText = payload.source_count;
    }
    
    // Update rotation cells
    const cellsGrid = document.getElementById('apiCellsGrid');
    if (cellsGrid && payload.active_rotation_cells) {
        renderMainPageCellsGrid(payload.active_rotation_cells);
    }
}

function renderMainPageCellsGrid(cells) {
    const cellsGrid = document.getElementById('apiCellsGrid');
    if (!cellsGrid || !cells) return;
    cellsGrid.innerHTML = '';
    cells.forEach(cell => {
        const card = document.createElement('div');
        card.style.background = 'var(--bg-input)';
        card.style.border = '1px solid var(--border)';
        card.style.borderRadius = 'var(--radius-sm)';
        card.style.padding = '8px 12px';
        card.style.fontSize = '0.78rem';
        card.style.display = 'flex';
        card.style.flexDirection = 'column';
        card.style.gap = '4px';
        
        let statusText = 'Active';
        let color = 'var(--green)';
        
        if (cell.exhausted_today) {
            statusText = 'Exhausted';
            color = 'var(--red)';
        } else if (!cell.is_active) {
            statusText = 'Cooldown';
            color = 'var(--amber)';
        }
        
        card.innerHTML = `
            <div style="font-weight:600; color:var(--text-primary); display:flex; justify-content:space-between; gap:4px;">
                <span>Key #${cell.key_index}</span>
                <span style="font-size:0.65rem; text-transform:uppercase; color:var(--text-muted);">${cell.tier}</span>
            </div>
            <div style="display:flex; align-items:center; gap:6px; margin-top:2px;">
                <span style="width:6px; height:6px; border-radius:50%; background:${color};"></span>
                <span style="color:${color}; font-weight:500;">${statusText}</span>
            </div>
        `;
        cellsGrid.appendChild(card);
    });
}

function updateAllKeyGrids(data) {
    if (!data) return;
    renderConfigKeysGrid(data.rotation_cells || [], data.key_count || 0);
    renderMainPageCellsGrid(data.rotation_cells || []);
    
    // Auto-hide warning if there's at least one active non-exhausted key
    const hasActiveKey = (data.rotation_cells || []).some(cell => cell.is_active && !cell.exhausted_today);
    if (hasActiveKey) {
        const warningEl = document.getElementById('configWarning');
        if (warningEl) {
            warningEl.classList.add('hidden');
        }
    }
}

async function loadMainPageKeyStatus() {
    try {
        const res = await fetch('/api/keys/status');
        const data = await res.json();
        updateAllKeyGrids(data);
    } catch (e) {
        console.warn('Failed to load main page key status:', e);
    }
}

// --- Step 5: Report Results Rendering ---

function displayResearchReport(synthesis, sources) {
    hideAllSteps();
    document.getElementById('step-results').classList.remove('hidden');

    document.getElementById('reportTitle').innerText = synthesis.title || 'Research Report';
    document.getElementById('reportMeta').innerText = `Completed on ${new Date().toLocaleDateString()}`;

    // Downloads
    const exportContainer = document.getElementById('exportContainer');
    exportContainer.innerHTML = `
        <a href="/api/research/export/${currentSessionId}" class="btn-primary" download>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Export Report (${outputFormat.toUpperCase()})
        </a>
    `;

    // Summary Text
    document.getElementById('reportSummaryText').innerText = synthesis.summary || 'No summary available.';

    // Takeaways
    const takeaways = synthesis.key_takeaways || [];
    const tc = document.getElementById('takeawaysContainer');
    const tl = document.getElementById('takeawaysList');
    if (takeaways.length > 0) {
        tc.classList.remove('hidden');
        tl.innerHTML = takeaways.map(t => `<li>${escapeHtml(t)}</li>`).join('');
    } else {
        tc.classList.add('hidden');
    }

    // Sections blocks
    const sectionsContainer = document.getElementById('reportSectionsContainer');
    sectionsContainer.innerHTML = '';

    const sections = synthesis.sections || [];
    sections.forEach(sec => {
        const block = document.createElement('div');
        block.className = 'report-section-block';

        // Title
        const secTitle = document.createElement('h3');
        secTitle.innerText = sec.title || 'Research Block';
        block.appendChild(secTitle);

        // Content narrative
        const secContent = document.createElement('div');
        secContent.className = 'report-section-content';
        secContent.innerHTML = (sec.content || '').split('\n\n').map(p => `<p>${escapeHtml(p)}</p>`).join('');
        block.appendChild(secContent);

        // Key insights (if exists)
        if (sec.key_findings && sec.key_findings.length > 0) {
            const ib = document.createElement('div');
            ib.className = 'insights-box';
            ib.innerHTML = `
                <h4>Key Insights</h4>
                <ul>
                    ${sec.key_findings.map(f => `<li>${escapeHtml(f)}</li>`).join('')}
                </ul>
            `;
            block.appendChild(ib);
        }

        // Tabular data matrix (if exists)
        if (sec.data && Array.isArray(sec.data) && sec.data.length > 0) {
            const tableContainer = document.createElement('div');
            tableContainer.className = 'table-scroll';

            const table = document.createElement('table');
            table.className = 'data-table';

            const cols = [];
            sec.data.forEach(row => {
                if (typeof row === 'object') {
                    Object.keys(row).forEach(k => {
                        if (!cols.includes(k)) cols.push(k);
                    });
                }
            });

            if (cols.length > 0) {
                // Header
                const thead = document.createElement('thead');
                thead.innerHTML = `<tr>${cols.map(c => `<th>${escapeHtml(c).replace(/_/g, ' ').toUpperCase()}</th>`).join('')}</tr>`;
                table.appendChild(thead);

                // Body
                const tbody = document.createElement('tbody');
                sec.data.forEach((row, rIdx) => {
                    const tr = document.createElement('tr');
                    if (rIdx % 2 === 1) tr.className = 'zebra';
                    tr.innerHTML = cols.map(c => `<td>${escapeHtml(String(row[c] !== undefined ? row[c] : '-'))}</td>`).join('');
                    tbody.appendChild(tr);
                });
                table.appendChild(tbody);
            }

            tableContainer.appendChild(table);
            block.appendChild(tableContainer);
        }

        sectionsContainer.appendChild(block);
    });

    // Sources grid
    const sourcesList = document.getElementById('resultsSourcesList');
    sourcesList.innerHTML = '';

    if (sources && sources.length > 0) {
        sources.forEach((src, idx) => {
            const sTitle = src.title || src.url || 'Reference Source';
            const sUrl = src.url || '#';
            const safeUrl = (sUrl.startsWith('http://') || sUrl.startsWith('https://')) ? sUrl : '#';
            const tier = src.tier_label || src.label || 'Tier 6';
            const score = src.quality_score || src.score || 50;

            const badgeClass = `badge-t${tier.match(/\d/)?.[0] || '6'}`;

            const item = document.createElement('div');
            item.className = 'source-grid-item';
            item.innerHTML = `
                <div class="source-main-info">
                    <span class="source-number">[${idx+1}]</span>
                    <a href="${encodeURI(safeUrl)}" target="_blank" rel="noopener noreferrer" class="source-anchor">${escapeHtml(sTitle)}</a>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span class="badge ${badgeClass}">${escapeHtml(tier)}</span>
                    <span class="source-score-info">Score: ${score}/100</span>
                </div>
            `;
            sourcesList.appendChild(item);
        });
    } else {
        sourcesList.innerHTML = '<p class="card-desc">No sources captured.</p>';
    }
}

// --- Sidebar Sessions History ---

async function loadSessionsHistory() {
    try {
        const res = await fetch('/api/research/sessions');
        const data = await res.json();
        renderSessions(data);
    } catch (e) {
        console.warn('Failed to load history list:', e);
    }
}

function renderSessions(sessions) {
    const list = document.getElementById('historyList');
    if (!sessions || sessions.length === 0) {
        list.innerHTML = '<div class="history-empty">No past research sessions.</div>';
        return;
    }

    list.innerHTML = sessions.map(s => {
        const date = s.created_at ? new Date(s.created_at).toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
        }) : '';
        const title = s.original_query || 'Unnamed Research';
        const statusText = s.status === 'complete' ? 'Complete' : s.status === 'researching' ? 'Resumable' : s.status === 'failed' ? 'Failed' : 'Incomplete';
        const badgeClass = s.status === 'complete' ? 'badge-t3' : s.status === 'failed' ? 'badge-t1' : 'badge-t2';

        return `
            <div class="history-item" onclick="loadPastSession('${s.id}')">
                <div class="history-meta">
                    <span class="badge ${badgeClass}" style="margin:0;">${statusText}</span>
                    <span class="history-date">${date}</span>
                </div>
                <div class="history-title">${escapeHtml(title).substring(0, 80)}</div>
                <button class="history-delete" onclick="event.stopPropagation(); deletePastSession('${s.id}', this)" title="Delete">✕</button>
            </div>
        `;
    }).join('');
}

async function loadPastSession(id) {
    try {
        const res = await fetch(`/api/research/sessions/${id}`);
        const data = await res.json();
        
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        currentSessionId = data.id;
        outputFormat = data.output_format || 'pdf';

        if (data.status === 'complete' && data.result_data) {
            displayResearchReport(data.result_data, data.sources_used);
        } else if ((data.status === 'ready' || data.status === 'researching' || data.status === 'failed' || data.status === 'incomplete') && data.research_vectors && data.research_vectors.length > 0) {
            document.getElementById('refinedPrompt').value = data.refined_prompt;
            currentVectors = data.research_vectors || [];
            renderVectorsBlueprint(currentVectors);
            hideAllSteps();
            document.getElementById('step-blueprint').classList.remove('hidden');
            setStatus(data.status === 'ready' ? 'Blueprint Ready' : 'Ready To Resume');
            if (data.status !== 'ready') {
                const completed = (data.vector_results || []).filter(r => r.success).length;
                showToast(`Loaded resumable session. ${completed}/${currentVectors.length} vectors already completed.`, 'warning');
            }
        } else {
            // Go back to input query state
            resetToQuery();
            document.getElementById('researchQuery').value = data.original_query || '';
        }
        
        toggleHistory();
    } catch (e) {
        showToast('Failed to load session details: ' + e.message, 'error');
    }
}

async function deletePastSession(id, btn) {
    if (!confirm('Delete this research session?')) return;
    try {
        await fetch(`/api/research/sessions/${id}`, { method: 'DELETE' });
        btn.closest('.history-item').remove();
    } catch (e) {
        console.error('Delete failed:', e);
    }
}

function toggleHistory() {
    const sb = document.getElementById('historySidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    sb.classList.toggle('hidden');
    if (backdrop) backdrop.classList.toggle('hidden');
    if (!sb.classList.contains('hidden')) loadSessionsHistory();
}

// --- Configurations & Settings ---

function showConfigModal(showWarning = false) {
    const warningEl = document.getElementById('configWarning');
    if (warningEl && !showWarning) {
        warningEl.classList.add('hidden');
    }
    document.getElementById('configModal').classList.remove('hidden');
    // Fetch and render live key statuses
    loadConfigKeyStatus();
}

async function loadConfigKeyStatus() {
    try {
        const res = await fetch('/api/keys/status');
        const data = await res.json();
        updateAllKeyGrids(data);
    } catch (e) {
        console.warn('Failed to load key status:', e);
    }
}

function renderConfigKeysGrid(cells, keyCount) {
    const grid = document.getElementById('configKeysGrid');
    const countEl = document.getElementById('configKeyCount');
    if (!grid) return;
    grid.innerHTML = '';

    if (cells.length === 0) {
        grid.innerHTML = '<span style="font-size:0.8rem; color:var(--text-muted);">No keys loaded yet.</span>';
        if (countEl) countEl.textContent = '';
        return;
    }

    // Group cells by key_index to show one card per key with aggregated tier statuses
    const keyMap = {};
    cells.forEach(cell => {
        if (!keyMap[cell.key_index]) keyMap[cell.key_index] = [];
        keyMap[cell.key_index].push(cell);
    });

    Object.keys(keyMap).sort((a, b) => Number(a) - Number(b)).forEach(keyIdx => {
        const tiers = keyMap[keyIdx];
        const allExhausted = tiers.every(t => t.exhausted_today);
        const anyExhausted = tiers.some(t => t.exhausted_today);
        const anyCooldown = tiers.some(t => !t.is_active && !t.exhausted_today);

        let overallStatus = 'Active';
        let color = 'var(--green)';
        if (allExhausted) {
            overallStatus = 'Exhausted';
            color = 'var(--red)';
        } else if (anyExhausted || anyCooldown) {
            overallStatus = 'Partial';
            color = 'var(--amber)';
        }

        const card = document.createElement('div');
        card.style.cssText = 'background:var(--bg-input); border:1px solid var(--border); border-radius:var(--radius-sm); padding:8px 12px; font-size:0.78rem; display:flex; flex-direction:column; gap:4px;';
        card.innerHTML = `
            <div style="font-weight:600; color:var(--text-primary);">
                Key #${keyIdx}
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
                <span style="width:6px; height:6px; border-radius:50%; background:${color};"></span>
                <span style="color:${color}; font-weight:500;">${overallStatus}</span>
            </div>
            <div style="display:flex; gap:4px; margin-top:2px;">
                ${tiers.map(t => {
                    let tc = t.is_active ? 'var(--green)' : (t.exhausted_today ? 'var(--red)' : 'var(--amber)');
                    return `<span style="font-size:0.6rem; padding:1px 5px; border-radius:3px; background:${tc}20; color:${tc}; text-transform:uppercase;">${t.tier}</span>`;
                }).join('')}
            </div>
        `;
        grid.appendChild(card);
    });

    if (countEl) {
        countEl.textContent = `${keyCount} key${keyCount !== 1 ? 's' : ''} in rotation pool`;
    }
}

function hideConfigModal() {
    document.getElementById('configModal').classList.add('hidden');
}

function handleApiError(errorMsg, defaultPrefix = 'Error') {
    const isQuotaError = errorMsg && (
        errorMsg.includes('429') || 
        errorMsg.toLowerCase().includes('resource_exhausted') || 
        errorMsg.toLowerCase().includes('quota') ||
        errorMsg.toLowerCase().includes('rate limit exceeded') ||
        errorMsg.toLowerCase().includes('limit: 0')
    );
    
    if (isQuotaError) {
        const warningEl = document.getElementById('configWarning');
        const warningTextEl = document.getElementById('configWarningText');
        if (warningEl && warningTextEl) {
            warningTextEl.innerText = "The Gemini API Key is exhausted or invalid. Please supply your own valid Gemini API Key to run research sessions.";
            warningEl.classList.remove('hidden');
        }
        
        showConfigModal(true);
        shakeElement('geminiKey');
        const geminiInput = document.getElementById('geminiKey');
        if (geminiInput) geminiInput.focus();
        
        showToast(`${defaultPrefix}: Gemini API quota exhausted. Please configure your own API key.`, 'warning');
    } else {
        showToast(`${defaultPrefix}: ${errorMsg}`, 'error');
    }
}

async function saveConfig() {
    const pplx = document.getElementById('perplexityKey').value.trim();
    const gemini = document.getElementById('geminiKey').value.trim();
    const yt = document.getElementById('youtubeKey').value.trim();

    try {
        const payload = {};
        if (pplx) payload.perplexity_key = pplx;
        if (gemini) payload.gemini_key = gemini;
        if (yt) payload.youtube_key = yt;

        let responseMsg = 'Settings saved successfully!';

        if (Object.keys(payload).length > 0) {
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.message) responseMsg = data.message;

            // Refresh key status grids in both places
            if (data.rotation_cells) {
                updateAllKeyGrids(data);
                
                // If we now have active keys, clear the error status
                const hasActiveKey = data.rotation_cells.some(cell => cell.is_active && !cell.exhausted_today);
                if (hasActiveKey) {
                    setStatus('Ready');
                }
            }
        }

        if (pplx) localStorage.setItem('perplexity_key', pplx);
        // Don't store gemini key in localStorage anymore — it's appended server-side
        // Clear the gemini input since the key is now in the pool
        if (gemini) document.getElementById('geminiKey').value = '';
        if (yt) localStorage.setItem('youtube_key', yt);

        showToast(responseMsg, 'success');
        // Don't close modal so user can see the updated key grid
    } catch (e) {
        showToast('Failed to save settings: ' + e.message, 'error');
    }
}

async function restoreSettings() {
    const pplx = localStorage.getItem('perplexity_key');
    const yt = localStorage.getItem('youtube_key');
    if (pplx) document.getElementById('perplexityKey').value = pplx;
    if (yt) document.getElementById('youtubeKey').value = yt;

    // Gemini keys are managed server-side via add_key() — don't restore from localStorage
    // Clean up any old gemini key from localStorage
    localStorage.removeItem('gemini_key');

    // Only send perplexity and youtube keys on page load
    const payload = {};
    if (pplx) payload.perplexity_key = pplx;
    if (yt) payload.youtube_key = yt;

    if (Object.keys(payload).length > 0) {
        try {
            await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } catch (e) {
            console.warn("Failed to auto-register keys:", e);
        }
    }
}

// --- Utility Helpers ---

function shakeElement(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.add('shake');
        setTimeout(() => el.classList.remove('shake'), 500);
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// --- Tab Management & Session History Tab ---

function startNewResearchGlobal() {
    researchStartTime = null;
    if (activeEventSource) {
        activeEventSource.close();
        activeEventSource = null;
    }
    switchTab('new-research');
    resetToQuery();
    const qInput = document.getElementById('researchQuery');
    const cInput = document.getElementById('researchContext');
    if (qInput) qInput.value = '';
    if (cInput) cInput.value = '';
    currentSessionId = null;
    currentQuestions = [];
    currentAnswers = {};
    currentVectors = [];
    currentAssumptions = [];
    showToast('Started new research session', 'success');
}

function switchTab(tabName) {
    const tabNew = document.getElementById('tabNewResearch');
    const tabPast = document.getElementById('tabPastResearches');
    const panelNew = document.getElementById('panel-new-research');
    const panelPast = document.getElementById('panel-past-researches');

    if (tabName === 'new-research') {
        tabNew.classList.add('active');
        tabPast.classList.remove('active');
        panelNew.classList.remove('hidden');
        panelPast.classList.add('hidden');
    } else {
        tabNew.classList.remove('active');
        tabPast.classList.add('active');
        panelNew.classList.add('hidden');
        panelPast.classList.remove('hidden');
        loadSessionsHistoryTab();
    }
}

async function loadSessionsHistoryTab() {
    const list = document.getElementById('historyListTab');
    try {
        const res = await fetch('/api/research/sessions');
        const sessions = await res.json();
        
        if (!sessions || sessions.length === 0) {
            list.innerHTML = '<div class="history-empty">No past research sessions.</div>';
            return;
        }
        
        list.innerHTML = sessions.map(s => {
            const date = s.created_at ? new Date(s.created_at).toLocaleDateString('en-IN', {
                day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
            }) : '';
            const title = s.original_query || 'Unnamed Research';
            const statusText = s.status === 'complete' ? 'Complete' : s.status === 'failed' ? 'Failed' : 'Incomplete';
            const badgeClass = s.status === 'complete' ? 'badge-t3' : s.status === 'failed' ? 'badge-t1' : 'badge-t2';
            const activeClass = (currentSessionId === s.id) ? 'active' : '';

            return `
                <div class="history-tab-item ${activeClass}" id="tab-session-${s.id}" onclick="loadPastSessionDetails('${s.id}')">
                    <div class="item-header">
                        <span class="badge ${badgeClass}">${statusText}</span>
                        <span class="item-date">${date}</span>
                    </div>
                    <div class="item-title">${escapeHtml(title)}</div>
                    <button class="history-delete-btn" onclick="event.stopPropagation(); deletePastSessionTab('${s.id}')" title="Delete">✕</button>
                </div>
            `;
        }).join('');
        
    } catch (e) {
        list.innerHTML = '<div class="history-empty" style="color: var(--red);">Failed to load history list.</div>';
    }
}

async function deletePastSessionTab(id) {
    if (!confirm('Delete this research session?')) return;
    try {
        await fetch(`/api/research/sessions/${id}`, { method: 'DELETE' });
        loadSessionsHistoryTab();
        loadSessionsHistory(); // Also reload the sidebar history
        if (currentSessionId === id) {
            document.getElementById('historyDetailCard').innerHTML = `
                <div class="history-detail-placeholder">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48" style="color: var(--text-muted); margin-bottom: 1rem;">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                    </svg>
                    <h3>Select a past research session to view details</h3>
                    <p>Here you can see the original prompt, clarification questions, final report and refine it further.</p>
                </div>
            `;
        }
    } catch (e) {
        console.error('Delete failed:', e);
    }
}

async function loadPastSessionDetails(id) {
    // Set active item in the list
    document.querySelectorAll('.history-tab-item').forEach(el => el.classList.remove('active'));
    const activeEl = document.getElementById(`tab-session-${id}`);
    if (activeEl) activeEl.classList.add('active');

    currentSessionId = id;
    const card = document.getElementById('historyDetailCard');
    card.innerHTML = '<div class="history-detail-placeholder"><div class="spinner"></div><p style="margin-top: 1rem;">Fetching details...</p></div>';

    try {
        const res = await fetch(`/api/research/sessions/${id}`);
        const data = await res.json();
        
        if (data.error) {
            card.innerHTML = `<div class="history-detail-placeholder" style="color: var(--red);"><p>Error: ${escapeHtml(data.error)}</p></div>`;
            return;
        }

        outputFormat = data.output_format || 'pdf';
        renderSessionDetailsIntoCard(data, card);
        
    } catch (e) {
        card.innerHTML = `<div class="history-detail-placeholder" style="color: var(--red);"><p>Failed to load session details: ${escapeHtml(e.message)}</p></div>`;
    }
}

function renderSessionDetailsIntoCard(session, container) {
    container.innerHTML = '';

    // 1. Header and Meta Info
    const headerDiv = document.createElement('div');
    headerDiv.className = 'results-report-header';
    headerDiv.style.borderBottom = '1px solid var(--border)';
    headerDiv.style.paddingBottom = '1.5rem';
    headerDiv.style.marginBottom = '2rem';
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'results-titles';
    const titleH2 = document.createElement('h2');
    titleH2.innerText = session.result_data && session.result_data.title ? session.result_data.title : 'Research Details';
    titleDiv.appendChild(titleH2);
    
    const metaDiv = document.createElement('div');
    metaDiv.className = 'meta-info';
    metaDiv.innerText = `Session ID: ${session.id} | Date: ${session.created_at ? new Date(session.created_at).toLocaleDateString() : 'N/A'}`;
    titleDiv.appendChild(metaDiv);
    headerDiv.appendChild(titleDiv);

    // Downloads
    if (session.status === 'complete' && session.output_file_path) {
        const downloadsDiv = document.createElement('div');
        downloadsDiv.className = 'results-downloads';
        downloadsDiv.innerHTML = `
            <a href="/api/research/export/${session.id}" class="btn-primary" download>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon" width="16" height="16">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Export Report (${(session.output_format || 'PDF').toUpperCase()})
            </a>
        `;
        headerDiv.appendChild(downloadsDiv);
    }
    container.appendChild(headerDiv);

    // 2. Input Parameters Section
    const inputSection = document.createElement('div');
    inputSection.innerHTML = `
        <h3 style="font-size: 1.1rem; margin-bottom: 1rem; color: var(--accent);">📝 Input Parameters</h3>
        <div class="input-block-details">
            <h4>Original Search Prompt</h4>
            <p>${escapeHtml(session.original_query)}</p>
        </div>
    `;
    
    if (session.original_context) {
        const contextBlock = document.createElement('div');
        contextBlock.className = 'input-block-details';
        contextBlock.innerHTML = `
            <h4>Additional Context & Guidelines</h4>
            <p>${escapeHtml(session.original_context)}</p>
        `;
        inputSection.appendChild(contextBlock);
    }

    if (session.clarification_answers && session.clarification_answers.length > 0) {
        const answersBlock = document.createElement('div');
        answersBlock.className = 'input-block-details';
        answersBlock.innerHTML = `
            <h4>Clarification Answers Given</h4>
            <div class="answers-grid">
                ${session.clarification_answers.map(ans => `
                    <div class="answer-box">
                        <div class="ans-q">${escapeHtml(ans.question_text)}</div>
                        <div class="ans-a">${escapeHtml(ans.answer)}</div>
                    </div>
                `).join('')}
            </div>
        `;
        inputSection.appendChild(answersBlock);
    }

    if (session.refined_prompt) {
        const refinedBlock = document.createElement('div');
        refinedBlock.className = 'input-block-details';
        refinedBlock.innerHTML = `
            <h4>AI-Refined Master Prompt Blueprint</h4>
            <p style="white-space: pre-wrap; font-size: 0.85rem; line-height: 1.5; color: var(--text-muted);">${escapeHtml(session.refined_prompt)}</p>
        `;
        inputSection.appendChild(refinedBlock);
    }
    
    container.appendChild(inputSection);
    container.appendChild(document.createElement('hr')).style.margin = '2rem 0';

    // 3. Research Results Section
    if (session.status === 'complete' && session.result_data) {
        const resultsHeader = document.createElement('h3');
        resultsHeader.style.fontSize = '1.1rem';
        resultsHeader.style.marginBottom = '1rem';
        resultsHeader.style.color = 'var(--green)';
        resultsHeader.innerText = '📊 Research Outcomes';
        container.appendChild(resultsHeader);

        // Executive Summary
        const summaryCard = document.createElement('div');
        summaryCard.className = 'report-exec-summary';
        summaryCard.innerHTML = `
            <h3 style="font-size: 1rem; margin-bottom: 8px;">Executive Summary</h3>
            <p>${escapeHtml(session.result_data.summary || 'No summary available.')}</p>
        `;
        
        const takeaways = session.result_data.key_takeaways || [];
        if (takeaways.length > 0) {
            const takeawaysDiv = document.createElement('div');
            takeawaysDiv.className = 'takeaways-list-container';
            takeawaysDiv.innerHTML = `
                <h4 style="font-size: 0.9rem; margin-top: 1rem; margin-bottom: 8px;">Key Strategic Takeaways</h4>
                <ul>
                    ${takeaways.map(t => `<li>${escapeHtml(t)}</li>`).join('')}
                </ul>
            `;
            summaryCard.appendChild(takeawaysDiv);
        }
        container.appendChild(summaryCard);

        // Sections
        const sectionsContainer = document.createElement('div');
        sectionsContainer.className = 'report-sections';
        
        const sections = session.result_data.sections || [];
        sections.forEach(sec => {
            const block = document.createElement('div');
            block.className = 'report-section-block';
            block.style.marginTop = '1.5rem';

            const secTitle = document.createElement('h3');
            secTitle.style.fontSize = '1rem';
            secTitle.innerText = sec.title || 'Research Block';
            block.appendChild(secTitle);

            const secContent = document.createElement('div');
            secContent.className = 'report-section-content';
            secContent.innerHTML = (sec.content || '').split('\n\n').map(p => `<p>${escapeHtml(p)}</p>`).join('');
            block.appendChild(secContent);

            if (sec.key_findings && sec.key_findings.length > 0) {
                const ib = document.createElement('div');
                ib.className = 'insights-box';
                ib.innerHTML = `
                    <h4>Key Insights</h4>
                    <ul>
                        ${sec.key_findings.map(f => `<li>${escapeHtml(f)}</li>`).join('')}
                    </ul>
                `;
                block.appendChild(ib);
            }

            if (sec.data && Array.isArray(sec.data) && sec.data.length > 0) {
                const tableContainer = document.createElement('div');
                tableContainer.className = 'table-scroll';

                const table = document.createElement('table');
                table.className = 'data-table';

                const cols = [];
                sec.data.forEach(row => {
                    if (typeof row === 'object') {
                        Object.keys(row).forEach(k => {
                            if (!cols.includes(k)) cols.push(k);
                        });
                    }
                });

                if (cols.length > 0) {
                    const thead = document.createElement('thead');
                    thead.innerHTML = `<tr>${cols.map(c => `<th>${escapeHtml(c).replace(/_/g, ' ').toUpperCase()}</th>`).join('')}</tr>`;
                    table.appendChild(thead);

                    const tbody = document.createElement('tbody');
                    sec.data.forEach((row, rIdx) => {
                        const tr = document.createElement('tr');
                        if (rIdx % 2 === 1) tr.className = 'zebra';
                        tr.innerHTML = cols.map(c => `<td>${escapeHtml(String(row[c] !== undefined ? row[c] : '-'))}</td>`).join('');
                        tbody.appendChild(tr);
                    });
                    table.appendChild(tbody);
                }

                tableContainer.appendChild(table);
                block.appendChild(tableContainer);
            }
            sectionsContainer.appendChild(block);
        });
        container.appendChild(sectionsContainer);

        // Sources
        const sourcesCard = document.createElement('div');
        sourcesCard.className = 'sources-card';
        sourcesCard.style.marginTop = '2rem';
        sourcesCard.innerHTML = '<h3>Authoritative Sources Compiled</h3>';
        
        const sourcesList = document.createElement('div');
        sourcesList.className = 'sources-list-grid';
        
        const sources = session.sources_used || [];
        if (sources.length > 0) {
            sources.forEach((src, idx) => {
                const sTitle = src.title || src.url || 'Reference Source';
                const sUrl = src.url || '#';
                const safeUrl2 = (sUrl.startsWith('http://') || sUrl.startsWith('https://')) ? sUrl : '#';
                const tier = src.tier_label || src.label || 'Tier 6';
                const score = src.quality_score || src.score || 50;
                const badgeClass = `badge-t${tier.match(/\d/)?.[0] || '6'}`;

                const item = document.createElement('div');
                item.className = 'source-grid-item';
                item.innerHTML = `
                    <div class="source-main-info">
                        <span class="source-number">[${idx+1}]</span>
                        <a href="${encodeURI(safeUrl2)}" target="_blank" rel="noopener noreferrer" class="source-anchor">${escapeHtml(sTitle)}</a>
                    </div>
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span class="badge ${badgeClass}">${escapeHtml(tier)}</span>
                        <span class="source-score-info">Score: ${score}/100</span>
                    </div>
                `;
                sourcesList.appendChild(item);
            });
        } else {
            sourcesList.innerHTML = '<p class="card-desc">No sources captured.</p>';
        }
        sourcesCard.appendChild(sourcesList);
        container.appendChild(sourcesCard);

        // 4. Refinement Feedback Box inside Past session details
        const refineCard = document.createElement('div');
        refineCard.className = 'refinement-card';
        refineCard.id = 'pastRefinementCard';
        refineCard.innerHTML = `
            <h3>💡 Refine this Research</h3>
            <p class="card-desc">Need something modified or added? Type your refinement comments below and the AI will update this report instantly.</p>
            <div class="form-group">
                <textarea id="refinementInputPast" rows="2" placeholder="e.g. Please add a pricing tier comparison table for local vs metro deliveries..." class="input textarea"></textarea>
            </div>
            <button class="btn-primary" id="btnApplyRefinementPast" onclick="applyRefinement(true)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon" width="16" height="16">
                    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6m12-4a9 9 0 0 1-15 6.7L3 16"/>
                </svg>
                Apply Refinement
            </button>
        `;
        container.appendChild(refineCard);

    } else if (session.status === 'failed') {
        const errorCard = document.createElement('div');
        errorCard.className = 'summary-card';
        errorCard.style.borderColor = 'var(--red)';
        errorCard.style.background = 'var(--red-dim)';
        errorCard.innerHTML = `
            <h3 style="color: var(--red);">❌ Research Session Failed</h3>
            <p style="color: var(--red); font-weight: 500;">
                ${escapeHtml(session.result_data && session.result_data.error ? session.result_data.error : 'An error occurred during research.')}
            </p>
            ${session.output_file_path ? `<a href="/api/research/export/${session.id}" class="btn-secondary" download>Download Partial Output</a>` : ''}
            ${session.research_vectors && session.research_vectors.length > 0 ? `<button class="btn-primary" style="margin-top: 10px;" onclick="resumeUnfinishedSession('${session.id}')">Resume Research</button>` : ''}
        `;
        container.appendChild(errorCard);
    } else {
        const unfinishedCard = document.createElement('div');
        unfinishedCard.className = 'summary-card';
        unfinishedCard.innerHTML = `
            <h3>⚠️ Incomplete Session</h3>
            <p>This session was not completed. Status: <strong>${escapeHtml(session.status)}</strong></p>
            ${session.output_file_path ? `<p style="margin-top: 8px;">Partial output is available.</p><a href="/api/research/export/${session.id}" class="btn-secondary" download>Download Partial Output</a>` : ''}
            <button class="btn-primary" style="margin-top: 10px;" onclick="resumeUnfinishedSession('${session.id}')">Resume Research</button>
        `;
        container.appendChild(unfinishedCard);
    }
}

function resumeUnfinishedSession(id) {
    switchTab('new-research');
    loadPastSession(id);
}

async function applyRefinement(isPastTab) {
    const inputId = isPastTab ? 'refinementInputPast' : 'refinementInput';
    const btnId = isPastTab ? 'btnApplyRefinementPast' : 'btnApplyRefinement';
    
    const refinement_instruction = document.getElementById(inputId).value.trim();
    if (!refinement_instruction) {
        shakeElement(inputId);
        return;
    }

    const btn = document.getElementById(btnId);
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner-sm"></div> Refining...';
    
    try {
        const res = await fetch('/api/research/refine_result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                refinement_instruction: refinement_instruction
            })
        });
        const data = await res.json();
        
        btn.disabled = false;
        btn.innerHTML = originalText;
        
        if (!data.success) {
            handleApiError(data.error, 'Refinement failed');
            return;
        }

        showToast('Research updated successfully!', 'success');
        
        if (isPastTab) {
            // Reload details of this past session
            loadPastSessionDetails(currentSessionId);
            // Refresh list
            loadSessionsHistoryTab();
        } else {
            // Update the display of new results using sources_used from backend
            displayResearchReport(data.synthesis, data.sources_used || []);
            // Clear input
            document.getElementById(inputId).value = '';
        }
        
        // Also refresh history sidebar
        loadSessionsHistory();
        
    } catch (err) {
        btn.disabled = false;
        btn.innerHTML = originalText;
        handleApiError(err.message, 'Error');
    }
}

// --- Toast Notifications ---

function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Log alert with elapsed time to server
    let elapsedText = 'N/A';
    if (researchStartTime) {
        const elapsedMs = Date.now() - researchStartTime;
        const minutes = Math.floor(elapsedMs / 60000);
        const seconds = Math.floor((elapsedMs % 60000) / 1000);
        elapsedText = `${minutes} min ${seconds} sec`;
    }

    if (currentSessionId) {
        fetch('/api/research/log_alert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message,
                type: type,
                elapsed_time: elapsedText
            })
        }).catch(err => console.warn("Failed to log alert to server:", err));
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let iconSvg = '';
    if (type === 'success') {
        iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toast-icon"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
    } else if (type === 'error') {
        iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toast-icon"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
    } else if (type === 'warning') {
        iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toast-icon"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
    }

    toast.innerHTML = `
        ${iconSvg}
        <div class="toast-message">${escapeHtml(message)}</div>
        <button class="toast-close">&times;</button>
    `;

    container.appendChild(toast);

    const closeBtn = toast.querySelector('.toast-close');
    let timeoutId;

    const removeToast = () => {
        toast.classList.add('hiding');
        toast.addEventListener('animationend', () => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        });
    };

    closeBtn.addEventListener('click', () => {
        clearTimeout(timeoutId);
        removeToast();
    });

    timeoutId = setTimeout(removeToast, 5000);
}
