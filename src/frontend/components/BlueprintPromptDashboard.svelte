<!--
  Blueprint-themed Prompt Management Dashboard
  Inspired by Artifex Hackworth's technical precision
  Subtle tojo.world branding integration
-->
<script>
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import PromptVersioning from './PromptVersioning.svelte';
  import PromptTemplateBuilder from './PromptTemplateBuilder.svelte';
  import PromptCategoryManager from './PromptCategoryManager.svelte';
  
  // Import blueprint theme
  import '../styles/blueprint-theme.css';
  
  // Active view management
  const activeView = writable('dashboard');
  const selectedPromptId = writable(null);
  const showCreatePrompt = writable(false);
  
  // Dashboard data
  const dashboardData = writable({
    totalPrompts: 0,
    totalVersions: 0,
    totalCategories: 0,
    recentPrompts: [],
    recentVersions: [],
    popularCategories: []
  });
  
  const loading = writable(false);
  const error = writable(null);
  
  // API base
  const API_BASE = '/api/v1/prompts';
  
  onMount(() => {
    loadDashboardData();
  });
  
  // API Functions
  async function loadDashboardData() {
    $loading = true;
    $error = null;
    
    try {
      // Load categories
      const categoriesResponse = await fetch(`${API_BASE}/categories`);
      const categoriesResult = await categoriesResponse.json();
      
      // For demo purposes, we'll simulate other data
      const data = {
        totalPrompts: 47, // Demo data
        totalVersions: 156, // Demo data
        totalCategories: categoriesResult.success ? categoriesResult.count : 8,
        recentPrompts: [], // Would come from recent prompts API
        recentVersions: [], // Would come from recent versions API
        popularCategories: categoriesResult.success ? categoriesResult.categories.slice(0, 5) : [
          { name: 'Technical', color: '#003d7a', description: 'Engineering and development prompts' },
          { name: 'Analysis', color: '#0066cc', description: 'Data analysis and research' },
          { name: 'Design', color: '#ff6b35', description: 'UI/UX and creative prompts' }
        ]
      };
      
      dashboardData.set(data);
    } catch (err) {
      $error = 'Failed to load dashboard data: ' + err.message;
    } finally {
      $loading = false;
    }
  }
  
  // Navigation functions
  function showDashboard() {
    activeView.set('dashboard');
    selectedPromptId.set(null);
  }
  
  function showVersioning(promptId = null) {
    activeView.set('versioning');
    selectedPromptId.set(promptId);
  }
  
  function showTemplateBuilder() {
    activeView.set('template-builder');
    selectedPromptId.set(null);
  }
  
  function showCategoryManager() {
    activeView.set('categories');
    selectedPromptId.set(null);
  }
  
  // Template builder save handler
  async function handleTemplateSave(templateData) {
    console.log('Saving template:', templateData);
    await new Promise(resolve => setTimeout(resolve, 1000));
    await loadDashboardData();
  }
  
  // Helper functions
  function formatNumber(num) {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }
  
  function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  }
</script>

