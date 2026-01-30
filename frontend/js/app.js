// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// State
let currentDocument = null;
let currentFilter = 'all';

// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const uploadSection = document.getElementById('uploadSection');
const analysisSection = document.getElementById('analysisSection');
const themeToggle = document.getElementById('themeToggle');
const exportBtn = document.getElementById('exportBtn');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadThemePreference();
});

// Event Listeners
function initializeEventListeners() {
    // File upload
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);

    // Theme toggle
    themeToggle.addEventListener('click', toggleTheme);

    // Export and new analysis
    exportBtn.addEventListener('click', exportReport);
    newAnalysisBtn.addEventListener('click', resetToUpload);

    // Clause filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.dataset.filter;
            filterClauses();
        });
    });

    // Search functionality
    initializeSearch();
}

// File Handling
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        uploadFile(file);
    }
}

function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');

    const file = e.dataTransfer.files[0];
    if (file) {
        uploadFile(file);
    }
}

// Upload and Process
async function uploadFile(file) {
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
        alert('Please upload a PDF or DOCX file');
        return;
    }

    // Validate file size (16MB)
    if (file.size > 16 * 1024 * 1024) {
        alert('File size must be less than 16MB');
        return;
    }

    // Show progress
    progressContainer.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'Uploading document...';

    // Simulate progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 5;
        if (progress <= 90) {
            progressFill.style.width = progress + '%';
        }
    }, 200);

    try {
        // Create form data
        const formData = new FormData();
        formData.append('file', file);

        // Upload file
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();

        // Complete progress
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        progressText.textContent = 'Analysis complete!';

        // Store document
        currentDocument = data.document;

        // Show results after a brief delay
        setTimeout(() => {
            displayAnalysis(currentDocument);
        }, 1000);

    } catch (error) {
        clearInterval(progressInterval);
        progressContainer.style.display = 'none';
        alert('Error processing document: ' + error.message);
        console.error('Upload error:', error);
    }
}

// Display Analysis
function displayAnalysis(document) {
    // Hide upload, show analysis
    uploadSection.style.display = 'none';
    analysisSection.style.display = 'block';

    // Document info
    document.getElementById('documentName').textContent = document.filename;
    document.getElementById('documentType').textContent = document.summary?.document_type || 'Legal Document';
    document.getElementById('documentDate').textContent = new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    // Risk assessment
    displayRiskAssessment(document.risk_assessment);

    // Summary
    displaySummary(document.summary);

    // Clauses
    displayClauses(document.clauses);

    // Key terms
    displayKeyTerms(document.key_terms);

    // Recommendations
    displayRecommendations(document.risk_assessment?.recommendations || []);
}

function displayRiskAssessment(risk) {
    if (!risk) return;

    const riskBadge = document.getElementById('riskBadge');
    const riskScore = document.getElementById('riskScore');
    const riskFactors = document.getElementById('riskFactors');

    // Risk level
    const level = risk.overall_risk_level || 'low';
    riskBadge.textContent = level.toUpperCase() + ' RISK';
    riskBadge.className = 'risk-badge ' + level;

    // Risk score
    riskScore.textContent = Math.round(risk.overall_risk_score || 0);

    // Risk factors
    riskFactors.innerHTML = '';
    if (risk.risk_factors && risk.risk_factors.length > 0) {
        risk.risk_factors.forEach(factor => {
            const item = document.createElement('div');
            item.className = 'risk-factor-item';
            item.innerHTML = `
                <h4>${factor.factor} (${factor.score})</h4>
                <p>${factor.description}</p>
            `;
            riskFactors.appendChild(item);
        });
    }

    // Missing clauses
    if (risk.missing_clauses && risk.missing_clauses.length > 0) {
        const item = document.createElement('div');
        item.className = 'risk-factor-item';
        item.innerHTML = `
            <h4>Missing Essential Clauses</h4>
            <p>${risk.missing_clauses.join(', ')}</p>
        `;
        riskFactors.appendChild(item);
    }
}

function displaySummary(summary) {
    if (!summary) return;

    document.getElementById('executiveSummary').textContent = summary.executive_summary || 'No summary available';
    document.getElementById('parties').textContent = summary.parties?.join(', ') || 'Not specified';
    document.getElementById('purpose').textContent = summary.purpose || 'Not specified';
}

