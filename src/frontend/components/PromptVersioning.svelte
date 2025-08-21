<!--
  Prompt Versioning Component
  Provides version management interface for prompts
  Updated with Blueprint Theme integration for tojo.world
-->
<script>
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  
  // Import blueprint theme
  import '../styles/blueprint-theme.css';
  import '../styles/blueprint-components.css';
  
  export let promptId = null;
  export let showVersionList = true;
  export let allowEditing = true;
  
  // Stores
  const versions = writable([]);
  const activeVersion = writable(null);
  const loading = writable(false);
  const error = writable(null);
  const showCreateModal = writable(false);
  const showTemplateModal = writable(false);
  
  // Form data
  let newVersionData = {
    title: '',
    content: '',
    variables: {},
    version_number: 1
  };
  
  let templateData = {
    content: '',
    variables: {}
  };
  
  let processedContent = '';
  
  // API base URL
  const API_BASE = '/api/v1/prompts';
  
  // Load versions on mount
  onMount(() => {
    if (promptId) {
      loadVersions();
      loadActiveVersion();
    }
  });
  
  // API Functions
  async function loadVersions() {
    $loading = true;
    $error = null;
    
    try {
      const response = await fetch(`${API_BASE}/${promptId}/versions`);
      const result = await response.json();
      
      if (result.success) {
        versions.set(result.versions);
      } else {
        $error = result.error;
      }
    } catch (err) {
      $error = 'Failed to load versions: ' + err.message;
    } finally {
      $loading = false;
    }
  }
  
  async function loadActiveVersion() {
    try {
      const response = await fetch(`${API_BASE}/${promptId}/versions/active`);
      const result = await response.json();
      
      if (result.success) {
        activeVersion.set(result.version);
      }
    } catch (err) {
      console.warn('No active version found:', err);
    }
  }
  
  async function createVersion() {
    $loading = true;
    $error = null;
    
    try {
      const versionData = {
        ...newVersionData,
        prompt_id: promptId,
        created_by: 'current_user' // TODO: Get from user context
      };
      
      const response = await fetch(`${API_BASE}/versions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(versionData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        await loadVersions();
        await loadActiveVersion();
        resetCreateForm();
        $showCreateModal = false;
      } else {
        $error = result.error;
      }
    } catch (err) {
      $error = 'Failed to create version: ' + err.message;
    } finally {
      $loading = false;
    }
  }
  
  async function activateVersion(versionId) {
    $loading = true;
    $error = null;
    
    try {
      const response = await fetch(`${API_BASE}/${promptId}/versions/${versionId}/activate`, {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (result.success) {
        await loadActiveVersion();
        await loadVersions();
      } else {
        $error = result.error;
      }
    } catch (err) {
      $error = 'Failed to activate version: ' + err.message;
    } finally {
      $loading = false;
    }
  }
  
  async function processTemplate() {
    $loading = true;
    $error = null;
    
    try {
      const response = await fetch(`${API_BASE}/template/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(templateData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        processedContent = result.processed_content;
      } else {
        $error = result.error;
        if (result.validation) {
          $error += `. Missing variables: ${result.validation.missing_variables.join(', ')}`;
        }
      }
    } catch (err) {
      $error = 'Failed to process template: ' + err.message;
    } finally {
      $loading = false;
    }
  }
  
  async function extractVariables() {
    if (!templateData.content) return;
    
    try {
      const response = await fetch(`${API_BASE}/template/variables`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: templateData.content })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Initialize variables object with empty values
        const variables = {};
        result.variables.forEach(varName => {
          variables[varName] = '';
        });
        templateData.variables = variables;
        templateData = { ...templateData }; // Trigger reactivity
      }
    } catch (err) {
      console.warn('Failed to extract variables:', err);
    }
  }
  
  // Helper functions
  function resetCreateForm() {
    newVersionData = {
      title: '',
      content: '',
      variables: {},
      version_number: ($versions.length || 0) + 1
    };
  }
  
  function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
  }
  
  function formatVariables(variables) {
    if (!variables || Object.keys(variables).length === 0) return 'None';
    return Object.keys(variables).map(key => `{${key}}`).join(', ');
  }
  
  // Event handlers
  function handleCreateClick() {
    resetCreateForm();
    $showCreateModal = true;
  }
  
  function handleTemplateClick() {
    templateData = { content: '', variables: {} };
    processedContent = '';
    $showTemplateModal = true;
  }
  
  function handleContentChange() {
    extractVariables();
  }
