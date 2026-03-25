document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const form = document.getElementById('auditForm');
    const domainInput = document.getElementById('domain');
    const companyInput = document.getElementById('company');
    const submitBtn = document.getElementById('submitBtn');
    const btnIcon = submitBtn.querySelector('svg');
    const btnSpinner = document.getElementById('btnSpinner');
    
    // Layout States
    const heroSection = document.getElementById('heroSection');
    const workspace = document.getElementById('workspace');
    
    // Workspace Elements
    const currentFocusText = document.getElementById('currentFocusText');
    const activeTargetDomain = document.getElementById('activeTargetDomain');
    const targetBadge = document.querySelector('.target-badge');
    
    // Canvas Elements
    const agentLiveStatus = document.getElementById('agentLiveStatus');
    const centralOrb = document.getElementById('centralOrb');
    const agentMainState = document.getElementById('agentMainState');
    const agentSubState = document.getElementById('agentSubState');
    const artifactVault = document.getElementById('artifactVault');
    
    // Terminal
    const logList = document.getElementById('logList');
    const terminalWindow = document.getElementById('terminalWindow');

    // Progress
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    // Agent Nodes
    const agentNodes = {
        'extraction': document.getElementById('node-extraction'),
        'vision': document.getElementById('node-vision'),
        'market': document.getElementById('node-market'),
        'rag': document.getElementById('node-rag'),
        'synthesis': document.getElementById('node-synthesis')
    };

    // History Modal
    const historyModal = document.getElementById('historyModal');
    const openHistoryBtn = document.getElementById('openHistoryBtn');
    const closeHistoryBtn = document.getElementById('closeHistoryBtn');
    const historyList = document.getElementById('historyList');

    // Preview Modal
    const previewModal = document.getElementById('previewModal');
    const closePreviewBtn = document.getElementById('closePreviewBtn');
    const previewContent = document.getElementById('previewContent');

    let eventSource = null;
    let currentJobId = null;

    // History Functions
    openHistoryBtn.addEventListener('click', async () => {
        historyModal.classList.remove('hidden');
        historyList.innerHTML = '<div class="spinner" style="margin: 40px auto;"></div>';
        
        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            
            if (!data.history || data.history.length === 0) {
                historyList.innerHTML = '<p style="color: #a1a1aa; text-align: center; padding: 40px;">No archives found. Your past audits will appear here.</p>';
                return;
            }
            
            let html = '<div class="history-grid">';
            data.history.forEach(item => {
                html += `
                    <div class="history-card">
                        <div class="hc-header">
                            <div class="hc-domain">${item.domain}</div>
                            <div class="hc-company">${item.company}</div>
                            <div class="hc-date">${item.date} • Vault: ${item.archive_id ? item.archive_id.slice(0, 8) : 'Legacy'}</div>
                        </div>
                        <div class="hc-actions">
                            <a href="/output/archives/${item.archive_id}/Strategy_Document.docx" class="btn-dl docx" target="_blank"><i data-feather="file-text"></i> DOCX</a>
                            <a href="/output/archives/${item.archive_id}/12_Month_Action_Plan.xlsx" class="btn-dl xlsx" target="_blank"><i data-feather="grid"></i> XLSX</a>
                            <a href="/output/archives/${item.archive_id}/Master_Presentation.pptx" class="btn-dl pptx" target="_blank" style="background: rgba(210, 71, 38, 0.1); color: #ff8a65;"><i data-feather="monitor"></i> PPTX</a>
                            <button class="btn-dl preview-btn" onclick="openLivePreview('${item.archive_id}')"><i data-feather="eye"></i> Preview</button>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            historyList.innerHTML = html;
            feather.replace();
            
        } catch (e) {
            historyList.innerHTML = '<p style="color: #ef4444; text-align: center; padding: 40px;">Error securely connecting to Archive Vault.</p>';
        }
    });

    closeHistoryBtn.addEventListener('click', () => {
        historyModal.classList.add('hidden');
    });

    closePreviewBtn.addEventListener('click', () => {
        previewModal.classList.add('hidden');
    });

    window.openLivePreview = async (archiveId) => {
        previewModal.classList.remove('hidden');
        previewContent.innerHTML = '<div class="spinner" style="margin: 40px auto;"></div><p style="text-align:center;color:var(--text-muted);">Decrypting Vault Artifacts...</p>';

        try {
            const res = await fetch(`/output/archives/${archiveId}/strategy_narrative.json`);
            if (!res.ok) throw new Error("Preview format not supported on older legacy archives.");
            
            const data = await res.json();
            
            let html = `<div class="report-reader">`;
            html += `<h1>Executive Summary</h1>`;
            html += `<p>${data.executive_summary || 'N/A'}</p>`;
            
            html += `<h2>Competitive Landscape</h2>`;
            html += `<p>${data.competitive_landscape_analysis || 'N/A'}</p>`;
            
            if (data.integrated_strategy_technical) {
                html += `<h2>Technical & AI Readiness (Pillar 1)</h2>`;
                html += `<p>${data.integrated_strategy_technical.overview || 'N/A'}</p>`;
                if (data.integrated_strategy_technical.key_initiatives) {
                    html += `<ul>${data.integrated_strategy_technical.key_initiatives.map(i => `<li>${i}</li>`).join('')}</ul>`;
                }
            }
            
            if (data.content_strategy_roadmap && data.content_strategy_roadmap.length > 0) {
                html += `<h2>Key Content Opportunities</h2>`;
                data.content_strategy_roadmap.forEach(pillar => {
                    html += `<h3>${pillar.topic}</h3>`;
                    html += `<p>${pillar.rationale}</p>`;
                    if (pillar.sub_topics) {
                        html += `<ul>${pillar.sub_topics.map(t => `<li>${t}</li>`).join('')}</ul>`;
                    }
                });
            }
            
            html += `</div>`;
            previewContent.innerHTML = html;
            
        } catch(e) {
            previewContent.innerHTML = `<p style="color: #f472b6; text-align: center; padding: 40px;"><i data-feather="alert-triangle"></i> ${e.message}</p>`;
            feather.replace();
        }
    };

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const domain = domainInput.value.trim();
        const company = companyInput.value.trim();
        if(!domain || !company) return;

        // UI Transition to Loading
        btnIcon.classList.add('hidden');
        btnSpinner.classList.remove('hidden');
        submitBtn.disabled = true;

        const formData = new FormData();
        formData.append('domain', domain);
        formData.append('company', company);

        try {
            const response = await fetch('/api/start-audit', { method: 'POST', body: formData });
            const data = await response.json();
            currentJobId = data.job_id;
            
            // Switch to Workspace
            setTimeout(() => {
                heroSection.classList.add('hidden');
                workspace.classList.remove('hidden');
                
                activeTargetDomain.innerText = domain;
                targetBadge.classList.add('active');
                
                resetWorkspaceState();
                startLogStream(currentJobId);
            }, 600);

        } catch (error) {
            console.error(error);
            submitBtn.disabled = false;
            btnIcon.classList.remove('hidden');
            btnSpinner.classList.add('hidden');
            alert("Connection error deploying agent swarm.");
        }
    });

    function resetWorkspaceState() {
        if(eventSource) eventSource.close();
        logList.innerHTML = '';
        artifactVault.classList.add('hidden');
        agentLiveStatus.classList.remove('hidden');
        
        progressContainer.classList.add('hidden');
        progressFill.style.width = '0%';
        progressText.innerText = '0% | Initializing...';
        
        centralOrb.className = 'giant-orb booting';
        agentMainState.innerText = "Agent Deployed";
        agentSubState.innerText = "Connecting to LangGraph network...";
        currentFocusText.innerText = "Initializing Swarm...";
        
        Object.values(agentNodes).forEach(node => {
            node.className = 'node-item pending';
            node.querySelector('.node-status').innerText = 'Awaiting...';
        });
    }

    function startLogStream(jobId) {
        eventSource = new EventSource(`/api/stream-logs/${jobId}`);

        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.done) {
                eventSource.close();
                if (data.status === 'completed') {
                    finishPipeline(currentJobId);
                } else {
                    handleError(data.message || "Pipeline failed.");
                }
                return;
            }

            if (data.log) {
                parseAndRenderLog(data.log);
            }
        };

        eventSource.onerror = function() {
            eventSource.close();
        };
    }

    // Advanced Parser for Node Tracking and Orb Morphing
    function parseAndRenderLog(rawText) {
        // Skip silent keep-alives
        if (rawText.includes(": keep-alive ping")) return;

        // Intercept Progress Markers
        if (rawText.includes("[PROGRESS]")) {
            const match = rawText.match(/\[PROGRESS\]\s*([^\|]+)\|\s*(.*)/);
            if (match) {
                const percent = match[1].trim();
                const desc = match[2].trim();
                progressContainer.classList.remove('hidden');
                progressFill.style.width = percent;
                progressText.innerText = `${percent} | ${desc}`;
                return; // Do not render PROGRESS tags in terminal directly
            }
        }

        const currentActive = logList.querySelector('.active');
        if (currentActive) currentActive.classList.remove('active');

        const newLi = document.createElement('li');
        newLi.className = 'log-item active';

        // Detect Logic Phases
        if (rawText.includes("Phase 1, 1.5 & 2")) {
            setNodeActive('extraction'); setNodeActive('vision'); setNodeActive('market');
            centralOrb.className = 'giant-orb extracting';
            agentMainState.innerText = "Extracting Intelligence";
            agentSubState.innerText = "Scraping UI, SEO seeds, and Market KPIs in parallel.";
            currentFocusText.innerText = "Parallel Data Extraction";
            newLi.className = 'log-item node-marker';
            
        } else if (rawText.includes("Phase 4: Constructing Recursive FAISS")) {
            setNodeDone('extraction'); setNodeDone('vision'); setNodeDone('market');
            setNodeActive('rag');
            centralOrb.className = 'giant-orb extracting';
            agentMainState.innerText = "Vectorizing Context";
            agentSubState.innerText = "Building local RAG database for rapid retrieval.";
            currentFocusText.innerText = "RAG Vector Indexing";
            newLi.className = 'log-item node-marker';
            
        } else if (rawText.includes("Phase 5: GPT-4o AEO Strategy Synthesis")) {
            setNodeDone('rag');
            setNodeActive('synthesis');
            centralOrb.className = 'giant-orb synthesizing';
            agentMainState.innerText = "Synthesizing Strategy";
            agentSubState.innerText = "GPT-4o is writing the integrated narrative parameters.";
            currentFocusText.innerText = "LLM Narrative Generation";
            newLi.className = 'log-item node-marker';
            
        } else if (rawText.includes("Phase 6: Injecting Dynamic Architecture")) {
            setNodeDone('synthesis');
            centralOrb.className = 'giant-orb booting';
            agentMainState.innerText = "Compiling Deliverables";
            agentSubState.innerText = "Generating dynamic charts, Excel models, and native DOCX.";
            currentFocusText.innerText = "File Compilation";
            newLi.className = 'log-item node-marker';
            
        } else if (rawText.includes("✅")) {
            newLi.className = 'log-item success-marker';
        } else if (rawText.includes("[!]")) {
            newLi.className = 'log-item error-marker';
        }

        newLi.innerText = rawText;
        logList.appendChild(newLi);

        // Auto Scroll
        terminalWindow.scrollTop = terminalWindow.scrollHeight;
    }

    function setNodeActive(key) {
        if(agentNodes[key]) {
            agentNodes[key].className = 'node-item active';
            agentNodes[key].querySelector('.node-status').innerText = 'Processing...';
        }
    }
    
    function setNodeDone(key) {
        if(agentNodes[key]) {
            agentNodes[key].className = 'node-item done';
            agentNodes[key].querySelector('.node-status').innerText = 'Complete';
        }
    }

    async function finishPipeline(jobId) {
        const currentActive = logList.querySelector('.active');
        if (currentActive) currentActive.classList.remove('active');

        currentFocusText.innerText = "Audit Successfully Compiled.";
        
        // Hide Live Status Orb, Show Artifact Vault
        agentLiveStatus.classList.add('hidden');
        
        try {
            const statusRes = await fetch(`/api/status/${jobId}`);
            const jobStatus = await statusRes.json();
            
            if (jobStatus.deliverables) {
                const docxLink = document.getElementById('docxLink');
                const xlsxLink = document.getElementById('xlsxLink');
                const pptxLink = document.getElementById('pptxLink');
                if (docxLink) docxLink.href = jobStatus.deliverables.docx;
                if (xlsxLink) xlsxLink.href = jobStatus.deliverables.xlsx;
                if (pptxLink) pptxLink.href = jobStatus.deliverables.pptx;
            }

            const res = await fetch('/api/history');
            const data = await res.json();
            if (data.history && data.history.length > 0) {
                const latest = data.history[0]; // Most recent audit
                const previewBtn = document.getElementById('livePreviewBtn');
                if (previewBtn) {
                    previewBtn.classList.remove('hidden');
                    previewBtn.onclick = () => window.openLivePreview(latest.archive_id);
                }
            }
        } catch(e) {
            console.error("Failed to fetch latest archive for preview binding", e);
        }
        
        setTimeout(() => {
            artifactVault.classList.remove('hidden');
        }, 300);
    }

    function handleError(msg) {
        centralOrb.style.background = 'radial-gradient(circle, #fff 5%, #ef4444 40%, transparent 70%)';
        centralOrb.style.animation = 'none';
        agentMainState.innerText = "Critical Failure";
        agentSubState.innerText = msg;
        
        const errLi = document.createElement('li');
        errLi.className = 'log-item error-marker';
        errLi.innerText = `[System Failure] ${msg}`;
        logList.appendChild(errLi);
    }
});