function displayClauses(clauses) {
    if (!clauses || clauses.length === 0) {
        document.getElementById('clausesList').innerHTML = '<p>No clauses detected</p>';
        return;
    }

    const clausesList = document.getElementById('clausesList');
    clausesList.innerHTML = '';

    clauses.forEach(clause => {
        const item = document.createElement('div');
        item.className = `clause-item ${clause.risk_level}`;
        item.dataset.risk = clause.risk_level;

        let issuesHtml = '';
        if (clause.issues && clause.issues.length > 0) {
            issuesHtml = `
                <div class="clause-issues">
                    <h5>Issues:</h5>
                    <ul>
                        ${clause.issues.map(issue => `<li>${issue}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        let recommendationsHtml = '';
        if (clause.recommendations && clause.recommendations.length > 0) {
            recommendationsHtml = `
                <div class="clause-recommendations">
                    <h5>Recommendations:</h5>
                    <ul>
                        ${clause.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        item.innerHTML = `
            <div class="clause-header">
                <span class="clause-category">${clause.category.replace(/_/g, ' ')}</span>
                <span class="clause-risk" style="background: var(--risk-${clause.risk_level}); color: white;">
                    ${clause.risk_level.toUpperCase()}
                </span>
            </div>
            <div class="clause-text">${clause.text}</div>
            ${issuesHtml}
            ${recommendationsHtml}
        `;

        clausesList.appendChild(item);
    });
}

function filterClauses() {
    const clauses = document.querySelectorAll('.clause-item');

    clauses.forEach(clause => {
        if (currentFilter === 'all') {
            clause.style.display = 'block';
        } else {
            clause.style.display = clause.dataset.risk === currentFilter ? 'block' : 'none';
        }
    });
}

function displayKeyTerms(terms) {
    if (!terms || terms.length === 0) {
        document.getElementById('keyTermsGrid').innerHTML = '<p>No key terms extracted</p>';
        return;
    }

    const grid = document.getElementById('keyTermsGrid');
    grid.innerHTML = '';

    terms.forEach(term => {
        const item = document.createElement('div');
        item.className = 'key-term-item';
        item.innerHTML = `
            <div class="key-term-header">
                <span class="key-term-text">${term.text}</span>
                <span class="key-term-category">${term.category}</span>
            </div>
            <p style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.25rem;">
                Importance: ${Math.round(term.importance_score)}
            </p>
        `;
        grid.appendChild(item);
    });
}

function displayRecommendations(recommendations) {
    if (!recommendations || recommendations.length === 0) {
        document.getElementById('recommendationsList').innerHTML = '<p>No recommendations</p>';
        return;
    }

    const list = document.getElementById('recommendationsList');
    list.innerHTML = '';

    recommendations.forEach(rec => {
        const item = document.createElement('div');
        item.className = 'recommendation-item';
        item.innerHTML = `<p>${rec}</p>`;
        list.appendChild(item);
    });
}

// Export Report
async function exportReport() {
    if (!currentDocument) return;

    try {
        exportBtn.disabled = true;
        exportBtn.textContent = 'Generating PDF...';

        const response = await fetch(`${API_BASE_URL}/export/${currentDocument.id}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Export failed');
        }

        // Download file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `legal_analysis_${currentDocument.id}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        exportBtn.disabled = false;
        exportBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M8 2a1 1 0 000 2h2a1 1 0 100-2H8z"/>
                <path d="M3 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v6h-4.586l1.293-1.293a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L10.414 13H15v3a2 2 0 01-2 2H5a2 2 0 01-2-2V5z"/>
            </svg>
            Export PDF Report
        `;

    } catch (error) {
        alert('Error exporting report: ' + error.message);
        exportBtn.disabled = false;
        exportBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M8 2a1 1 0 000 2h2a1 1 0 100-2H8z"/>
                <path d="M3 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v6h-4.586l1.293-1.293a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L10.414 13H15v3a2 2 0 01-2 2H5a2 2 0 01-2-2V5z"/>
            </svg>
            Export PDF Report
        `;
    }
}

// Reset to Upload
function resetToUpload() {
    currentDocument = null;
    currentFilter = 'all';
    uploadSection.style.display = 'flex';
    analysisSection.style.display = 'none';
    progressContainer.style.display = 'none';
    fileInput.value = '';
}

// Theme Management
function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

function loadThemePreference() {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    }
}

// ============= SEARCH FUNCTIONALITY =============

let searchState = {
    query: '',
    riskLevels: [],
    sortBy: 'relevance'
};

let searchDebounceTimer = null;

function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearSearch = document.getElementById('clearSearch');
    const sortBy = document.getElementById('sortBy');
    const riskChips = document.querySelectorAll('.chip[data-filter="risk"]');

    // Search input with debouncing
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        searchState.query = query;

        // Show/hide clear button
        clearSearch.style.display = query ? 'block' : 'none';

        // Debounce search
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            performSearch();
        }, 500);
    });

    // Clear search
    clearSearch.addEventListener('click', () => {
        searchInput.value = '';
        searchState.query = '';
        clearSearch.style.display = 'none';
        document.getElementById('searchResults').style.display = 'none';
    });

    // Risk level chips
    riskChips.forEach(chip => {
        chip.addEventListener('click', () => {
            chip.classList.toggle('active');

            // Update risk levels array
            searchState.riskLevels = Array.from(
                document.querySelectorAll('.chip[data-filter="risk"].active')
            ).map(c => c.dataset.value);

            if (searchState.query || searchState.riskLevels.length > 0) {
                performSearch();
            }
        });
    });

    // Sort by
    sortBy.addEventListener('change', (e) => {
        searchState.sortBy = e.target.value;
        if (searchState.query || searchState.riskLevels.length > 0) {
            performSearch();
        }
    });
}

