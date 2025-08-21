<!--
  Prompt Template Builder Component
  Advanced template creation with variable management and preview
-->
<script>
  // Import blueprint theme
  import '../styles/blueprint-theme.css';
  import '../styles/blueprint-components.css';
  
  import { writable, derived } from 'svelte/store';
  import { onMount } from 'svelte';
  
  export let initialTemplate = '';
  export let onSave = null;
  export let showCategorySelection = true;
  export let allowExport = true;
  
  // Stores
  const template = writable(initialTemplate);
  const variables = writable({});
  const categories = writable([]);
  const selectedCategories = writable([]);
  const previewMode = writable(false);
  const loading = writable(false);
  const error = writable(null);
  const success = writable(null);
  
  // Template metadata
  let templateMeta = {
    title: '',
    description: '',
    version: '1.0',
    author: 'current_user' // TODO: Get from user context
  };
  
  // Variable types for better UX
  const variableTypes = {
    'text': 'Text',
    'number': 'Number', 
    'email': 'Email',
    'url': 'URL',
    'date': 'Date',
    'select': 'Select Options',
    'multiline': 'Multiline Text'
  };
  
  // Derived stores
  const extractedVariables = derived(template, ($template) => {
    const pattern = /\{([^}]+)\}/g;
    const found = new Set();
    let match;
    
    while ((match = pattern.exec($template)) !== null) {
      found.add(match[1]);
    }
    
    return Array.from(found);
  });
  
  const processedTemplate = derived(
    [template, variables], 
    ([$template, $variables]) => {
      let processed = $template;
      
      Object.entries($variables).forEach(([key, config]) => {
        const placeholder = `{${key}}`;
        const value = config.value || `[${key}]`;
        processed = processed.replace(new RegExp(placeholder, 'g'), value);
      });
      
      return processed;
    }
  );
  
  // API base
  const API_BASE = '/api/v1/prompts';
  
  onMount(() => {
    loadCategories();
    
    // Update variables when extracted variables change
    extractedVariables.subscribe(vars => {
      const current = { ...$variables };
      
      // Add new variables
      vars.forEach(varName => {
        if (!current[varName]) {
          current[varName] = {
            type: 'text',
            description: '',
            defaultValue: '',
            value: '',
            required: true,
            options: [] // for select type
          };
        }
      });
      
      // Remove variables no longer in template
      Object.keys(current).forEach(varName => {
        if (!vars.includes(varName)) {
          delete current[varName];
        }
      });
      
      variables.set(current);
    });
  });
  
  // API Functions
  async function loadCategories() {
    try {
      const response = await fetch(`${API_BASE}/categories`);
      const result = await response.json();
      
      if (result.success) {
        categories.set(result.categories);
      }
    } catch (err) {
      console.warn('Failed to load categories:', err);
    }
  }
  
  async function createCategory(name, description = '') {
    $loading = true;
    $error = null;
    
    try {
      const response = await fetch(`${API_BASE}/categories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name,
          description,
          color: getRandomColor(),
          created_by: templateMeta.author
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        await loadCategories();
        return result.category_id;
      } else {
        throw new Error(result.error);
      }
    } catch (err) {
      $error = 'Failed to create category: ' + err.message;
      throw err;
    } finally {
      $loading = false;
    }
  }
  
  async function saveTemplate() {
    if (!templateMeta.title.trim() || !$template.trim()) {
      $error = 'Title and content are required';
      return;
    }
    
    $loading = true;
    $error = null;
    $success = null;
    
    try {
      const templateData = {
        title: templateMeta.title,
        content: $template,
        variables: $variables,
        metadata: {
          description: templateMeta.description,
          version: templateMeta.version,
          author: templateMeta.author,
          categories: $selectedCategories,
          created_at: Date.now()
        }
      };
      
      if (onSave) {
        await onSave(templateData);
        $success = 'Template saved successfully!';
      } else {
        // Default save behavior - could save to local storage or API
        console.log('Template data:', templateData);
        $success = 'Template prepared for saving!';
      }
    } catch (err) {
      $error = 'Failed to save template: ' + err.message;
    } finally {
      $loading = false;
    }
  }
  
  async function exportTemplate() {
    const templateData = {
      title: templateMeta.title,
      content: $template,
      variables: $variables,
      metadata: {
        description: templateMeta.description,
        version: templateMeta.version,
        author: templateMeta.author,
        categories: $selectedCategories,
        exported_at: new Date().toISOString()
      }
    };
    
    const blob = new Blob([JSON.stringify(templateData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${templateMeta.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_template.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
  
  async function importTemplate(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
      const text = await file.text();
      const imported = JSON.parse(text);
      
      if (imported.title) templateMeta.title = imported.title;
      if (imported.content) template.set(imported.content);
      if (imported.variables) variables.set(imported.variables);
      if (imported.metadata) {
        if (imported.metadata.description) templateMeta.description = imported.metadata.description;
        if (imported.metadata.version) templateMeta.version = imported.metadata.version;
        if (imported.metadata.author) templateMeta.author = imported.metadata.author;
        if (imported.metadata.categories) selectedCategories.set(imported.metadata.categories);
      }
      
      $success = 'Template imported successfully!';
    } catch (err) {
      $error = 'Failed to import template: Invalid file format';
    }
    
    // Reset file input
    event.target.value = '';
  }
  
  // Helper functions
  function getRandomColor() {
    const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899'];
    return colors[Math.floor(Math.random() * colors.length)];
  }
  
  function addVariableOption(varName) {
    const current = { ...$variables };
    current[varName].options.push('');
    variables.set(current);
  }
  
  function removeVariableOption(varName, index) {
    const current = { ...$variables };
    current[varName].options.splice(index, 1);
    variables.set(current);
  }
  
  function insertVariable(varName) {
    const textarea = document.querySelector('.template-editor');
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const currentValue = $template;
      const newValue = currentValue.substring(0, start) + `{${varName}}` + currentValue.substring(end);
      template.set(newValue);
      
      // Set cursor position after inserted variable
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + varName.length + 2;
        textarea.focus();
      }, 0);
    }
  }
  
  function clearMessages() {
    error.set(null);
    success.set(null);
  }
</script>

<div class="template-builder">
  <!-- Header -->
  <div class="header">
    <div class="title-section">
      <h2>Prompt Template Builder</h2>
      <p class="subtitle">Create reusable prompt templates with dynamic variables</p>
    </div>
    
    <div class="header-actions">
      {#if allowExport}
        <input 
          type="file" 
          accept=".json" 
          on:change={importTemplate}
          style="display: none;"
          id="import-input"
        />
        <button 
          class="btn btn-secondary"
          on:click={() => document.getElementById('import-input').click()}
          disabled={$loading}
        >
          Import
        </button>
        <button 
          class="btn btn-secondary"
          on:click={exportTemplate}
          disabled={$loading || !$template.trim()}
        >
          Export
        </button>
      {/if}
      
      <button 
        class="btn btn-secondary"
        on:click={() => previewMode.set(!$previewMode)}
        disabled={$loading}
      >
        {$previewMode ? 'Edit' : 'Preview'}
      </button>
      
      <button 
        class="btn btn-primary"
        on:click={saveTemplate}
        disabled={$loading || !templateMeta.title.trim() || !$template.trim()}
      >
        {$loading ? 'Saving...' : 'Save Template'}
      </button>
    </div>
  </div>
  
  <!-- Messages -->
  {#if $error}
    <div class="message error">
      <span class="message-icon">⚠️</span>
      {$error}
      <button class="close-btn" on:click={clearMessages}>×</button>
    </div>
  {/if}
  
  {#if $success}
    <div class="message success">
      <span class="message-icon">✅</span>
      {$success}
      <button class="close-btn" on:click={clearMessages}>×</button>
    </div>
  {/if}
  
  <!-- Template Metadata -->
  <div class="metadata-section">
    <h3>Template Information</h3>
    <div class="metadata-grid">
      <div class="form-group">
        <label for="template-title">Title *</label>
        <input 
          id="template-title"
          type="text"
          bind:value={templateMeta.title}
          placeholder="Enter template title..."
          required
        />
      </div>
      
      <div class="form-group">
        <label for="template-version">Version</label>
        <input 
          id="template-version"
          type="text"
          bind:value={templateMeta.version}
          placeholder="1.0"
        />
      </div>
      
      <div class="form-group full-width">
        <label for="template-description">Description</label>
        <textarea 
          id="template-description"
          bind:value={templateMeta.description}
          placeholder="Describe what this template does..."
          rows="3"
        ></textarea>
      </div>
    </div>
  </div>
  
  <!-- Categories -->
  {#if showCategorySelection && $categories.length > 0}
    <div class="categories-section">
      <h3>Categories</h3>
      <div class="categories-grid">
        {#each $categories as category}
          <label class="category-checkbox">
            <input 
              type="checkbox"
              value={category.id}
              bind:group={$selectedCategories}
            />
            <span class="category-name" style="border-left: 3px solid {category.color}">
              {category.name}
            </span>
          </label>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- Main Content -->
  <div class="main-content">
    <!-- Template Editor -->
    <div class="editor-section">
      <div class="section-header">
        <h3>Template Content</h3>
        <div class="editor-tools">
          <span class="variable-hint">Use {variable_name} for dynamic content</span>
          {#if $extractedVariables.length > 0}
            <div class="quick-variables">
              <span class="quick-label">Quick Insert:</span>
              {#each $extractedVariables as varName}
                <button 
                  class="variable-btn"
                  on:click={() => insertVariable(varName)}
                  title="Insert {varName}"
                >
                  {varName}
                </button>
              {/each}
            </div>
          {/if}
        </div>
      </div>
      
      {#if $previewMode}
        <div class="template-preview">
          <h4>Preview</h4>
          <div class="preview-content">
            <pre>{$processedTemplate}</pre>
          </div>
        </div>
      {:else}
        <textarea 
          class="template-editor"
          bind:value={$template}
          placeholder="Enter your template content here...

Example:
Hello {name},

Welcome to {system}! You have {message_count} new messages.

Best regards,
{assistant_name}"
          rows="12"
        ></textarea>
      {/if}
    </div>
    
    <!-- Variables Configuration -->
    {#if $extractedVariables.length > 0}
      <div class="variables-section">
        <div class="section-header">
          <h3>Variables Configuration</h3>
          <span class="variable-count">{$extractedVariables.length} variables</span>
        </div>
        
        <div class="variables-list">
          {#each $extractedVariables as varName}
            <div class="variable-config">
              <div class="variable-header">
                <h4>{varName}</h4>
                <button 
                  class="insert-btn"
                  on:click={() => insertVariable(varName)}
                  title="Insert into template"
                >
                  Insert
                </button>
              </div>
              
              <div class="variable-form">
                <div class="form-row">
                  <div class="form-group">
                    <label>Type</label>
                    <select bind:value={$variables[varName].type}>
                      {#each Object.entries(variableTypes) as [value, label]}
                        <option {value}>{label}</option>
                      {/each}
                    </select>
                  </div>
                  
                  <div class="form-group">
                    <label>
                      <input 
                        type="checkbox" 
                        bind:checked={$variables[varName].required}
                      />
                      Required
                    </label>
                  </div>
                </div>
                
                <div class="form-group">
                  <label>Description</label>
                  <input 
                    type="text"
                    bind:value={$variables[varName].description}
                    placeholder="Describe this variable..."
                  />
                </div>
                
                <div class="form-group">
                  <label>Default Value</label>
                  {#if $variables[varName].type === 'multiline'}
                    <textarea 
                      bind:value={$variables[varName].defaultValue}
                      placeholder="Default value..."
                      rows="3"
                    ></textarea>
                  {:else if $variables[varName].type === 'select'}
                    <input 
                      type="text"
                      bind:value={$variables[varName].defaultValue}
                      placeholder="Default selection..."
                    />
                  {:else}
                    <input 
                      type="text"
                      bind:value={$variables[varName].defaultValue}
                      placeholder="Default value..."
                    />
                  {/if}
                </div>
                
                <!-- Select options -->
                {#if $variables[varName].type === 'select'}
                  <div class="form-group">
                    <label>Options</label>
                    <div class="options-list">
                      {#each $variables[varName].options as option, index}
                        <div class="option-row">
                          <input 
                            type="text"
                            bind:value={$variables[varName].options[index]}
                            placeholder="Option {index + 1}..."
                          />
                          <button 
                            class="remove-option-btn"
                            on:click={() => removeVariableOption(varName, index)}
                          >
                            ×
                          </button>
                        </div>
                      {/each}
                      <button 
                        class="add-option-btn"
                        on:click={() => addVariableOption(varName)}
                      >
                        Add Option
                      </button>
                    </div>
                  </div>
                {/if}
                
                <!-- Test Value -->
                <div class="form-group">
                  <label>Test Value (for preview)</label>
                  {#if $variables[varName].type === 'multiline'}
                    <textarea 
                      bind:value={$variables[varName].value}
                      placeholder="Enter test value..."
                      rows="2"
                    ></textarea>
                  {:else if $variables[varName].type === 'select'}
                    <select bind:value={$variables[varName].value}>
                      <option value="">Select...</option>
                      {#each $variables[varName].options as option}
                        <option value={option}>{option}</option>
                      {/each}
                    </select>
                  {:else}
                    <input 
                      type={$variables[varName].type === 'number' ? 'number' : 
                           $variables[varName].type === 'email' ? 'email' :
                           $variables[varName].type === 'url' ? 'url' :
                           $variables[varName].type === 'date' ? 'date' : 'text'}
                      bind:value={$variables[varName].value}
                      placeholder="Enter test value..."
                    />
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {:else if $template.trim()}
      <div class="no-variables">
        <div class="no-variables-content">
          <h3>No Variables Detected</h3>
          <p>Add variables to your template using curly braces: <code>{variable_name}</code></p>
          <p>Variables make your templates dynamic and reusable.</p>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .template-builder {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem;
    background: #fafafa;
    min-height: 100vh;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    background: white;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    margin-bottom: 2rem;
  }
  
  .title-section h2 {
    margin: 0 0 0.5rem 0;
    color: #1f2937;
    font-size: 2rem;
    font-weight: 700;
  }
  
  .subtitle {
    margin: 0;
    color: #6b7280;
    font-size: 1.1rem;
  }
  
  .header-actions {
    display: flex;
    gap: 0.75rem;
    flex-shrink: 0;
  }
  
  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
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
  
  .message {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    border-radius: 0.75rem;
    margin-bottom: 1.5rem;
    font-weight: 500;
  }
  
  .message.error {
    background: #fee2e2;
    border: 1px solid #fca5a5;
    color: #dc2626;
  }
  
  .message.success {
    background: #d1fae5;
    border: 1px solid #86efac;
    color: #16a34a;
  }
  
  .message-icon {
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
  
  .metadata-section {
    background: white;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    margin-bottom: 2rem;
  }
  
  .metadata-section h3 {
    margin: 0 0 1.5rem 0;
    color: #1f2937;
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  .metadata-grid {
    display: grid;
    grid-template-columns: 1fr 200px;
    gap: 1.5rem;
    align-items: start;
  }
  
  .metadata-grid .full-width {
    grid-column: 1 / -1;
  }
  
  .categories-section {
    background: white;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    margin-bottom: 2rem;
  }
  
  .categories-section h3 {
    margin: 0 0 1.5rem 0;
    color: #1f2937;
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  .categories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
  }
  
  .category-checkbox {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .category-checkbox:hover {
    background: #f9fafb;
    border-color: #d1d5db;
  }
  
  .category-name {
    flex: 1;
    padding-left: 0.75rem;
    font-weight: 500;
  }
  
  .main-content {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 2rem;
  }
  
  .editor-section {
    background: white;
    border-radius: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }
  
  .section-header {
    padding: 1.5rem 2rem;
    border-bottom: 1px solid #e5e7eb;
    background: #f8fafc;
  }
  
  .section-header h3 {
    margin: 0;
    color: #1f2937;
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  .editor-tools {
    margin-top: 1rem;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1rem;
  }
  
  .variable-hint {
    color: #6b7280;
    font-size: 0.875rem;
    font-style: italic;
  }
  
  .quick-variables {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .quick-label {
    color: #6b7280;
    font-size: 0.875rem;
    font-weight: 500;
  }
  
  .variable-btn {
    padding: 0.25rem 0.75rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 1rem;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .variable-btn:hover {
    background: #2563eb;
  }
  
  .template-editor {
    width: 100%;
    padding: 2rem;
    border: none;
    resize: vertical;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.875rem;
    line-height: 1.6;
    background: #fafafa;
    min-height: 400px;
  }
  
  .template-editor:focus {
    outline: none;
    background: white;
  }
  
  .template-preview {
    padding: 2rem;
  }
  
  .template-preview h4 {
    margin: 0 0 1rem 0;
    color: #1f2937;
  }
  
  .preview-content {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1.5rem;
    min-height: 300px;
  }
  
  .preview-content pre {
    margin: 0;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.875rem;
    line-height: 1.6;
    white-space: pre-wrap;
  }
  
  .variables-section {
    background: white;
    border-radius: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    max-height: calc(100vh - 2rem);
    overflow-y: auto;
  }
  
  .variable-count {
    color: #6b7280;
    font-size: 0.875rem;
    font-weight: 500;
  }
  
  .variables-list {
    max-height: calc(100vh - 200px);
    overflow-y: auto;
  }
  
  .variable-config {
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .variable-config:last-child {
    border-bottom: none;
  }
  
  .variable-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .variable-header h4 {
    margin: 0;
    color: #3b82f6;
    font-size: 1.1rem;
    font-weight: 600;
    font-family: monospace;
  }
  
  .insert-btn {
    padding: 0.25rem 0.75rem;
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .insert-btn:hover {
    background: #e5e7eb;
  }
  
  .variable-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 1rem;
    align-items: end;
  }
  
  .form-group label {
    font-weight: 500;
    color: #374151;
    font-size: 0.875rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .form-group input,
  .form-group textarea,
  .form-group select {
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 0.5rem;
    font-size: 0.875rem;
  }
  
  .form-group input:focus,
  .form-group textarea:focus,
  .form-group select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
  
  .options-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .option-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  
  .option-row input {
    flex: 1;
  }
  
  .remove-option-btn {
    width: 2rem;
    height: 2rem;
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .add-option-btn {
    padding: 0.5rem 1rem;
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    align-self: flex-start;
  }
  
  .add-option-btn:hover {
    background: #e5e7eb;
  }
  
  .no-variables {
    background: white;
    border-radius: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 300px;
  }
  
  .no-variables-content {
    text-align: center;
    color: #6b7280;
    max-width: 300px;
  }
  
  .no-variables-content h3 {
    color: #9ca3af;
    margin-bottom: 1rem;
  }
  
  .no-variables-content code {
    background: #f3f4f6;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-family: monospace;
    color: #3b82f6;
  }
  
  @media (max-width: 1024px) {
    .main-content {
      grid-template-columns: 1fr;
    }
    
    .metadata-grid {
      grid-template-columns: 1fr;
    }
    
    .header {
      flex-direction: column;
      gap: 1.5rem;
      align-items: stretch;
    }
    
    .header-actions {
      justify-content: flex-end;
      flex-wrap: wrap;
    }
  }
  
  @media (max-width: 640px) {
    .template-builder {
      padding: 0.5rem;
    }
    
    .header,
    .metadata-section,
    .categories-section,
    .editor-section,
    .variables-section {
      padding: 1rem;
    }
    
    .categories-grid {
      grid-template-columns: 1fr;
    }
    
    .form-row {
      grid-template-columns: 1fr;
    }
  }
</style>