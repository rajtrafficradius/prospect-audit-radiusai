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

    // Agent Nodes
    const agentNodes = {
        'extraction': document.getElementById('node-extraction'),
        'vision': document.getElementById('node-vision'),
        'market': document.getElementById('node-market'),
        'rag': document.getElementById('node-rag'),
        'synthesis': document.getElementById('node-synthesis')
    };

    let eventSource = null;
    let currentJobId = null;

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
                    finishPipeline();
                } else {
                    handleError("Pipeline exited with a failure status.");
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

    function finishPipeline() {
        const currentActive = logList.querySelector('.active');
        if (currentActive) currentActive.classList.remove('active');

        currentFocusText.innerText = "Audit Successfully Compiled.";
        
        // Hide Live Status Orb, Show Artifact Vault
        agentLiveStatus.classList.add('hidden');
        
        document.getElementById('dl-docx').href = `/output/deliverables/Strategy_Document.docx`;
        document.getElementById('dl-xlsx').href = `/output/deliverables/12_Month_Action_Plan.xlsx`;
        
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