<div class="blueprint-dashboard blueprint-grid">
  <!-- Blueprint Header with Technical Drawing Style -->
  <header class="blueprint-nav">
    <div class="header-content">
      <div class="brand-section">
        <div class="brand-header">
          <div class="tojo-compass"></div>
          <div class="brand-text">
            <h1 class="blueprint-title">Prompt Management System</h1>
            <p class="blueprint-subtitle">Technical Specification & Control Interface</p>
          </div>
        </div>
        <div class="drawing-info">
          <span class="drawing-number">DWG-001</span>
          <span class="revision">Rev. 1.0</span>
        </div>
      </div>
      
      <nav class="technical-nav">
        <button 
          class="blueprint-nav-item"
          class:active={$activeView === 'dashboard'}
          on:click={showDashboard}
        >
          Dashboard
        </button>
        
        <button 
          class="blueprint-nav-item"
          class:active={$activeView === 'versioning'}
          on:click={() => showVersioning()}
        >
          Versioning
        </button>
        
        <button 
          class="blueprint-nav-item"
          class:active={$activeView === 'template-builder'}
          on:click={showTemplateBuilder}
        >
          Template Builder
        </button>
        
        <button 
          class="blueprint-nav-item"
          class:active={$activeView === 'categories'}
          on:click={showCategoryManager}
        >
          Categories
        </button>
      </nav>
    </div>
  </header>
  
  <!-- Main Technical Drawing Area -->
  <main class="blueprint-workspace paper-surface">
    {#if $activeView === 'dashboard'}
      <!-- Technical Dashboard Layout -->
      <div class="technical-overview">
        <!-- System Metrics Panel -->
        <section class="metrics-panel blueprint-card">
          <div class="blueprint-card-header">
            <h2 class="section-title">System Metrics</h2>
            <div class="metric-legend">
              <span class="legend-item">● Active</span>
              <span class="legend-item">○ Total</span>
            </div>
          </div>
          <div class="blueprint-card-content">
            <div class="metrics-grid">
              <div class="blueprint-metric">
                <div class="blueprint-metric-value">{formatNumber($dashboardData.totalPrompts)}</div>
                <div class="blueprint-metric-label">Total Prompts</div>
                <div class="metric-indicator"></div>
              </div>
              
              <div class="blueprint-metric">
                <div class="blueprint-metric-value">{formatNumber($dashboardData.totalVersions)}</div>
                <div class="blueprint-metric-label">Version Count</div>
                <div class="metric-indicator"></div>
              </div>
              
              <div class="blueprint-metric">
                <div class="blueprint-metric-value">{formatNumber($dashboardData.totalCategories)}</div>
                <div class="blueprint-metric-label">Categories</div>
                <div class="metric-indicator"></div>
              </div>
              
              <div class="blueprint-metric action-metric" on:click={showTemplateBuilder}>
                <div class="blueprint-metric-value">+</div>
                <div class="blueprint-metric-label">Create New</div>
                <div class="metric-indicator active"></div>
              </div>
            </div>
          </div>
        </section>
        
        <!-- Technical Operations Panel -->
        <section class="operations-panel blueprint-card">
          <div class="blueprint-card-header">
            <h2 class="section-title">System Operations</h2>
            <div class="operation-status">
              <span class="status-indicator active"></span>
              <span>Online</span>
            </div>
          </div>
          <div class="blueprint-card-content">
            <div class="operations-grid">
              <button class="blueprint-button primary" on:click={showTemplateBuilder}>
                <div class="button-icon">⚡</div>
                <div class="button-content">
                  <span class="button-title">Initialize Template</span>
                  <span class="button-desc">Create new prompt template</span>
                </div>
                <div class="blueprint-arrow"></div>
              </button>
              
              <button class="blueprint-button" on:click={showCategoryManager}>
                <div class="button-icon">⚙</div>
                <div class="button-content">
                  <span class="button-title">Configure Categories</span>
                  <span class="button-desc">Manage classification system</span>
                </div>
                <div class="blueprint-arrow"></div>
              </button>
              
              <button class="blueprint-button" on:click={() => showVersioning()}>
                <div class="button-icon">🔄</div>
                <div class="button-content">
                  <span class="button-title">Version Control</span>
                  <span class="button-desc">Manage template revisions</span>
                </div>
                <div class="blueprint-arrow"></div>
              </button>
              
              <button class="blueprint-button">
                <div class="button-icon">📊</div>
                <div class="button-content">
                  <span class="button-title">Analytics Dashboard</span>
                  <span class="button-desc">Performance metrics</span>
                </div>
                <div class="blueprint-arrow"></div>
              </button>
            </div>
          </div>
        </section>
        
        <!-- Technical Specifications Grid -->
        <div class="specifications-grid">
          <!-- Category Specifications -->
          <section class="spec-panel blueprint-card">
            <div class="blueprint-card-header">
              <h2 class="section-title">Category Specifications</h2>
              <button class="blueprint-button small" on:click={showCategoryManager}>
                Configure
              </button>
            </div>
            <div class="blueprint-card-content">
              {#if $dashboardData.popularCategories.length > 0}
                <div class="category-specifications">
                  {#each $dashboardData.popularCategories as category}
                    <div class="category-spec" style="border-left: 3px solid {category.color}">
                      <div class="spec-header">
                        <div class="spec-name">{category.name}</div>
                        <div class="spec-indicator" style="background: {category.color}">
                          {category.name.charAt(0)}
                        </div>
                      </div>
                      {#if category.description}
                        <div class="spec-description">{category.description}</div>
                      {/if}
                      <div class="spec-meta">
                        <span class="spec-code">CAT-{category.name.toUpperCase().substring(0,3)}</span>
                      </div>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="empty-specification">
                  <div class="empty-icon">📋</div>
                  <p>No category specifications defined.</p>
                  <button class="blueprint-button small" on:click={showCategoryManager}>
                    Initialize Categories
                  </button>
                </div>
              {/if}
            </div>
          </section>
          
          <!-- Recent Activity Log -->
          <section class="spec-panel blueprint-card">
            <div class="blueprint-card-header">
              <h2 class="section-title">Activity Log</h2>
              <div class="log-timestamp">
                <span class="timestamp-label">Last Update:</span>
                <span class="timestamp-value">{new Date().toLocaleTimeString()}</span>
              </div>
            </div>
            <div class="blueprint-card-content">
              {#if $dashboardData.recentVersions.length > 0}
                <div class="activity-log">
                  {#each $dashboardData.recentVersions as version}
                    <div class="log-entry">
                      <div class="log-indicator"></div>
                      <div class="log-content">
                        <div class="log-title">{version.title}</div>
                        <div class="log-meta">
                          Version {version.version_number} • {formatTimestamp(version.created_at)}
                        </div>
                      </div>
                      <button 
                        class="blueprint-button small"
                        on:click={() => showVersioning(version.prompt_id)}
                      >
                        View
                      </button>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="empty-specification">
                  <div class="empty-icon">📝</div>
                  <p>No recent activity to display.</p>
                  <button class="blueprint-button small primary" on:click={showTemplateBuilder}>
                    Create First Template
                  </button>
                </div>
              {/if}
            </div>
          </section>
        </div>
      </div>
      
    {:else if $activeView === 'versioning'}
      <!-- Technical Drawing Header for Sub-views -->
      <div class="drawing-header">
        <button class="blueprint-button" on:click={showDashboard}>
          ← Return to Overview
        </button>
        <h2 class="drawing-title">Prompt Version Control System</h2>
        <div class="drawing-meta">DWG-002 | Versioning Interface</div>
      </div>
      <PromptVersioning promptId={$selectedPromptId} />
      
    {:else if $activeView === 'template-builder'}
      <div class="drawing-header">
        <button class="blueprint-button" on:click={showDashboard}>
          ← Return to Overview
        </button>
        <h2 class="drawing-title">Template Construction Interface</h2>
        <div class="drawing-meta">DWG-003 | Template Builder</div>
      </div>
      <PromptTemplateBuilder onSave={handleTemplateSave} />
      
    {:else if $activeView === 'categories'}
      <div class="drawing-header">
        <button class="blueprint-button" on:click={showDashboard}>
          ← Return to Overview
        </button>
        <h2 class="drawing-title">Category Management System</h2>
        <div class="drawing-meta">DWG-004 | Category Interface</div>
      </div>
      <PromptCategoryManager />
    {/if}
  </main>
  
  <!-- Technical Error Display -->
  {#if $error}
    <div class="blueprint-error-panel">
      <div class="error-header">
        <span class="error-code">ERR-001</span>
        <span class="error-type">System Alert</span>
        <button class="close-error" on:click={() => error.set(null)}>×</button>
      </div>
      <div class="error-content">
        <div class="error-icon">⚠</div>
        <div class="error-message">{$error}</div>
      </div>
    </div>
  {/if}
  
  <!-- Technical Loading Interface -->
  {#if $loading}
    <div class="blueprint-loading-overlay">
      <div class="loading-interface blueprint-card">
        <div class="blueprint-loading">
          <div class="blueprint-spinner"></div>
          <span>Processing system data...</span>
        </div>
        <div class="loading-progress">
          <div class="progress-bar"></div>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Subtle tojo.world watermark -->
  <div class="tojo-watermark">hosted on tojo.world</div>
</div>

<style>
  /* Blueprint Dashboard Layout */
  .blueprint-dashboard {
    min-height: 100vh;
    background: var(--paper-tertiary);
    position: relative;
    font-family: var(--font-body);
  }
  
  .header-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: var(--spacing-lg) var(--spacing-xl);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .brand-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-xl);
  }
  
  .brand-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }
  
  .brand-text {
    display: flex;
    flex-direction: column;
  }
  
  .blueprint-title {
    margin: 0;
    color: var(--blueprint-primary);
    font-size: 1.75rem;
    font-weight: 700;
    font-family: var(--font-heading);
    letter-spacing: -0.025em;
  }
  
  .blueprint-subtitle {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-family: var(--font-technical);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
  }
  
  .drawing-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-family: var(--font-technical);
    font-size: 11px;
    color: var(--text-tertiary);
    text-align: right;
  }
  
  .drawing-number {
    font-weight: 600;
    color: var(--blueprint-primary);
  }
  
  .technical-nav {
    display: flex;
    gap: 0;
  }
  
  .blueprint-workspace {
    max-width: 1400px;
    margin: 0 auto;
    padding: var(--spacing-xl);
    min-height: calc(100vh - 120px);
  }
  
  /* Technical Overview Layout */
  .technical-overview {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }
  
  .metrics-panel {
    width: 100%;
  }
  
  .section-title {
    margin: 0;
    color: var(--blueprint-primary);
    font-size: 1.125rem;
    font-weight: 600;
    font-family: var(--font-technical);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .metric-legend {
    display: flex;
    gap: var(--spacing-md);
    font-family: var(--font-technical);
    font-size: 10px;
    color: var(--text-tertiary);
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-lg);
  }
  
  .metric-indicator {
    position: absolute;
    top: var(--spacing-sm);
    right: var(--spacing-sm);
    width: 8px;
    height: 8px;
    border: 2px solid var(--line-construction);
    border-radius: 50%;
    background: var(--paper-base);
  }
  
  .metric-indicator.active {
    border-color: var(--blueprint-accent);
    background: var(--blueprint-accent);
  }
  
  .action-metric {
    cursor: pointer;
    border-color: var(--blueprint-primary);
  }
  
  .action-metric:hover {
    border-color: var(--blueprint-secondary);
    box-shadow: var(--shadow-elevation);
  }
  
  .operations-panel {
    width: 100%;
  }
  
  .operation-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: var(--font-technical);
    font-size: 11px;
    color: var(--text-secondary);
  }
  
  .status-indicator {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--line-construction);
  }
  
  .status-indicator.active {
    background: var(--blueprint-accent);
    box-shadow: 0 0 6px var(--blueprint-accent);
  }
  
  .operations-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-lg);
  }
  
  .blueprint-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    text-align: left;
    width: 100%;
  }
  
  .blueprint-button.small {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: 10px;
    min-width: auto;
    width: auto;
  }
  
  .button-icon {
    width: 2.5rem;
    height: 2.5rem;
    background: var(--paper-secondary);
    border: var(--border-weight-thin) solid var(--line-construction);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
  }
  
  .button-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .button-title {
    font-size: 12px;
    font-weight: 600;
    line-height: 1.2;
  }
  
  .button-desc {
    font-size: 10px;
    opacity: 0.8;
    line-height: 1.3;
  }
  
  .specifications-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-xl);
  }
  
  .spec-panel {
    height: fit-content;
  }
  
  .category-specifications {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .category-spec {
    padding: var(--spacing-md);
    background: var(--paper-secondary);
    border: var(--border-weight-thin) solid var(--line-construction);
    border-radius: 4px;
  }
  
  .spec-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xs);
  }
  
  .spec-name {
    font-family: var(--font-technical);
    font-weight: 600;
    color: var(--blueprint-primary);
    font-size: 13px;
  }
  
  .spec-indicator {
    width: 20px;
    height: 20px;
    border-radius: 2px;
    color: white;
    font-size: 10px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .spec-description {
    font-size: 11px;
    color: var(--text-secondary);
    line-height: 1.4;
    margin-bottom: var(--spacing-xs);
  }
  
  .spec-meta {
    display: flex;
    justify-content: flex-end;
  }
  
  .spec-code {
    font-family: var(--font-technical);
    font-size: 9px;
    color: var(--text-tertiary);
    font-weight: 600;
  }
  
  .log-timestamp {
    display: flex;
    gap: 6px;
    font-family: var(--font-technical);
    font-size: 10px;
    color: var(--text-tertiary);
  }
  
  .timestamp-label {
    color: var(--text-secondary);
  }
  
  .timestamp-value {
    color: var(--blueprint-primary);
    font-weight: 600;
  }
  
  .activity-log {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .log-entry {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm);
    background: var(--paper-secondary);
    border: var(--border-weight-thin) solid var(--line-construction);
    border-left: var(--border-weight-medium) solid var(--blueprint-primary);
    border-radius: 2px;
  }
  
  .log-indicator {
    width: 6px;
    height: 6px;
    background: var(--blueprint-accent);
    border-radius: 50%;
    flex-shrink: 0;
  }
  
  .log-content {
    flex: 1;
    min-width: 0;
  }
  
  .log-title {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .log-meta {
    font-family: var(--font-technical);
    font-size: 9px;
    color: var(--text-tertiary);
    margin-top: 2px;
  }
  
  .empty-specification {
    text-align: center;
    padding: var(--spacing-xl) var(--spacing-md);
    color: var(--text-secondary);
  }
  
  .empty-icon {
    font-size: 2rem;
    margin-bottom: var(--spacing-md);
    opacity: 0.5;
  }
  
  .empty-specification p {
    margin: 0 0 var(--spacing-md) 0;
    font-size: 12px;
  }
  
  /* Drawing Header for Sub-views */
  .drawing-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-xl);
    padding-bottom: var(--spacing-lg);
    border-bottom: var(--border-weight-medium) solid var(--blueprint-primary);
  }
  
  .drawing-title {
    margin: 0;
    color: var(--blueprint-primary);
    font-size: 1.5rem;
    font-weight: 700;
    font-family: var(--font-technical);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .drawing-meta {
    margin-left: auto;
    font-family: var(--font-technical);
    font-size: 11px;
    color: var(--text-tertiary);
    font-weight: 600;
  }
  
  /* Error Panel */
  .blueprint-error-panel {
    position: fixed;
    top: var(--spacing-xl);
    right: var(--spacing-xl);
    width: 400px;
    background: var(--paper-base);
    border: var(--border-weight-medium) solid var(--blueprint-accent);
    border-radius: 4px;
    box-shadow: var(--shadow-elevation);
    z-index: 1000;
  }
  
  .error-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--blueprint-accent);
    color: white;
  }
  
  .error-code {
    font-family: var(--font-technical);
    font-size: 10px;
    font-weight: 700;
  }
  
  .error-type {
    font-family: var(--font-technical);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
  }
  
  .close-error {
    margin-left: auto;
    background: none;
    border: none;
    color: white;
    font-size: 16px;
    cursor: pointer;
    padding: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .error-content {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
  }
  
  .error-icon {
    font-size: 1.25rem;
    color: var(--blueprint-accent);
  }
  
  .error-message {
    font-size: 12px;
    color: var(--text-primary);
    line-height: 1.4;
  }
  
  /* Loading Interface */
  .blueprint-loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(248, 246, 240, 0.95);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
  }
  
  .loading-interface {
    padding: var(--spacing-xl);
    max-width: 300px;
    text-align: center;
  }
  
  .loading-progress {
    margin-top: var(--spacing-md);
    height: 2px;
    background: var(--line-construction);
    border-radius: 1px;
    overflow: hidden;
  }
  
  .progress-bar {
    height: 100%;
    background: var(--blueprint-primary);
    width: 100%;
    animation: loading-progress 2s ease-in-out infinite;
  }
  
  @keyframes loading-progress {
    0%, 100% { transform: translateX(-100%); }
    50% { transform: translateX(100%); }
  }
  
  /* Responsive Design */
  @media (max-width: 1024px) {
    .specifications-grid {
      grid-template-columns: 1fr;
    }
    
    .header-content {
      flex-direction: column;
      gap: var(--spacing-lg);
      align-items: stretch;
    }
    
    .brand-section {
      justify-content: center;
    }
    
    .technical-nav {
      justify-content: center;
      flex-wrap: wrap;
    }
  }
  
  @media (max-width: 768px) {
    .metrics-grid,
    .operations-grid {
      grid-template-columns: 1fr;
    }
    
    .blueprint-workspace {
      padding: var(--spacing-md);
    }
    
    .header-content {
      padding: var(--spacing-md);
    }
    
    .blueprint-error-panel {
      top: var(--spacing-md);
      right: var(--spacing-md);
      left: var(--spacing-md);
      width: auto;
    }
    
    .drawing-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }
    
    .drawing-meta {
      margin-left: 0;
      text-align: center;
    }
  }
  
  @media (max-width: 640px) {
    .brand-header {
      flex-direction: column;
      text-align: center;
      gap: var(--spacing-sm);
    }
    
    .technical-nav {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0;
    }
    
    .blueprint-nav-item {
      text-align: center;
      border-right: none;
      border-bottom: var(--border-weight-thin) solid var(--line-construction);
    }
    
    .blueprint-nav-item:nth-child(even) {
      border-right: var(--border-weight-thin) solid var(--line-construction);
    }
  }
</style>