<!--
  Prompt Management Dashboard
  Main dashboard that integrates versioning, template builder, and category management
-->
<script>
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import PromptVersioning from './PromptVersioning.svelte';
  import PromptTemplateBuilder from './PromptTemplateBuilder.svelte';
  import PromptCategoryManager from './PromptCategoryManager.svelte';
  
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
      // In a real implementation, you'd have specific endpoints for dashboard stats
      const data = {
        totalPrompts: 0, // Would come from prompt count API
        totalVersions: 0, // Would come from version count API
        totalCategories: categoriesResult.success ? categoriesResult.count : 0,
        recentPrompts: [], // Would come from recent prompts API
        recentVersions: [], // Would come from recent versions API
        popularCategories: categoriesResult.success ? categoriesResult.categories.slice(0, 5) : []
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
    // Here you would save the template to your backend
    // For now, we'll just log it and show a success message
    console.log('Saving template:', templateData);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // After saving, you might want to refresh dashboard data
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

<div class="prompt-management-dashboard">
  <!-- Navigation Header -->
  <header class="dashboard-header">
    <div class="header-content">
      <div class="brand">
        <h1>Prompt Management</h1>
        <p class="tagline">Create, version, and organize your AI prompts</p>
      </div>
      
      <nav class="main-nav">
        <button 
          class="nav-button"
          class:active={$activeView === 'dashboard'}
          on:click={showDashboard}
        >
          📊 Dashboard
        </button>
        
        <button 
          class="nav-button"
          class:active={$activeView === 'versioning'}
          on:click={() => showVersioning()}
        >
          🔄 Versioning
        </button>
        
        <button 
          class="nav-button"
          class:active={$activeView === 'template-builder'}
          on:click={showTemplateBuilder}
        >
          🛠️ Template Builder
        </button>
        
        <button 
          class="nav-button"
          class:active={$activeView === 'categories'}
          on:click={showCategoryManager}
        >
          🏷️ Categories
        </button>
      </nav>
    </div>
  </header>
  
  <!-- Main Content Area -->
  <main class="dashboard-content">
    {#if $activeView === 'dashboard'}
      <!-- Dashboard Overview -->
      <div class="dashboard-overview">
        <!-- Stats Cards -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">📝</div>
            <div class="stat-content">
              <div class="stat-number">{formatNumber($dashboardData.totalPrompts)}</div>
              <div class="stat-label">Total Prompts</div>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon">🔄</div>
            <div class="stat-content">
              <div class="stat-number">{formatNumber($dashboardData.totalVersions)}</div>
              <div class="stat-label">Total Versions</div>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon">🏷️</div>
            <div class="stat-content">
              <div class="stat-number">{formatNumber($dashboardData.totalCategories)}</div>
              <div class="stat-label">Categories</div>
            </div>
          </div>
          
          <div class="stat-card action-card" on:click={showTemplateBuilder}>
            <div class="stat-icon">➕</div>
            <div class="stat-content">
              <div class="stat-label">Create New</div>
              <div class="stat-sublabel">Template</div>
            </div>
          </div>
        </div>
        
        <!-- Quick Actions -->
        <div class="quick-actions">
          <h2>Quick Actions</h2>
          <div class="actions-grid">
            <button class="action-button" on:click={showTemplateBuilder}>
              <div class="action-icon">🛠️</div>
              <div class="action-content">
                <h3>Create Template</h3>
                <p>Build a new prompt template with variables</p>
              </div>
            </button>
            
            <button class="action-button" on:click={showCategoryManager}>
              <div class="action-icon">🏷️</div>
              <div class="action-content">
                <h3>Manage Categories</h3>
                <p>Organize prompts with custom categories</p>
              </div>
            </button>
            
            <button class="action-button" on:click={() => showVersioning()}>
              <div class="action-icon">🔄</div>
              <div class="action-content">
                <h3>Version Control</h3>
                <p>Manage prompt versions and A/B testing</p>
              </div>
            </button>
            
            <button class="action-button">
              <div class="action-icon">📊</div>
              <div class="action-content">
                <h3>Analytics</h3>
                <p>View prompt performance and usage stats</p>
              </div>
            </button>
          </div>
        </div>
        
        <!-- Recent Activity & Popular Categories -->
        <div class="dashboard-sections">
          <!-- Recent Activity -->
          <section class="dashboard-section">
            <h2>Recent Activity</h2>
            {#if $dashboardData.recentVersions.length > 0}
              <div class="activity-list">
                {#each $dashboardData.recentVersions as version}
                  <div class="activity-item">
                    <div class="activity-icon">📝</div>
                    <div class="activity-content">
                      <div class="activity-title">{version.title}</div>
                      <div class="activity-meta">
                        Version {version.version_number} • {formatTimestamp(version.created_at)}
                      </div>
                    </div>
                    <button 
                      class="activity-action"
                      on:click={() => showVersioning(version.prompt_id)}
                    >
                      View
                    </button>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="empty-section">
                <p>No recent activity to display.</p>
                <button class="btn btn-primary" on:click={showTemplateBuilder}>
                  Create Your First Template
                </button>
              </div>
            {/if}
          </section>
          
          <!-- Popular Categories -->
          <section class="dashboard-section">
            <h2>Categories</h2>
            {#if $dashboardData.popularCategories.length > 0}
              <div class="categories-list">
                {#each $dashboardData.popularCategories as category}
                  <div class="category-item" style="border-left: 3px solid {category.color}">
                    <div class="category-info">
                      <div class="category-name">{category.name}</div>
                      {#if category.description}
                        <div class="category-description">{category.description}</div>
                      {/if}
                    </div>
                    <div class="category-badge" style="background: {category.color}20; color: {category.color}">
                      {category.name.charAt(0).toUpperCase()}
                    </div>
                  </div>
                {/each}
              </div>
              <div class="section-footer">
                <button class="link-button" on:click={showCategoryManager}>
                  View All Categories →
                </button>
              </div>
            {:else}
              <div class="empty-section">
                <p>No categories created yet.</p>
                <button class="btn btn-secondary" on:click={showCategoryManager}>
                  Create Categories
                </button>
              </div>
            {/if}
          </section>
        </div>
      </div>
      
    {:else if $activeView === 'versioning'}
      <!-- Versioning View -->
      <div class="view-header">
        <button class="back-button" on:click={showDashboard}>
          ← Back to Dashboard
        </button>
        <h2>Prompt Versioning</h2>
      </div>
      <PromptVersioning promptId={$selectedPromptId} />
      
    {:else if $activeView === 'template-builder'}
      <!-- Template Builder View -->
      <div class="view-header">
        <button class="back-button" on:click={showDashboard}>
          ← Back to Dashboard
        </button>
        <h2>Template Builder</h2>
      </div>
      <PromptTemplateBuilder onSave={handleTemplateSave} />
      
    {:else if $activeView === 'categories'}
      <!-- Categories View -->
      <div class="view-header">
        <button class="back-button" on:click={showDashboard}>
          ← Back to Dashboard
        </button>
        <h2>Category Management</h2>
      </div>
      <PromptCategoryManager />
    {/if}
  </main>
  
  <!-- Error Display -->
  {#if $error}
    <div class="error-toast">
      <span class="error-icon">⚠️</span>
      {$error}
      <button class="close-btn" on:click={() => error.set(null)}>×</button>
    </div>
  {/if}
  
  <!-- Loading Overlay -->
  {#if $loading}
    <div class="loading-overlay">
      <div class="loading-content">
        <div class="spinner"></div>
        <span>Loading dashboard...</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .prompt-management-dashboard {
    min-height: 100vh;
    background: #fafafa;
    position: relative;
  }
  
  .dashboard-header {
    background: white;
    border-bottom: 1px solid #e5e7eb;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .header-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1.5rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .brand h1 {
    margin: 0 0 0.25rem 0;
    color: #1f2937;
    font-size: 2rem;
    font-weight: 700;
  }
  
  .tagline {
    margin: 0;
    color: #6b7280;
    font-size: 0.95rem;
  }
  
  .main-nav {
    display: flex;
    gap: 0.5rem;
  }
  
  .nav-button {
    padding: 0.75rem 1.25rem;
    border: 1px solid transparent;
    border-radius: 0.5rem;
    background: transparent;
    color: #6b7280;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .nav-button:hover {
    background: #f3f4f6;
    color: #374151;
  }
  
  .nav-button.active {
    background: #3b82f6;
    color: white;
    border-color: #3b82f6;
  }
  
  .dashboard-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .view-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .back-button {
    padding: 0.5rem 1rem;
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    color: #374151;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .back-button:hover {
    background: #e5e7eb;
  }
  
  .view-header h2 {
    margin: 0;
    color: #1f2937;
    font-size: 1.875rem;
    font-weight: 700;
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }
  
  .stat-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.2s;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .stat-card:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
  }
  
  .action-card {
    cursor: pointer;
    border-color: #3b82f6;
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    color: white;
  }
  
  .action-card .stat-icon {
    background: rgba(255, 255, 255, 0.2);
    color: white;
  }
  
  .stat-icon {
    width: 3rem;
    height: 3rem;
    background: #f3f4f6;
    border-radius: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    flex-shrink: 0;
  }
  
  .stat-content {
    flex: 1;
  }
  
  .stat-number {
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
    line-height: 1;
  }
  
  .action-card .stat-number {
    color: white;
  }
  
  .stat-label {
    font-size: 0.875rem;
    color: #6b7280;
    font-weight: 500;
    margin-top: 0.25rem;
  }
  
  .action-card .stat-label {
    color: rgba(255, 255, 255, 0.9);
    font-size: 1rem;
    font-weight: 600;
  }
  
  .stat-sublabel {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.8);
    margin-top: 0.125rem;
  }
  
  .quick-actions {
    margin-bottom: 3rem;
  }
  
  .quick-actions h2 {
    margin: 0 0 1.5rem 0;
    color: #1f2937;
    font-size: 1.5rem;
    font-weight: 600;
  }
  
  .actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
  }
  
  .action-button {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .action-button:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
    border-color: #d1d5db;
  }
  
  .action-icon {
    width: 3rem;
    height: 3rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    flex-shrink: 0;
  }
  
  .action-content h3 {
    margin: 0 0 0.5rem 0;
    color: #1f2937;
    font-size: 1.1rem;
    font-weight: 600;
  }
  
  .action-content p {
    margin: 0;
    color: #6b7280;
    font-size: 0.875rem;
    line-height: 1.4;
  }
  
  .dashboard-sections {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }
  
  .dashboard-section {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .dashboard-section h2 {
    margin: 0 0 1.5rem 0;
    color: #1f2937;
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  .activity-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .activity-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
  }
  
  .activity-icon {
    width: 2rem;
    height: 2rem;
    background: #3b82f6;
    color: white;
    border-radius: 0.375rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    flex-shrink: 0;
  }
  
  .activity-content {
    flex: 1;
    min-width: 0;
  }
  
  .activity-title {
    font-weight: 500;
    color: #1f2937;
    margin-bottom: 0.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .activity-meta {
    font-size: 0.75rem;
    color: #6b7280;
  }
  
  .activity-action {
    padding: 0.25rem 0.75rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
    flex-shrink: 0;
  }
  
  .activity-action:hover {
    background: #2563eb;
  }
  
  .categories-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .category-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
  }
  
  .category-info {
    flex: 1;
    min-width: 0;
  }
  
  .category-name {
    font-weight: 500;
    color: #1f2937;
    margin-bottom: 0.25rem;
  }
  
  .category-description {
    font-size: 0.75rem;
    color: #6b7280;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .category-badge {
    width: 2rem;
    height: 2rem;
    border-radius: 0.375rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    font-weight: 600;
    flex-shrink: 0;
  }
  
  .empty-section {
    text-align: center;
    padding: 2rem 1rem;
    color: #6b7280;
  }
  
  .empty-section p {
    margin: 0 0 1rem 0;
  }
  
  .btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-primary {
    background: #3b82f6;
    color: white;
  }
  
  .btn-primary:hover {
    background: #2563eb;
  }
  
  .btn-secondary {
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
  }
  
  .btn-secondary:hover {
    background: #e5e7eb;
  }
  
  .section-footer {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
  
  .link-button {
    background: none;
    border: none;
    color: #3b82f6;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: color 0.2s;
  }
  
  .link-button:hover {
    color: #2563eb;
  }
  
  .error-toast {
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: #fee2e2;
    border: 1px solid #fca5a5;
    color: #dc2626;
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    z-index: 1000;
    max-width: 400px;
  }
  
  .error-icon {
    font-size: 1.25rem;
  }
  
  .close-btn {
    margin-left: auto;
    background: none;
    border: none;
    color: inherit;
    font-size: 1.25rem;
    cursor: pointer;
    opacity: 0.7;
  }
  
  .close-btn:hover {
    opacity: 1;
  }
  
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
  }
  
  .loading-content {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 2rem 3rem;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    color: #6b7280;
  }
  
  .spinner {
    width: 2rem;
    height: 2rem;
    border: 3px solid #e5e7eb;
    border-top: 3px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  @media (max-width: 1024px) {
    .dashboard-sections {
      grid-template-columns: 1fr;
    }
    
    .header-content {
      flex-direction: column;
      gap: 1.5rem;
      align-items: stretch;
    }
    
    .main-nav {
      justify-content: center;
      flex-wrap: wrap;
    }
  }
  
  @media (max-width: 768px) {
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .actions-grid {
      grid-template-columns: 1fr;
    }
    
    .dashboard-content {
      padding: 1rem;
    }
    
    .header-content {
      padding: 1rem;
    }
    
    .action-button {
      flex-direction: column;
      text-align: center;
      gap: 1rem;
    }
    
    .error-toast {
      top: 1rem;
      right: 1rem;
      left: 1rem;
      max-width: none;
    }
  }
  
  @media (max-width: 640px) {
    .stats-grid {
      grid-template-columns: 1fr;
    }
    
    .main-nav {
      grid-template-columns: repeat(2, 1fr);
      display: grid;
      gap: 0.5rem;
    }
    
    .nav-button {
      padding: 1rem;
      text-align: center;
    }
  }
</style>