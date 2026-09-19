/**
 * ResourceLoop AI — Frontend Application
 * SPA with hash-based routing and REST API integration.
 */

const API = '';  // Same origin — FastAPI serves both API and static

let currentOrg = 1;
let resCurrentPage = 1;
let resTotalPages = 1;

// ═══════════════ ROUTING ═══════════════

function navigate(page) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    // Show target
    const el = document.getElementById(`page-${page}`);
    if (el) el.classList.add('active');
    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItems = document.querySelectorAll('.nav-item');
    const pages = ['dashboard', 'resources', 'find-resource', 'circularity', 'network', 'documents', 'impact'];
    const idx = pages.indexOf(page);
    if (idx >= 0 && navItems[idx]) navItems[idx].classList.add('active');
    // Update title
    const titles = {
        'dashboard': 'Dashboard',
        'resources': 'Resource Inventory',
        'find-resource': 'Find a Resource',
        'circularity': 'Circularity',
        'network': 'Resource Network',
        'documents': 'Documents & Knowledge',
        'impact': 'Impact',
    };
    document.getElementById('page-title').textContent = titles[page] || 'Dashboard';
    // Load data for the page
    loadPageData(page);
}

function loadPageData(page) {
    switch(page) {
        case 'dashboard': loadDashboard(); break;
        case 'resources': loadResources(); break;
        case 'network': loadNetwork(); break;
        case 'documents': loadDocuments(); break;
        case 'impact': loadImpact(); break;
    }
}