</script>

<div class="prompt-versioning">
  <!-- Header -->
  <div class="header">
    <h3>Prompt Versioning</h3>
    {#if allowEditing}
      <div class="actions">
        <button 
          class="btn btn-secondary" 
          on:click={handleTemplateClick}
          disabled={$loading}
        >
          Template Tester
        </button>
        <button 
          class="btn btn-primary" 
          on:click={handleCreateClick}
          disabled={$loading || !promptId}
        >
          Create Version
        </button>
      </div>
    {/if}
  </div>
  
  <!-- Error Display -->
  {#if $error}
    <div class="error-banner">
      <span class="error-icon">⚠️</span>
      {$error}
      <button class="close-btn" on:click={() => error.set(null)}>×</button>
    </div>
  {/if}
  
  <!-- Loading State -->
  {#if $loading}
    <div class="loading">
      <div class="spinner"></div>
      <span>Loading versions...</span>
    </div>
  {/if}
  
  <!-- Active Version Display -->
  {#if $activeVersion}
    <div class="active-version">
      <div class="version-header">
        <h4>Active Version</h4>
        <span class="version-badge active">v{$activeVersion.version_number}</span>
      </div>
      <div class="version-content">
        <h5>{$activeVersion.title}</h5>
        <pre class="content-preview">{$activeVersion.content}</pre>
        <div class="version-meta">
          <span>Variables: {formatVariables($activeVersion.variables)}</span>
          <span>Created: {formatTimestamp($activeVersion.created_at)}</span>
          <span>By: {$activeVersion.created_by}</span>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Version List -->
  {#if showVersionList && $versions.length > 0}
    <div class="version-list">
      <h4>All Versions ({$versions.length})</h4>
      <div class="versions-grid">
        {#each $versions as version}
          <div class="version-card" class:active={$activeVersion?.id === version.id}>
            <div class="version-card-header">
              <span class="version-number">v{version.version_number}</span>
              <span class="version-title">{version.title}</span>
              {#if $activeVersion?.id === version.id}
                <span class="active-badge">Active</span>
              {:else if allowEditing}
                <button 
                  class="activate-btn"
                  on:click={() => activateVersion(version.id)}
                  disabled={$loading}
                >
                  Activate
                </button>
              {/if}
            </div>
            <div class="version-card-content">
              <pre class="content-snippet">{version.content.slice(0, 200)}{version.content.length > 200 ? '...' : ''}</pre>
            </div>
            <div class="version-card-meta">
              <span class="variables">{formatVariables(version.variables)}</span>
              <span class="created-info">
                {formatTimestamp(version.created_at)} by {version.created_by}
              </span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- Create Version Modal -->
  {#if $showCreateModal}
    <div class="modal-overlay" on:click={() => showCreateModal.set(false)}>
      <div class="modal" on:click|stopPropagation>
        <div class="modal-header">
          <h4>Create New Version</h4>
          <button class="close-btn" on:click={() => showCreateModal.set(false)}>×</button>
        </div>
        <div class="modal-content">
          <form on:submit|preventDefault={createVersion}>
            <div class="form-group">
              <label for="version-title">Title</label>
              <input 
                id="version-title"
                type="text" 
                bind:value={newVersionData.title}
                placeholder="Enter version title..."
                required
              />
            </div>
            
            <div class="form-group">
              <label for="version-content">Content</label>
              <textarea 
                id="version-content"
                bind:value={newVersionData.content}
                on:input={handleContentChange}
                placeholder="Enter prompt content... Use {variable_name} for variables"
                rows="8"
                required
              ></textarea>
            </div>
            
            <div class="form-group">
              <label for="version-number">Version Number</label>
              <input 
                id="version-number"
                type="number" 
                bind:value={newVersionData.version_number}
                min="1"
                required
              />
            </div>
            
            <!-- Variables Preview -->
            {#if Object.keys(newVersionData.variables).length > 0}
              <div class="variables-preview">
                <h5>Detected Variables:</h5>
                <div class="variables-list">
                  {#each Object.keys(newVersionData.variables) as varName}
                    <span class="variable-tag">{varName}</span>
                  {/each}
                </div>
              </div>
            {/if}
            
            <div class="modal-actions">
              <button type="button" class="btn btn-secondary" on:click={() => showCreateModal.set(false)}>
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" disabled={$loading}>
                {$loading ? 'Creating...' : 'Create Version'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Template Tester Modal -->
  {#if $showTemplateModal}
    <div class="modal-overlay" on:click={() => showTemplateModal.set(false)}>
      <div class="modal modal-large" on:click|stopPropagation>
        <div class="modal-header">
          <h4>Template Tester</h4>
          <button class="close-btn" on:click={() => showTemplateModal.set(false)}>×</button>
        </div>
        <div class="modal-content">
          <div class="template-tester">
            <div class="template-input">
              <div class="form-group">
                <label for="template-content">Template Content</label>
                <textarea 
                  id="template-content"
                  bind:value={templateData.content}
                  on:input={handleContentChange}
                  placeholder="Enter template content with {variable} placeholders..."
                  rows="6"
                ></textarea>
              </div>
              
              <!-- Variables Input -->
              {#if Object.keys(templateData.variables).length > 0}
                <div class="variables-section">
                  <h5>Variables</h5>
                  {#each Object.entries(templateData.variables) as [varName, varValue]}
                    <div class="form-group">
                      <label for="var-{varName}">{varName}</label>
                      <input 
                        id="var-{varName}"
                        type="text"
                        bind:value={templateData.variables[varName]}
                        placeholder="Enter value for {varName}..."
                      />
                    </div>
                  {/each}
                </div>
              {/if}
              
              <button 
                class="btn btn-primary"
                on:click={processTemplate}
                disabled={$loading || !templateData.content}
              >
                {$loading ? 'Processing...' : 'Process Template'}
              </button>
            </div>
            
            <div class="template-output">
              <h5>Processed Output</h5>
              {#if processedContent}
                <div class="output-content">
                  <pre>{processedContent}</pre>
                </div>
              {:else}
                <div class="output-placeholder">
                  Processed content will appear here...
                </div>
              {/if}
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .prompt-versioning {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .header h3 {
    margin: 0;
    color: #1f2937;
  }
  
  .actions {
    display: flex;
    gap: 0.75rem;
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
  
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .btn-primary {
    background: #3b82f6;
    color: white;
  }
  
  .btn-primary:hover:not(:disabled) {
    background: #2563eb;
  }
  
  .btn-secondary {
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
  }
  
  .btn-secondary:hover:not(:disabled) {
    background: #e5e7eb;
  }
  
  .error-banner {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: #fee2e2;
    border: 1px solid #fecaca;
    border-radius: 0.5rem;
    color: #dc2626;
    margin-bottom: 1rem;
  }
  
  .error-icon {
    font-size: 1.25rem;
  }
  
  .close-btn {
    margin-left: auto;
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
    color: inherit;
    opacity: 0.7;
  }
  
  .close-btn:hover {
    opacity: 1;
  }
  
  .loading {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 2rem;
    justify-content: center;
    color: #6b7280;
  }
  
  .spinner {
    width: 1.5rem;
    height: 1.5rem;
    border: 2px solid #e5e7eb;
    border-top: 2px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .active-version {
    background: #f8fafc;
    border: 2px solid #3b82f6;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }
  
  .version-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  .version-header h4 {
    margin: 0;
    color: #1f2937;
  }
  
  .version-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .version-badge.active {
    background: #3b82f6;
    color: white;
  }
  
  .version-content h5 {
    margin: 0 0 0.75rem 0;
    color: #374151;
  }
  
  .content-preview {
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.875rem;
    white-space: pre-wrap;
    overflow-x: auto;
  }
  
  .version-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.875rem;
    color: #6b7280;
  }
  
  .version-list h4 {
    margin-bottom: 1rem;
    color: #1f2937;
  }
  
  .versions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1rem;
  }
  
  .version-card {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1rem;
    background: white;
    transition: all 0.2s;
  }
  
  .version-card:hover {
    shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    border-color: #d1d5db;
  }
  
  .version-card.active {
    border-color: #3b82f6;
    background: #f8fafc;
  }
  
  .version-card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }
  
  .version-number {
    font-weight: 600;
    color: #3b82f6;
  }
  
  .version-title {
    flex: 1;
    font-weight: 500;
    color: #1f2937;
  }
  
  .active-badge {
    padding: 0.125rem 0.5rem;
    background: #10b981;
    color: white;
    border-radius: 0.75rem;
    font-size: 0.75rem;
    font-weight: 500;
  }
  
  .activate-btn {
    padding: 0.25rem 0.75rem;
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    cursor: pointer;
  }
  
  .activate-btn:hover:not(:disabled) {
    background: #e5e7eb;
  }
  
  .content-snippet {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 0.375rem;
    padding: 0.75rem;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.75rem;
    margin-bottom: 0.75rem;
    white-space: pre-wrap;
    overflow: hidden;
  }
  
  .version-card-meta {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.75rem;
    color: #6b7280;
  }
  
  .variables {
    font-weight: 500;
  }
  
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .modal {
    background: white;
    border-radius: 0.75rem;
    width: 90%;
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
  }
  
  .modal-large {
    max-width: 900px;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .modal-header h4 {
    margin: 0;
    color: #1f2937;
  }
  
  .modal-content {
    padding: 1.5rem;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #374151;
  }
  
  .form-group input,
  .form-group textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 0.5rem;
    font-size: 0.875rem;
  }
  
  .form-group input:focus,
  .form-group textarea:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
  
  .variables-preview {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
  }
  
  .variables-preview h5 {
    margin: 0 0 0.75rem 0;
    color: #475569;
  }
  
  .variables-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .variable-tag {
    padding: 0.25rem 0.75rem;
    background: #3b82f6;
    color: white;
    border-radius: 1rem;
    font-size: 0.75rem;
    font-weight: 500;
  }
  
  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 1.5rem;
  }
  
  .template-tester {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }
  
  .template-input,
  .template-output {
    min-height: 400px;
  }
  
  .variables-section {
    margin-bottom: 1rem;
  }
  
  .variables-section h5 {
    margin-bottom: 0.75rem;
    color: #374151;
  }
  
  .template-output h5 {
    margin-bottom: 1rem;
    color: #374151;
  }
  
  .output-content {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1rem;
    min-height: 200px;
  }
  
  .output-content pre {
    margin: 0;
    white-space: pre-wrap;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.875rem;
  }
  
  .output-placeholder {
    padding: 2rem;
    text-align: center;
    color: #9ca3af;
    font-style: italic;
  }
  
  @media (max-width: 768px) {
    .template-tester {
      grid-template-columns: 1fr;
    }
    
    .versions-grid {
      grid-template-columns: 1fr;
    }
    
    .actions {
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .version-meta {
      flex-direction: column;
      gap: 0.5rem;
    }
  }
</style>