async function performSearch() {
    const { query, riskLevels, sortBy } = searchState;

    // If no query and no filters, hide results
    if (!query && riskLevels.length === 0) {
        document.getElementById('searchResults').style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                risk_levels: riskLevels.length > 0 ? riskLevels : null,
                sort_by: sortBy,
                limit: 50
            })
        });

        if (!response.ok) {
            throw new Error('Search failed');
        }

        const data = await response.json();
        displaySearchResults(data.search_results);

    } catch (error) {
        console.error('Search error:', error);
        document.getElementById('resultsCount').textContent = 'Error performing search';
    }
}

function displaySearchResults(results) {
    const searchResults = document.getElementById('searchResults');
    const resultsCount = document.getElementById('resultsCount');
    const resultsList = document.getElementById('resultsList');

    // Show results section
    searchResults.style.display = 'block';

    // Update count
    const count = results.total_results || 0;
    resultsCount.textContent = `${count} result${count !== 1 ? 's' : ''} found`;

    // Clear previous results
    resultsList.innerHTML = '';

    // Display results
    if (!results.results || results.results.length === 0) {
        resultsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 2rem;">No documents match your search criteria.</p>';
        return;
    }

    results.results.forEach(result => {
        const doc = result.document;
        const item = document.createElement('div');
        item.className = 'result-item';

        // Format date
        const date = doc.processed_at ? new Date(doc.processed_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }) : 'Unknown date';

        // Get snippet
        let snippet = '';
        if (result.matches && result.matches.length > 0) {
            snippet = result.matches[0].text;
            // Highlight search terms
            if (searchState.query) {
                const terms = searchState.query.toLowerCase().split(/\s+/);
                terms.forEach(term => {
                    const regex = new RegExp(`(${escapeRegex(term)})`, 'gi');
                    snippet = snippet.replace(regex, '<mark>$1</mark>');
                });
            }
        } else {
            snippet = doc.summary?.executive_summary?.substring(0, 200) + '...' || 'No preview available';
        }

        // Risk badge color
        const riskLevel = doc.risk_level || 'low';
        const riskColor = {
            'low': 'var(--risk-low)',
            'medium': 'var(--risk-medium)',
            'high': 'var(--risk-high)',
            'critical': 'var(--risk-critical)'
        }[riskLevel] || 'var(--primary-blue)';

        item.style.borderLeftColor = riskColor;

        item.innerHTML = `
            <div class="result-header">
                <div class="result-title">${doc.filename || 'Untitled Document'}</div>
                <div class="result-meta">
                    <span class="result-type">${doc.document_type || doc.summary?.document_type || 'Document'}</span>
                    <span class="result-date">${date}</span>
                </div>
            </div>
            <div class="result-snippet">${snippet}</div>
            <div class="result-stats">
                <span>
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                        <circle cx="6" cy="6" r="5" fill="${riskColor}"/>
                    </svg>
                    ${riskLevel.toUpperCase()} Risk
                </span>
                <span>📄 ${doc.clauses?.length || 0} clauses</span>
                <span>⚡ Score: ${Math.round(doc.risk_score || 0)}/100</span>
            </div>
        `;

        // Click to view document
        item.addEventListener('click', () => {
            currentDocument = doc;
            displayAnalysis(doc);
            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        resultsList.appendChild(item);
    });
}

function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