function changeOrganization(orgId) {
    currentOrg = parseInt(orgId);
    const active = document.querySelector('.page.active');
    if (active) {
        const page = active.id.replace('page-', '');
        loadPageData(page);
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('hidden');
    const main = document.querySelector('main');
    main.classList.toggle('ml-0');
    main.classList.toggle('ml-64');
}

// ═══════════════ API HELPERS ═══════════════

async function apiGet(url) {
    try {
        const res = await fetch(`${API}${url}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error('API GET error:', url, err);
        return null;
    }
}

async function apiPost(url, data) {
    try {
        const res = await fetch(`${API}${url}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            let msg = `HTTP ${res.status}`;
            if (err.detail) {
                if (Array.isArray(err.detail)) {
                    msg = err.detail.map(e => e.msg || e.message || JSON.stringify(e)).join('; ');
                } else if (typeof err.detail === 'string') {
                    msg = err.detail;
                } else {
                    msg = JSON.stringify(err.detail);
                }
            }
            throw new Error(msg);
        }
        return await res.json();
    } catch (err) {
        console.error('API POST error:', url, err);
        throw err;
    }
}

async function apiPostForm(url, formData) {
    try {
        const res = await fetch(`${API}${url}`, {
            method: 'POST',
            body: formData,
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return await res.json();
    } catch (err) {
        console.error('API POST form error:', url, err);
        throw err;
    }
}

function formatCurrency(val) {
    return '€' + Number(val || 0).toLocaleString('en', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatNumber(val) {
    return Number(val || 0).toLocaleString();
}

// ═══════════════ DASHBOARD ═══════════════

async function loadDashboard() {
    const data = await apiGet(`/api/dashboard?organization_id=${currentOrg}`);
    if (!data) return;
    const s = data.stats;
    document.getElementById('stat-total').textContent = formatNumber(s.total_resources);
    document.getElementById('stat-available').textContent = formatNumber(s.available_resources);
    document.getElementById('stat-underutilized').textContent = formatNumber(s.underutilized_resources);
    document.getElementById('stat-maintenance').textContent = formatNumber(s.in_maintenance);

    // Opportunities
    const opps = data.opportunities || [];
    if (opps[0]) document.getElementById('opp-underutil').textContent = opps[0].description;
    if (opps[1]) document.getElementById('opp-redist').textContent = opps[1].description;
    if (opps[2]) document.getElementById('opp-repair').textContent = opps[2].description;

    // Impact
    document.getElementById('imp-reused').textContent = formatNumber(s.resources_matched);
    document.getElementById('imp-redist').textContent = formatNumber(s.resources_redistributed);
    document.getElementById('imp-purchases').textContent = formatNumber(s.estimated_purchases_avoided);
    document.getElementById('imp-cost').textContent = formatCurrency(s.estimated_cost_avoided);
    document.getElementById('imp-waste').textContent = formatNumber(s.estimated_waste_avoided_kg) + ' kg';
    document.getElementById('imp-co2').textContent = formatNumber(s.estimated_co2_saved_kg) + ' kg';

    // Underutilized
    const underList = document.getElementById('dashboard-underutilized');
    const underItems = data.underutilized_resources || [];
    if (underItems.length === 0) {
        underList.innerHTML = '<p class="text-sm text-gray-400">No underutilized resources detected.</p>';
    } else {
        underList.innerHTML = underItems.slice(0, 6).map(r => `
            <div class="flex items-center gap-3 p-3 bg-surface-50 rounded-lg">
                <div class="w-2 h-2 rounded-full ${r.underutilization_score === 'high' ? 'bg-red-400' : r.underutilization_score === 'medium' ? 'bg-amber-400' : 'bg-green-400'}"></div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">${r.name}</p>
                    <p class="text-xs text-gray-500">${r.department} · ${r.type} · ${r.utilization}% utilized</p>
                </div>
                <span class="text-xs text-gray-500 shrink-0">${r.potential_action}</span>
            </div>
        `).join('');
    }
}

// ═══════════════ RESOURCES ═══════════════

async function loadResources() {
    const search = document.getElementById('res-search').value;
    const category = document.getElementById('res-category').value;
    const availability = document.getElementById('res-availability').value;
    const condition = document.getElementById('res-condition').value;

    let params = new URLSearchParams({
        organization_id: currentOrg,
        page: resCurrentPage,
        per_page: 15,
    });
    if (search) params.set('search', search);
    if (category) params.set('category', category);
    if (availability) params.set('availability', availability);
    if (condition) params.set('condition', condition);

    const data = await apiGet(`/api/resources?${params}`);
    if (!data) return;

    const tbody = document.getElementById('resource-table-body');
    if (data.resources.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="px-4 py-12 text-center text-gray-400 text-sm">No resources found matching your filters.</td></tr>';
    } else {
        tbody.innerHTML = data.resources.map(r => `
            <tr class="hover:bg-surface-50 cursor-pointer" onclick="showResourceDetail(${r.id})">
                <td class="px-4 py-3">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 bg-brand-50 rounded-lg flex items-center justify-center text-brand-600 text-xs font-bold">${r.resource_id.slice(-3)}</div>
                        <div>
                            <p class="text-sm font-medium text-gray-900">${r.name}</p>
                            <p class="text-xs text-gray-500">${r.resource_id}</p>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.category}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.department_name || '—'}</td>
                <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        r.condition === 'Excellent' ? 'bg-green-100 text-green-800' :
                        r.condition === 'Good' ? 'bg-blue-100 text-blue-800' :
                        r.condition === 'Fair' ? 'bg-amber-100 text-amber-800' :
                        'bg-red-100 text-red-800'
                    }">${r.condition || '—'}</span>
                </td>
                <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        r.availability === 'available' ? 'bg-green-100 text-green-800' :
                        r.availability === 'underutilized' ? 'bg-amber-100 text-amber-800' :
                        r.availability === 'in_use' ? 'bg-blue-100 text-blue-800' :
                        r.availability === 'maintenance' ? 'bg-gray-100 text-gray-600' :
                        'bg-surface-100 text-gray-600'
                    }">${(r.availability || '').replace('_', ' ')}</span>
                </td>
                <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                        <div class="score-bar w-20">
                            <div class="score-fill ${(r.utilization || 0) < 20 ? 'bg-red-400' : (r.utilization || 0) < 50 ? 'bg-amber-400' : 'bg-green-400'}" style="width:${r.utilization || 0}%"></div>
                        </div>
                        <span class="text-xs text-gray-500 w-8">${r.utilization || 0}%</span>
                    </div>
                </td>
                <td class="px-4 py-3">
                    <button class="text-xs text-brand-600 hover:text-brand-800 font-medium" onclick="event.stopPropagation(); showResourceDetail(${r.id})">View</button>
                </td>
            </tr>
        `).join('');
    }

    // Pagination
    resTotalPages = data.pages || 1;
    document.getElementById('res-page-info').textContent = `Page ${data.page} of ${data.pages} (${data.total} resources)`;
    document.getElementById('res-prev-btn').disabled = data.page <= 1;
    document.getElementById('res-next-btn').disabled = data.page >= data.pages;
}

function resPage(dir) {
    resCurrentPage = Math.max(1, Math.min(resTotalPages, resCurrentPage + dir));
    loadResources();
}

async function showResourceDetail(id) {
    const r = await apiGet(`/api/resources/${id}`);
    if (!r) return;
    const specs = r.specifications || {};
    const specsHtml = Object.entries(specs).map(([k, v]) =>
        `<div><span class="text-xs text-gray-500">${k.replace(/_/g, ' ')}</span><p class="text-sm font-medium text-gray-900">${typeof v === 'object' ? JSON.stringify(v) : v}</p></div>`
    ).join('');

    const html = `
        <div class="space-y-6">
            <div class="flex items-start justify-between">
                <div>
                    <h3 class="text-xl font-bold text-gray-900">${r.name}</h3>
                    <p class="text-sm text-gray-500 mt-1">${r.resource_id} · ${r.category} · ${r.type}</p>
                </div>
                <button onclick="closeModal('resource-detail-modal')" class="p-2 hover:bg-surface-100 rounded-lg"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
            </div>
            ${r.description ? `<p class="text-sm text-gray-600">${r.description}</p>` : ''}
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div><p class="text-xs text-gray-500">Condition</p><p class="text-sm font-medium">${r.condition || '—'}</p></div>
                <div><p class="text-xs text-gray-500">Availability</p><p class="text-sm font-medium">${(r.availability || '').replace('_', ' ')}</p></div>
                <div><p class="text-xs text-gray-500">Utilization</p><p class="text-sm font-medium">${r.utilization || 0}%</p></div>
                <div><p class="text-xs text-gray-500">Remaining Life</p><p class="text-sm font-medium">${r.remaining_useful_life_months || '—'} months</p></div>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div><p class="text-xs text-gray-500">Organization</p><p class="text-sm font-medium">${r.organization_name || '—'}</p></div>
                <div><p class="text-xs text-gray-500">Department</p><p class="text-sm font-medium">${r.department_name || '—'}</p></div>
                <div><p class="text-xs text-gray-500">Location</p><p class="text-sm font-medium">${r.location || '—'}</p></div>
                <div><p class="text-xs text-gray-500">Share Scope</p><p class="text-sm font-medium">${r.share_scope || '—'}</p></div>
            </div>
            ${specsHtml ? `<div><h4 class="text-sm font-semibold text-gray-900 mb-2">Specifications</h4><div class="grid grid-cols-2 md:grid-cols-3 gap-3 bg-surface-50 rounded-xl p-4">${specsHtml}</div></div>` : ''}
            ${r.original_cost ? `<div class="grid grid-cols-2 gap-4"><div><p class="text-xs text-gray-500">Original Cost</p><p class="text-sm font-medium">${formatCurrency(r.original_cost)}</p></div><div><p class="text-xs text-gray-500">Estimated Current Value</p><p class="text-sm font-medium">${formatCurrency(r.estimated_current_value)}</p></div></div>` : ''}
        </div>
    `;
    showModal('resource-detail-modal', html);
}

// ═══════════════ FIND A RESOURCE ═══════════════

function fillExample(n) {
    const examples = {
        1: "We need 10 computers for an AI lab with at least 16GB RAM, 512GB SSD and dedicated graphics.",
        2: "We need 5 monitors with at least 24 inch screens and 1440p resolution for the design team.",
        3: "We need 20 ergonomic office chairs for the new office space."
    };
    document.getElementById('requirement-input').value = examples[n];
}

async function searchResources() {
    const query = document.getElementById('requirement-input').value.trim();
    if (!query) return;

    document.getElementById('match-loading').classList.remove('hidden');
    document.getElementById('parsed-requirements').classList.add('hidden');
    document.getElementById('matching-results').classList.add('hidden');

    try {
        const data = await apiPost('/api/matching/search', {
            raw_query: query,
            organization_id: currentOrg,
        });

        document.getElementById('match-loading').classList.add('hidden');

        // Show parsed requirements
        const parsed = data.parsed_requirements;
        const specsHtml = Object.entries(parsed.specifications || {}).map(([k, v]) => {
            const val = typeof v === 'object' ? (v.minimum ? `≥ ${v.minimum}` : v.required ? 'Required' : JSON.stringify(v)) : v;
            return `<div class="bg-white rounded-lg p-2"><p class="text-[10px] text-gray-500 uppercase">${k.replace(/_/g, ' ')}</p><p class="text-sm font-semibold text-gray-900">${val}</p></div>`;
        }).join('');

        document.getElementById('parsed-grid').innerHTML = `
            <div class="bg-white rounded-lg p-2"><p class="text-[10px] text-gray-500 uppercase">Category</p><p class="text-sm font-semibold text-gray-900">${parsed.category}</p></div>
            <div class="bg-white rounded-lg p-2"><p class="text-[10px] text-gray-500 uppercase">Type</p><p class="text-sm font-semibold text-gray-900">${parsed.type}</p></div>
            <div class="bg-white rounded-lg p-2"><p class="text-[10px] text-gray-500 uppercase">Quantity</p><p class="text-sm font-semibold text-gray-900">${parsed.quantity}</p></div>
            ${specsHtml}
        `;
        document.getElementById('parsed-requirements').classList.remove('hidden');

        // Show results
        document.getElementById('match-count').textContent = `${data.total_compatible} compatible ${parsed.type}(s) found`;
        document.getElementById('match-message').textContent = data.message;

        // Combination
        const combo = data.recommended_combination;
        if (combo && combo.sources.length > 0) {
            document.getElementById('combination-explanation').textContent = combo.explanation;
            document.getElementById('combination-sources').innerHTML = combo.sources.map(s => `
                <div class="flex items-center gap-3 bg-white rounded-lg p-3">
                    <div class="w-8 h-8 bg-brand-100 rounded-full flex items-center justify-center text-brand-700 text-xs font-bold">${s.overall_score.toFixed(0)}%</div>
                    <div class="flex-1">
                        <p class="text-sm font-medium text-gray-900">${s.resource_name} (${s.resource_code})</p>
                        <p class="text-xs text-gray-500">${s.department_name} · ${s.condition} · ${s.utilization}% utilized</p>
                    </div>
                </div>
            `).join('');
            document.getElementById('combination-card').classList.remove('hidden');
        } else {
            document.getElementById('combination-card').classList.add('hidden');
        }

        // Individual matches
        document.getElementById('match-list').innerHTML = data.individual_matches.length === 0
            ? '<p class="text-sm text-gray-400 text-center py-8">No matching resources found.</p>'
            : data.individual_matches.map((m, i) => `
                <div class="bg-white rounded-xl border border-surface-200 p-5">
                    <div class="flex items-start justify-between mb-3">
                        <div>
                            <span class="text-xs font-medium text-gray-500">Match #${i + 1}</span>
                            <h4 class="text-base font-semibold text-gray-900">${m.resource_name}</h4>
                            <p class="text-sm text-gray-500">${m.resource_code} · ${m.department_name} · ${m.location || '—'}</p>
                        </div>
                        <div class="text-right">
                            <div class="text-2xl font-bold text-brand-600">${m.overall_score.toFixed(0)}%</div>
                            <p class="text-xs text-gray-500">Overall Score</p>
                        </div>
                    </div>
                    <div class="grid grid-cols-3 md:grid-cols-6 gap-2 mb-3">
                        ${Object.entries(m.match_details).filter(([k]) => k !== 'technical_reasons').map(([k, v]) => `
                            <div class="text-center">
                                <div class="score-bar mb-1"><div class="score-fill ${v >= 70 ? 'bg-green-400' : v >= 40 ? 'bg-amber-400' : 'bg-red-400'}" style="width:${v}%"></div></div>
                                <p class="text-[10px] text-gray-500">${k.replace(/_/g, ' ')}</p>
                                <p class="text-xs font-semibold text-gray-700">${v}%</p>
                            </div>
                        `).join('')}
                    </div>
                    <div class="bg-surface-50 rounded-lg p-3">
                        <p class="text-xs text-gray-600">${m.explanation}</p>
                    </div>
                    <div class="flex items-center gap-2 mt-3 mb-4">
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${m.condition === 'Good' || m.condition === 'Excellent' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}">${m.condition}</span>
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">${m.utilization}% utilized</span>
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">${m.remaining_life_months}mo remaining</span>
                    </div>
                    <div class="flex items-center gap-3 pt-3 border-t border-surface-200">
                        <button onclick='openRequestModal(${JSON.stringify(m).replace(/'/g, '&#39;')})' class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-sm font-medium transition-colors">Request This Resource</button>
                        <button onclick='openContactModal(${JSON.stringify(m).replace(/'/g, '&#39;')})' class="px-4 py-2 border border-surface-300 hover:bg-surface-50 text-gray-700 rounded-lg text-sm font-medium transition-colors">Contact Authority</button>
                    </div>
                </div>
            `).join('');

        document.getElementById('matching-results').classList.remove('hidden');
    } catch (err) {
        document.getElementById('match-loading').classList.add('hidden');
        alert('Error: ' + err.message);
    }
}

// ═══════════════ CIRCULARITY ═══════════════

function fillCircularityExample(n) {
    const examples = {
        1: "Old office chair with broken armrest. Metal frame with fabric seat. Still has good wheels and gas lift. Only the left armrest is broken and needs repair.",
        2: "Old laptop from 2018, 8GB RAM, 256GB SSD. Screen works fine but battery doesn't hold charge anymore. Cosmetic scratches on the lid.",
        3: "HP LaserJet printer with cracked paper tray. Print quality is still good. Minor cosmetic damage to the exterior."
    };
    document.getElementById('circularity-description').value = examples[n];
}

let _circularityImageData = null;

function handleCircularityImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('preview-img').src = e.target.result;
            document.getElementById('image-preview').classList.remove('hidden');
            _circularityImageData = e.target.result;  // base64 data URL
        };
        reader.readAsDataURL(input.files[0]);
    }
}

async function analyzeCircularity() {
    const description = document.getElementById('circularity-description').value.trim();
    const hasImage = _circularityImageData !== null;

    if (!description && !hasImage) {
        alert('Please describe the resource or upload an image.');
        return;
    }

    document.getElementById('circularity-loading').classList.remove('hidden');
    document.getElementById('circularity-results').classList.add('hidden');

    try {
        const payload = {
            description: description || null,
            image_url: _circularityImageData,
            organization_id: currentOrg,
        };
        const data = await apiPost('/api/circularity/analyze', payload);

        document.getElementById('circularity-loading').classList.add('hidden');

        // Analysis grid
        const analysisItems = [
            { label: 'Object', value: data.detected_object },
            { label: 'Category', value: data.detected_category || 'Other' },
            { label: 'Material', value: data.detected_material },
            { label: 'Condition', value: data.detected_condition },
            { label: 'Damage', value: data.detected_damage || 'None detected' },
            { label: 'Repairability', value: data.repairability },
            { label: 'Structural Integrity', value: data.structural_integrity || 'Unknown' },
            { label: 'Est. Remaining Life', value: (data.estimated_remaining_life_months == null || data.estimated_remaining_life_months === 'null') ? 'Unknown' : (typeof data.estimated_remaining_life_months === 'number' ? `${data.estimated_remaining_life_months} months` : data.estimated_remaining_life_months) },
            { label: 'Confidence', value: `${Math.round((data.confidence || 0) * 100)}%` },
        ];
        document.getElementById('circularity-analysis-grid').innerHTML = analysisItems.map(item => `
            <div class="bg-surface-50 rounded-xl p-3">
                <p class="text-[10px] text-gray-500 uppercase tracking-wider">${item.label}</p>
                <p class="text-sm font-semibold text-gray-900 mt-0.5">${item.value}</p>
            </div>
        `).join('');

        const actionColors = {
            'REPAIR': 'bg-blue-600', 'REUSE': 'bg-green-600', 'REDISTRIBUTE': 'bg-brand-600',
            'REPURPOSE': 'bg-purple-600', 'DONATE': 'bg-amber-600', 'RECYCLE': 'bg-teal-600', 'DISPOSE': 'bg-gray-600',
        };

        // Primary recommendation
        const rec = data.recommendations[0];
        if (rec) {
            document.getElementById('circularity-recommended').innerHTML = `
                <div class="flex items-center gap-3">
                    <span class="px-4 py-2 ${actionColors[rec.action] || 'bg-gray-600'} text-white rounded-xl text-lg font-bold">${rec.action}</span>
                </div>
            `;
        }

        // Recommendation path
        const path = data.recommendation_path || [data.recommended_action];
        if (path.length > 1) {
            document.getElementById('circularity-path').innerHTML = `
                <p class="text-sm text-gray-700">Recommended path: <strong>${path.join(' → ')}</strong></p>
            `;
        } else {
            document.getElementById('circularity-path').innerHTML = '';
        }

        // Suitability score
        document.getElementById('circularity-score').innerHTML = `
            <div class="flex items-center gap-3">
                <span class="text-sm text-gray-600">Suitability Score:</span>
                <div class="flex-1 max-w-xs"><div class="score-bar h-3"><div class="score-fill ${(data.suitability_score||0) >= 70 ? 'bg-green-500' : (data.suitability_score||0) >= 40 ? 'bg-amber-500' : 'bg-red-500'}" style="width:${data.suitability_score||0}%"></div></div></div>
                <span class="text-sm font-bold text-gray-900">${data.suitability_score || 0}/100</span>
            </div>
        `;

        // Why factors
        const why = data.why_factors || [];
        document.getElementById('circularity-why').innerHTML = why.map(f => `
            <li class="flex items-start gap-2 text-sm text-gray-700">
                <span class="text-green-600 mt-0.5">✓</span>
                <span>${f}</span>
            </li>
        `).join('') || '<li class="text-sm text-gray-500">No specific factors identified.</li>';

        // Explanation
        document.getElementById('circularity-explanation').textContent = data.reason || rec?.explanation || '';

        // Next Actions — context-sensitive buttons
        const primaryAction = (data.recommended_action || '').toUpperCase();
        let actionsHtml = '';
        if (primaryAction === 'REPAIR') {
            actionsHtml = `
                <button class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium">Request Repair</button>
                <button class="px-4 py-2 border border-surface-300 hover:bg-surface-50 text-gray-700 rounded-lg text-sm font-medium">Contact Maintenance Authority</button>
            `;
        } else if (primaryAction === 'REDISTRIBUTE' || primaryAction === 'REUSE') {
            actionsHtml = `
                <button class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-sm font-medium">Request This Resource</button>
                <button class="px-4 py-2 border border-surface-300 hover:bg-surface-50 text-gray-700 rounded-lg text-sm font-medium">Contact Resource Authority</button>
            `;
        } else if (primaryAction === 'RECYCLE') {
            actionsHtml = `
                <button class="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-medium">Request Recycling</button>
                <button class="px-4 py-2 border border-surface-300 hover:bg-surface-50 text-gray-700 rounded-lg text-sm font-medium">Contact Recycling Authority</button>
            `;
        } else if (primaryAction === 'REPURPOSE') {
            actionsHtml = `
                <button class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium">Request Repurposing</button>
                <button class="px-4 py-2 border border-surface-300 hover:bg-surface-50 text-gray-700 rounded-lg text-sm font-medium">Contact Circularity Coordinator</button>
            `;
        } else if (primaryAction === 'DONATE') {
            actionsHtml = `
                <button class="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-medium">Request Donation</button>
                <button class="px-4 py-2 border border-surface-300 hover:bg-surface-50 text-gray-700 rounded-lg text-sm font-medium">Contact Circularity Coordinator</button>
            `;
        } else {
            actionsHtml = `
                <button class="px-4 py-2 border border-surface-300 hover:bg-surface-50 text-gray-700 rounded-lg text-sm font-medium">Contact Resource Authority</button>
            `;
        }
        document.getElementById('circularity-actions').innerHTML = actionsHtml;

        // Alternatives
        const alts = data.recommendations.slice(1);
        document.getElementById('circularity-alternatives').innerHTML = alts.map(r => `
            <div class="flex items-center gap-3 p-3 bg-surface-50 rounded-lg">
                <span class="text-sm font-bold text-gray-700 w-28">${r.action}</span>
                <div class="flex-1">
                    <div class="score-bar mb-1"><div class="score-fill ${r.score >= 70 ? 'bg-green-400' : r.score >= 40 ? 'bg-amber-400' : 'bg-red-400'}" style="width:${r.score}%"></div></div>
                    <p class="text-xs text-gray-600">${r.explanation}</p>
                </div>
                <span class="text-sm font-semibold text-gray-600 w-12 text-right">${r.score}%</span>
            </div>
        `).join('');

        document.getElementById('circularity-results').classList.remove('hidden');
    } catch (err) {
        document.getElementById('circularity-loading').classList.add('hidden');
        alert('Error: ' + err.message);
    }
}

// ═══════════════ NETWORK ═══════════════

async function loadNetwork() {
    const data = await apiGet('/api/organizations/network/overview');
    if (!data) return;

    const container = document.getElementById('network-content');
    let html = '';

    // Organization cards
    html += '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">';
    for (const node of data.nodes) {
        const org = node.organization;
        const supplyBadge = node.potential_supply ? '<span class="px-2 py-0.5 bg-green-100 text-green-700 text-[10px] font-medium rounded-full">Potential Supplier</span>' : '';
        const demandBadge = node.potential_demand ? '<span class="px-2 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-medium rounded-full">Potential Demand</span>' : '';
        html += `
            <div class="bg-white rounded-2xl border border-surface-200 p-5 card-hover transition-all">
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-10 h-10 bg-brand-100 rounded-xl flex items-center justify-center text-brand-700 font-bold text-sm">${org.name[0]}</div>
                    <div>
                        <h4 class="font-semibold text-gray-900">${org.name}</h4>
                        <p class="text-xs text-gray-500">${org.description || ''}</p>
                    </div>
                </div>
                <div class="grid grid-cols-3 gap-2 mb-3">
                    <div class="text-center bg-surface-50 rounded-lg p-2">
                        <p class="text-lg font-bold text-gray-900">${node.resources_total}</p>
                        <p class="text-[10px] text-gray-500">Total</p>
                    </div>
                    <div class="text-center bg-green-50 rounded-lg p-2">
                        <p class="text-lg font-bold text-green-700">${node.resources_shareable}</p>
                        <p class="text-[10px] text-gray-500">Shareable</p>
                    </div>
                    <div class="text-center bg-amber-50 rounded-lg p-2">
                        <p class="text-lg font-bold text-amber-700">${node.underutilized_count}</p>
                        <p class="text-[10px] text-gray-500">Underused</p>
                    </div>
                </div>
                <div class="flex gap-2 flex-wrap">${supplyBadge}${demandBadge}</div>
            </div>
        `;
    }
    html += '</div>';

    // Connections
    if (data.connections.length > 0) {
        html += '<h3 class="text-lg font-semibold text-gray-900 mb-4">Potential Connections</h3>';
        html += '<div class="space-y-3">';
        for (const conn of data.connections) {
            html += `
                <div class="bg-white rounded-xl border border-surface-200 p-4 flex items-center gap-4">
                    <div class="w-10 h-10 bg-brand-50 rounded-full flex items-center justify-center">
                        <svg class="w-5 h-5 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/></svg>
                    </div>
                    <div class="flex-1">
                        <p class="text-sm font-medium text-gray-900">${conn.from_organization} → ${conn.to_organization}</p>
                        <p class="text-xs text-gray-500">${conn.available_resources} shareable resources available for potential transfer</p>
                    </div>
                    <span class="px-3 py-1 bg-brand-50 text-brand-700 text-xs font-medium rounded-lg">Potential Match</span>
                </div>
            `;
        }
        html += '</div>';
    } else {
        html += '<p class="text-sm text-gray-400 text-center py-8">No cross-organization connections identified yet.</p>';
    }

    container.innerHTML = html;
}

// ═══════════════ DOCUMENTS ═══════════════

async function loadDocuments() {
    const data = await apiGet(`/api/documents?organization_id=${currentOrg}`);
    if (!data) return;

    const list = document.getElementById('document-list');
    if (data.length === 0) {
        list.innerHTML = '<p class="text-sm text-gray-400">No documents uploaded yet.</p>';
    } else {
        list.innerHTML = data.map(d => `
            <div class="flex items-center gap-3 p-3 bg-surface-50 rounded-lg">
                <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-gray-900">${d.name}</p>
                    <p class="text-xs text-gray-500">${d.category || 'Uncategorized'} · ${d.chunk_count} chunks · ${d.status}</p>
                </div>
                <span class="px-2 py-0.5 ${d.status === 'processed' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'} text-xs rounded-full font-medium">${d.status}</span>
            </div>
        `).join('');
    }
}

function fillRAGExample(n) {
    const examples = {
        1: "Can a department transfer unused computers to another department?",
        2: "What are the procurement rules for equipment over €500?",
        3: "How often should electronic equipment be maintained?"
    };
    document.getElementById('rag-query').value = examples[n];
}

async function queryRAG() {
    const query = document.getElementById('rag-query').value.trim();
    if (!query) return;

    try {
        const data = await apiPost('/api/documents/query', {
            query: query,
            organization_id: currentOrg,
        });

        document.getElementById('rag-answer').textContent = data.answer;
        document.getElementById('rag-sources').innerHTML = (data.sources || []).map(s => `
            <div class="bg-white rounded-lg p-3 border border-surface-200">
                <p class="text-xs text-gray-500">Source: Document #${s.document_id} (Chunk #${s.chunk_id})</p>
                <p class="text-xs text-gray-700 mt-1">${s.snippet}</p>
            </div>
        `).join('');
        document.getElementById('rag-disclaimer').textContent = data.disclaimer || '';
        document.getElementById('rag-results').classList.remove('hidden');
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

// ═══════════════ IMPACT ═══════════════

async function loadImpact() {
    const data = await apiGet(`/api/impact?organization_id=${currentOrg}`);
    if (!data) return;

    const s = data.summary;
    const env = data.environmental_details;
    const fin = data.financial_details;

    const container = document.getElementById('impact-content');
    container.innerHTML = `
        <!-- Key Metrics -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-white rounded-xl border border-surface-200 p-5">
                <p class="text-xs font-medium text-gray-500 uppercase">Resources Reused</p>
                <p class="text-3xl font-bold text-green-600 mt-1">${formatNumber(s.resources_reused)}</p>
            </div>
            <div class="bg-white rounded-xl border border-surface-200 p-5">
                <p class="text-xs font-medium text-gray-500 uppercase">Resources Repaired</p>
                <p class="text-3xl font-bold text-blue-600 mt-1">${formatNumber(s.resources_repaired)}</p>
            </div>
            <div class="bg-white rounded-xl border border-surface-200 p-5">
                <p class="text-xs font-medium text-gray-500 uppercase">Resources Redistributed</p>
                <p class="text-3xl font-bold text-brand-600 mt-1">${formatNumber(s.resources_redistributed)}</p>
            </div>
            <div class="bg-white rounded-xl border border-surface-200 p-5">
                <p class="text-xs font-medium text-gray-500 uppercase">Purchases Avoided</p>
                <p class="text-3xl font-bold text-purple-600 mt-1">${formatNumber(s.purchases_avoided)}</p>
            </div>
        </div>

        <!-- Financial + Environmental -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div class="bg-white rounded-2xl border border-surface-200 p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Financial Impact</h3>
                <div class="space-y-3">
                    <div class="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                        <span class="text-sm text-gray-700">Estimated Cost Avoided</span>
                        <span class="text-lg font-bold text-green-700">${formatCurrency(s.cost_avoided)}</span>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-surface-50 rounded-lg">
                        <span class="text-sm text-gray-700">Avg. Savings per Resource</span>
                        <span class="text-lg font-bold text-gray-900">${formatCurrency(fin.avg_savings_per_resource)}</span>
                    </div>
                </div>
                <p class="text-[10px] text-gray-400 mt-3">${fin.methodology}</p>
            </div>
            <div class="bg-white rounded-2xl border border-surface-200 p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Environmental Impact</h3>
                <div class="space-y-3">
                    <div class="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                        <span class="text-sm text-gray-700">CO₂ Emissions Prevented</span>
                        <span class="text-lg font-bold text-green-700">${formatNumber(s.co2_saved_kg)} kg</span>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-surface-50 rounded-lg">
                        <span class="text-sm text-gray-700">Waste Diverted from Landfill</span>
                        <span class="text-lg font-bold text-gray-900">${formatNumber(s.waste_avoided_kg)} kg</span>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-surface-50 rounded-lg">
                        <span class="text-sm text-gray-700">Trees Equivalent Saved</span>
                        <span class="text-lg font-bold text-gray-900">${env.trees_equivalent || 0}</span>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-surface-50 rounded-lg">
                        <span class="text-sm text-gray-700">Car km Equivalent</span>
                        <span class="text-lg font-bold text-gray-900">${formatNumber(env.car_km_equivalent || 0)} km</span>
                    </div>
                </div>
                <p class="text-[10px] text-gray-400 mt-3">${env.methodology}</p>
            </div>
        </div>

        <!-- Assumptions -->
        <div class="bg-white rounded-2xl border border-surface-200 p-6 mb-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Calculation Assumptions</h3>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                ${Object.entries(s.assumptions || {}).map(([k, v]) => `
                    <div class="bg-surface-50 rounded-lg p-3">
                        <p class="text-xs text-gray-500">${k.replace(/_/g, ' ')}</p>
                        <p class="text-sm font-semibold text-gray-900">${typeof v === 'number' ? v.toFixed(1) : v}</p>
                    </div>
                `).join('')}
            </div>
        </div>

        <!-- SDG Alignment -->
        <div class="bg-white rounded-2xl border border-surface-200 p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">SDG Alignment</h3>
            <div class="space-y-2">
                ${Object.entries(data.sdg_alignment || {}).map(([sdg, desc]) => `
                    <div class="flex items-center gap-3 p-3 bg-brand-50 rounded-lg">
                        <span class="px-3 py-1 bg-brand-500 text-white text-xs font-bold rounded-lg">${sdg}</span>
                        <span class="text-sm text-gray-700">${desc}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// ═══════════════ IMPORT ═══════════════
let _currentImportId = null;

function showImportModal() {
    document.getElementById('import-preview').classList.add('hidden');
    document.getElementById('import-confirm-btn').classList.add('hidden');
    document.getElementById('import-upload-area').classList.remove('hidden');
    document.getElementById('import-file').value = '';
    _currentImportId = null;
    document.getElementById('import-modal').classList.remove('hidden');
}

async function previewImport(input) {
    if (!input.files[0]) return;
    const formData = new FormData();
    formData.append('file', input.files[0]);
    formData.append('organization_id', currentOrg);

    try {
        const data = await apiPostForm('/api/upload/import/preview', formData);
        _currentImportId = data.import_id;
        document.getElementById('import-upload-area').classList.add('hidden');
        const preview = document.getElementById('import-preview');
        preview.classList.remove('hidden');

        let html = `
            <div class="bg-surface-50 rounded-xl p-4 mb-4">
                <div class="flex items-center justify-between mb-2">
                    <p class="text-xs font-medium text-gray-500">Import ID: <strong class="text-gray-900">${data.import_id}</strong></p>
                    <p class="text-xs text-gray-500">${data.filename}</p>
                </div>
                <div class="grid grid-cols-3 gap-4 text-center">
                    <div><p class="text-2xl font-bold text-gray-900">${data.total_rows}</p><p class="text-xs text-gray-500">Total Rows</p></div>
                    <div><p class="text-2xl font-bold text-green-600">${data.valid_rows}</p><p class="text-xs text-gray-500">Valid</p></div>
                    <div><p class="text-2xl font-bold text-red-500">${data.invalid_rows}</p><p class="text-xs text-gray-500">Invalid</p></div>
                </div>
            </div>
        `;

        if (data.errors && data.errors.length > 0) {
            html += '<div class="bg-red-50 rounded-xl p-3 mb-4"><p class="text-xs font-medium text-red-700 mb-1">Errors:</p>';
            data.errors.forEach(e => {
                html += `<p class="text-xs text-red-600">Row ${e.row}: ${e.error || (e.errors || []).join(', ')}</p>`;
            });
            html += '</div>';
        }

        preview.innerHTML = html;

        if (data.valid_rows > 0) {
            document.getElementById('import-confirm-btn').classList.remove('hidden');
        }
    } catch (err) {
        alert('Error parsing file: ' + err.message);
    }
}

async function confirmImport() {
    if (!_currentImportId) {
        alert('Please upload a file first.');
        return;
    }
    try {
        const data = await apiPost('/api/upload/import/confirm', {
            import_id: _currentImportId,
            organization_id: currentOrg,
        });
        alert(data.message || `Import complete! ${data.imported} imported, ${data.rejected} rejected.`);
        closeModal('import-modal');
        _currentImportId = null;
        loadResources();
    } catch (err) {
        alert('Import error: ' + err.message);
    }
}

// ═══════════════ ADD RESOURCE ═══════════════

function showAddResourceModal() {
    document.getElementById('add-resource-form').reset();
    document.getElementById('add-resource-modal').classList.remove('hidden');
}

async function submitNewResource() {
    const form = document.getElementById('add-resource-form');
    const fd = new FormData(form);
    const data = {
        resource_id: fd.get('resource_id'),
        name: fd.get('name'),
        category: fd.get('category'),
        type: fd.get('type'),
        description: fd.get('description'),
        condition: fd.get('condition'),
        availability: fd.get('availability'),
        utilization: parseInt(fd.get('utilization') || '0'),
        location: fd.get('location'),
        organization_id: currentOrg,
        department_id: parseInt(fd.get('department_id') || '1'),
        remaining_useful_life_months: parseInt(fd.get('remaining_useful_life_months') || '36'),
        specifications: {},
    };

    if (!data.resource_id || !data.name || !data.type) {
        alert('Please fill in required fields (Resource ID, Name, Type).');
        return;
    }

    try {
        await apiPost('/api/resources', data);
        closeModal('add-resource-modal');
        loadResources();
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

// ═══════════════ UPLOAD DOCUMENT ═══════════════

function showUploadDocModal() {
    document.getElementById('doc-name').value = '';
    document.getElementById('doc-file').value = '';
    document.getElementById('upload-doc-modal').classList.remove('hidden');
}

async function uploadDocument() {
    const name = document.getElementById('doc-name').value.trim();
    const category = document.getElementById('doc-category').value;
    const file = document.getElementById('doc-file').files[0];

    if (!name || !file) {
        alert('Please provide a name and select a file.');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    formData.append('category', category);
    formData.append('organization_id', currentOrg);

    try {
        await apiPostForm('/api/documents/upload', formData);
        closeModal('upload-doc-modal');
        loadDocuments();
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

// ═══════════════ MODALS ═══════════════

function showModal(id, html) {
    let modal = document.getElementById(id);
    if (!modal) {
        modal = document.createElement('div');
        modal.id = id;
        modal.className = 'fixed inset-0 bg-black/40 z-50 hidden flex items-center justify-center';
        document.body.appendChild(modal);
    }
    modal.innerHTML = `<div class="bg-white rounded-2xl w-full max-w-2xl mx-4 p-6 max-h-[85vh] overflow-y-auto">${html}</div>`;
    modal.classList.remove('hidden');
    modal.onclick = (e) => { if (e.target === modal) closeModal(id); };
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('hidden');
}

// ═══════════════ UTILS ═══════════════

function debounce(fn, ms) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), ms);
    };
}

// ═══════════════ REQUEST MODAL ═══════════════
let _requestMatch = null;

function openRequestModal(match) {
    _requestMatch = match;
    const html = `
        <div class="space-y-4">
            <div class="flex items-start justify-between">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900">Request This Resource</h3>
                    <p class="text-sm text-gray-500">Submit a transfer request to the resource authority.</p>
                </div>
                <button onclick="closeModal('request-modal')" class="p-2 hover:bg-surface-100 rounded-lg">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
            </div>
            <div class="bg-surface-50 rounded-xl p-4">
                <p class="text-xs text-gray-500 uppercase mb-1">Resource</p>
                <p class="text-sm font-semibold text-gray-900">${match.resource_name}</p>
                <p class="text-xs text-gray-500">${match.resource_code} · ${match.department_name} · ${match.location || ''}</p>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="text-xs font-medium text-gray-600 block mb-1">Your Organization</label>
                    <input id="req-org" value="ITER" class="w-full border border-surface-300 rounded-lg px-3 py-2 text-sm bg-surface-50" readonly>
                </div>
                <div>
                    <label class="text-xs font-medium text-gray-600 block mb-1">Your Department</label>
                    <input id="req-dept" value="Computer Science" class="w-full border border-surface-300 rounded-lg px-3 py-2 text-sm bg-surface-50" readonly>
                </div>
            </div>
            <div>
                <label class="text-xs font-medium text-gray-600 block mb-1">Reason for Request *</label>
                <textarea id="req-reason" rows="3" class="w-full border border-surface-300 rounded-lg px-3 py-2 text-sm outline-none focus:border-brand-400 resize-none" placeholder="Why do you need this resource?"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="text-xs font-medium text-gray-600 block mb-1">Quantity Needed</label>
                    <input id="req-qty" type="number" value="1" min="1" class="w-full border border-surface-300 rounded-lg px-3 py-2 text-sm">
                </div>
                <div>
                    <label class="text-xs font-medium text-gray-600 block mb-1">Required By</label>
                    <input id="req-by" type="date" class="w-full border border-surface-300 rounded-lg px-3 py-2 text-sm">
                </div>
            </div>
            <div>
                <label class="text-xs font-medium text-gray-600 block mb-1">Additional Message</label>
                <textarea id="req-msg" rows="2" class="w-full border border-surface-300 rounded-lg px-3 py-2 text-sm outline-none focus:border-brand-400 resize-none" placeholder="Any additional details..."></textarea>
            </div>
            <div id="req-summary" class="hidden bg-brand-50 rounded-xl p-4">
                <h4 class="text-sm font-semibold text-brand-800 mb-2">Request Summary</h4>
                <div class="text-sm text-brand-700 space-y-1"></div>
            </div>
            <div id="req-success" class="hidden bg-green-50 rounded-xl p-4 text-center">
                <p class="text-sm font-medium text-green-800">Resource request submitted successfully.</p>
                <p class="text-lg font-bold text-green-700 mt-1" id="req-success-id"></p>
                <p class="text-xs text-green-600 mt-1">Status: Pending Owner Approval</p>
            </div>
            <div id="req-error" class="hidden bg-red-50 rounded-xl p-4">
                <p class="text-sm font-medium text-red-700" id="req-error-msg"></p>
            </div>
            <div class="flex justify-end gap-3" id="req-actions">
                <button onclick="closeModal('request-modal')" class="px-4 py-2 text-sm text-gray-600 border rounded-lg hover:bg-surface-50">Cancel</button>
                <button onclick="submitRequest()" class="px-6 py-2 bg-brand-500 text-white rounded-lg text-sm font-medium hover:bg-brand-600">Submit Request</button>
            </div>
        </div>
    `;
    showModal('request-modal', html);
}

async function submitRequest() {
    const reason = document.getElementById('req-reason').value.trim();
    if (!reason) { alert('Please enter a reason.'); return; }

    const data = {
        resource_id: _requestMatch.resource_id,
        requester_id: 1,  // Default user
        requester_organization_id: currentOrg,
        requester_department_id: 1,
        reason: reason,
        quantity: parseInt(document.getElementById('req-qty').value) || 1,
        required_by: document.getElementById('req-by').value || null,
        message: document.getElementById('req-msg').value.trim(),
    };

    try {
        const res = await apiPost('/api/requests', data);
        document.getElementById('req-actions').classList.add('hidden');
        document.getElementById('req-success-id').textContent = res.request_id;
        document.getElementById('req-success').classList.remove('hidden');
        document.getElementById('req-error').classList.add('hidden');
    } catch (err) {
        document.getElementById('req-error-msg').textContent = err.message;
        document.getElementById('req-error').classList.remove('hidden');
    }
}

// ═══════════════ CONTACT MODAL ═══════════════

function openContactModal(match) {
    const html = `
        <div class="space-y-4">
            <div class="flex items-start justify-between">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900">Contact Resource Authority</h3>
                    <p class="text-sm text-gray-500">Send a message about this resource.</p>
                </div>
                <button onclick="closeModal('contact-modal')" class="p-2 hover:bg-surface-100 rounded-lg">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
            </div>
            <div class="bg-surface-50 rounded-xl p-4 space-y-2">
                <div><p class="text-xs text-gray-500">Resource</p><p class="text-sm font-semibold text-gray-900">${match.resource_name} (${match.resource_code})</p></div>
                <div><p class="text-xs text-gray-500">Department</p><p class="text-sm font-medium text-gray-700">${match.department_name}</p></div>
                <div><p class="text-xs text-gray-500">Location</p><p class="text-sm font-medium text-gray-700">${match.location || '—'}</p></div>
            </div>
            <div class="bg-surface-50 rounded-xl p-4">
                <p class="text-xs text-gray-500 mb-1">Resource Authority</p>
                <p class="text-sm font-semibold text-gray-900">${match.department_name} Department</p>
                <p class="text-xs text-gray-500">Contact the department responsible for this resource.</p>
            </div>
            <div>
                <label class="text-xs font-medium text-gray-600 block mb-1">Your Name *</label>
                <input id="contact-name" class="w-full border border-surface-300 rounded-lg px-3 py-2 text-sm" placeholder="Your name">
            </div>
            <div>
                <label class="text-xs font-medium text-gray-600 block mb-1">Your Email *</label>
                <input id="contact-email" type="email" class="w-full border border-surface-300 rounded-lg px-3 py-2 text-sm" placeholder="your@email.com">
            </div>
            <div>
                <label class="text-xs font-medium text-gray-600 block mb-1">Message *</label>
                <textarea id="contact-msg" rows="4" class="w-full border border-surface-300 rounded-lg px-3 py-2 text-sm outline-none focus:border-brand-400 resize-none" placeholder="Your message about this resource..."></textarea>
            </div>
            <div id="contact-success" class="hidden bg-green-50 rounded-xl p-4 text-center">
                <p class="text-sm font-medium text-green-800">Message sent to the resource authority.</p>
            </div>
            <div id="contact-error" class="hidden bg-red-50 rounded-xl p-4">
                <p class="text-sm font-medium text-red-700" id="contact-error-msg"></p>
            </div>
            <div class="flex justify-end gap-3" id="contact-actions">
                <button onclick="closeModal('contact-modal')" class="px-4 py-2 text-sm text-gray-600 border rounded-lg hover:bg-surface-50">Cancel</button>
                <button onclick="sendContact(${match.resource_id})" class="px-6 py-2 bg-brand-500 text-white rounded-lg text-sm font-medium hover:bg-brand-600">Send Message</button>
            </div>
        </div>
    `;
    showModal('contact-modal', html);
}

async function sendContact(resourceId) {
    const name = document.getElementById('contact-name').value.trim();
    const email = document.getElementById('contact-email').value.trim();
    const msg = document.getElementById('contact-msg').value.trim();
    if (!name || !email || !msg) { alert('Please fill in all fields.'); return; }

    try {
        await apiPost('/api/requests/contact', {
            resource_id: resourceId,
            sender_name: name,
            sender_email: email,
            message: msg,
        });
        document.getElementById('contact-actions').classList.add('hidden');
        document.getElementById('contact-success').classList.remove('hidden');
        document.getElementById('contact-error').classList.add('hidden');
    } catch (err) {
        document.getElementById('contact-error-msg').textContent = err.message;
        document.getElementById('contact-error').classList.remove('hidden');
    }
}

// ═══════════════ INIT ═══════════════

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});
