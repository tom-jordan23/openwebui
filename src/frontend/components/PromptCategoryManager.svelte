<!--
  Prompt Category Manager Component
  Manages prompt categories with CRUD operations
-->
<script>
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  
  export let allowEditing = true;
  export let onCategorySelect = null;
  export let selectedCategories = [];
  
  // Stores
  const categories = writable([]);
  const loading = writable(false);
  const error = writable(null);
  const success = writable(null);
  const showCreateModal = writable(false);
  const showEditModal = writable(false);
  const editingCategory = writable(null);
  
  // Form data
  let categoryForm = {
    name: '',
    description: '',
    color: '#3b82f6'
  };
  
  // Predefined colors
  const colorOptions = [
    { value: '#ef4444', name: 'Red' },
    { value: '#f97316', name: 'Orange' },
    { value: '#eab308', name: 'Yellow' },
    { value: '#22c55e', name: 'Green' },
    { value: '#06b6d4', name: 'Cyan' },
    { value: '#3b82f6', name: 'Blue' },
    { value: '#8b5cf6', name: 'Purple' },
    { value: '#ec4899', name: 'Pink' },
    { value: '#6b7280', name: 'Gray' },
    { value: '#1f2937', name: 'Dark' }
  ];
  
  // API base
  const API_BASE = '/api/v1/prompts';
  
  onMount(() => {
    loadCategories();
  });
  
  // API Functions
  async function loadCategories() {
    $loading = true;
    $error = null;
    
    try {
      const response = await fetch(`${API_BASE}/categories`);
      const result = await response.json();
      
      if (result.success) {
        categories.set(result.categories);
      } else {
        $error = result.error;
      }
    } catch (err) {
      $error = 'Failed to load categories: ' + err.message;
    } finally {
      $loading = false;
    }
  }
  
  async function createCategory() {
    if (!categoryForm.name.trim()) {
      $error = 'Category name is required';
      return;
    }
    
    $loading = true;
    $error = null;
    $success = null;
    
    try {
      const response = await fetch(`${API_BASE}/categories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: categoryForm.name.trim(),
          description: categoryForm.description.trim(),
          color: categoryForm.color,
          created_by: 'current_user' // TODO: Get from user context
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        await loadCategories();
        resetForm();
        $showCreateModal = false;
        $success = 'Category created successfully!';
      } else {
        $error = result.error;
      }
    } catch (err) {
      $error = 'Failed to create category: ' + err.message;
    } finally {
      $loading = false;
    }
  }
  
  async function updateCategory() {
    if (!categoryForm.name.trim()) {
      $error = 'Category name is required';
      return;
    }
    
    $loading = true;
    $error = null;
    $success = null;
    
    try {
      // Note: This endpoint would need to be implemented in the API
      const response = await fetch(`${API_BASE}/categories/${$editingCategory.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: categoryForm.name.trim(),
          description: categoryForm.description.trim(),
          color: categoryForm.color
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        await loadCategories();
        resetForm();
        $showEditModal = false;
        $editingCategory = null;
        $success = 'Category updated successfully!';
      } else {
        $error = result.error;
      }
    } catch (err) {
      $error = 'Failed to update category: ' + err.message;
    } finally {
      $loading = false;
    }
  }
  
  async function deleteCategory(category) {
    if (!confirm(`Are you sure you want to delete the category "${category.name}"? This action cannot be undone.`)) {
      return;
    }
    
    $loading = true;
    $error = null;
    $success = null;
    
    try {
      // Note: This endpoint would need to be implemented in the API
      const response = await fetch(`${API_BASE}/categories/${category.id}`, {
        method: 'DELETE'
      });
      
      const result = await response.json();
      
      if (result.success) {
        await loadCategories();
        $success = 'Category deleted successfully!';
      } else {
        $error = result.error;
      }
    } catch (err) {
      $error = 'Failed to delete category: ' + err.message;
    } finally {
      $loading = false;
    }
  }
  
  // Helper functions
  function resetForm() {
    categoryForm = {
      name: '',
      description: '',
      color: '#3b82f6'
    };
  }
  
  function handleCreateClick() {
    resetForm();
    $showCreateModal = true;
  }
  
  function handleEditClick(category) {
    categoryForm = {
      name: category.name,
      description: category.description || '',
      color: category.color || '#3b82f6'
    };
    editingCategory.set(category);
    $showEditModal = true;
  }
  
  function handleCategoryToggle(category) {
    if (onCategorySelect) {
      onCategorySelect(category);
    }
  }
  
  function isCategorySelected(categoryId) {
    return selectedCategories.includes(categoryId);
  }
  
  function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleDateString();
  }
  
  function clearMessages() {
    error.set(null);
    success.set(null);
  }
  
  function getContrastColor(hexColor) {
    // Convert hex to RGB
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    
    // Calculate relative luminance
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    return luminance > 0.5 ? '#000000' : '#ffffff';
  }
</script>

<div class="category-manager">
  <!-- Header -->
  <div class="header">
    <div class="title-section">
      <h2>Category Manager</h2>
      <p class="subtitle">Organize your prompts with categories</p>
    </div>
    
    {#if allowEditing}
      <button 
        class="btn btn-primary"
        on:click={handleCreateClick}
        disabled={$loading}
      >
        Create Category
      </button>
    {/if}
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
  
  <!-- Loading State -->
  {#if $loading && $categories.length === 0}
    <div class="loading">
      <div class="spinner"></div>
      <span>Loading categories...</span>
    </div>
  {/if}
  
  <!-- Categories Grid -->
  {#if $categories.length > 0}
    <div class="categories-grid">
      {#each $categories as category}
        <div 
          class="category-card" 
          class:selected={isCategorySelected(category.id)}
          style="border-left: 4px solid {category.color}"
        >
          <div class="category-header">
            <div class="category-info">
              <div 
                class="category-color-badge"
                style="background-color: {category.color}; color: {getContrastColor(category.color)}"
              >
                {category.name.charAt(0).toUpperCase()}
              </div>
              <div class="category-details">
                <h3 class="category-name">{category.name}</h3>
                {#if category.description}
                  <p class="category-description">{category.description}</p>
                {/if}
              </div>
            </div>
            
            {#if allowEditing}
              <div class="category-actions">
                <button 
                  class="action-btn edit-btn"
                  on:click={() => handleEditClick(category)}
                  title="Edit category"
                  disabled={$loading}
                >
                  ✏️
                </button>
                <button 
                  class="action-btn delete-btn"
                  on:click={() => deleteCategory(category)}
                  title="Delete category"
                  disabled={$loading}
                >
                  🗑️
                </button>
              </div>
            {/if}
          </div>
          
          <div class="category-meta">
            <span class="meta-item">
              Created: {formatTimestamp(category.created_at)}
            </span>
            <span class="meta-item">
              By: {category.created_by}
            </span>
          </div>
          
          {#if onCategorySelect}
            <button 
              class="select-btn"
              class:selected={isCategorySelected(category.id)}
              on:click={() => handleCategoryToggle(category)}
            >
              {isCategorySelected(category.id) ? 'Deselect' : 'Select'}
            </button>
          {/if}
        </div>
      {/each}
    </div>
  {:else if !$loading}
    <div class="empty-state">
      <div class="empty-content">
        <h3>No Categories Yet</h3>
        <p>Create your first category to start organizing prompts.</p>
        {#if allowEditing}
          <button 
            class="btn btn-primary"
            on:click={handleCreateClick}
          >
            Create First Category
          </button>
        {/if}
      </div>
    </div>
  {/if}
  
  <!-- Create Category Modal -->
  {#if $showCreateModal}
    <div class="modal-overlay" on:click={() => showCreateModal.set(false)}>
      <div class="modal" on:click|stopPropagation>
        <div class="modal-header">
          <h3>Create New Category</h3>
          <button class="close-btn" on:click={() => showCreateModal.set(false)}>×</button>
        </div>
        
        <div class="modal-content">
          <form on:submit|preventDefault={createCategory}>
            <div class="form-group">
              <label for="category-name">Name *</label>
              <input 
                id="category-name"
                type="text"
                bind:value={categoryForm.name}
                placeholder="Enter category name..."
                required
                maxlength="100"
              />
            </div>
            
            <div class="form-group">
              <label for="category-description">Description</label>
              <textarea 
                id="category-description"
                bind:value={categoryForm.description}
                placeholder="Describe this category..."
                rows="3"
                maxlength="500"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label for="category-color">Color</label>
              <div class="color-selection">
                <div class="color-options">
                  {#each colorOptions as colorOption}
                    <button
                      type="button"
                      class="color-option"
                      class:selected={categoryForm.color === colorOption.value}
                      style="background-color: {colorOption.value}"
                      title={colorOption.name}
                      on:click={() => categoryForm.color = colorOption.value}
                    >
                      {#if categoryForm.color === colorOption.value}
                        <span class="check-mark" style="color: {getContrastColor(colorOption.value)}">✓</span>
                      {/if}
                    </button>
                  {/each}
                </div>
                <input 
                  id="category-color"
                  type="color"
                  bind:value={categoryForm.color}
                  class="color-picker"
                />
              </div>
            </div>
            
            <!-- Preview -->
            <div class="form-group">
              <label>Preview</label>
              <div class="category-preview">
                <div 
                  class="preview-badge"
                  style="background-color: {categoryForm.color}; color: {getContrastColor(categoryForm.color)}"
                >
                  {categoryForm.name ? categoryForm.name.charAt(0).toUpperCase() : '?'}
                </div>
                <div class="preview-info">
                  <div class="preview-name">
                    {categoryForm.name || 'Category Name'}
                  </div>
                  {#if categoryForm.description}
                    <div class="preview-description">
                      {categoryForm.description}
                    </div>
                  {/if}
                </div>
              </div>
            </div>
            
            <div class="modal-actions">
              <button 
                type="button" 
                class="btn btn-secondary"
                on:click={() => showCreateModal.set(false)}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                class="btn btn-primary"
                disabled={$loading || !categoryForm.name.trim()}
              >
                {$loading ? 'Creating...' : 'Create Category'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Edit Category Modal -->
  {#if $showEditModal}
    <div class="modal-overlay" on:click={() => showEditModal.set(false)}>
      <div class="modal" on:click|stopPropagation>
        <div class="modal-header">
          <h3>Edit Category</h3>
          <button class="close-btn" on:click={() => showEditModal.set(false)}>×</button>
        </div>
        
        <div class="modal-content">
          <form on:submit|preventDefault={updateCategory}>
            <div class="form-group">
              <label for="edit-category-name">Name *</label>
              <input 
                id="edit-category-name"
                type="text"
                bind:value={categoryForm.name}
                placeholder="Enter category name..."
                required
                maxlength="100"
              />
            </div>
            
            <div class="form-group">
              <label for="edit-category-description">Description</label>
              <textarea 
                id="edit-category-description"
                bind:value={categoryForm.description}
                placeholder="Describe this category..."
                rows="3"
                maxlength="500"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label for="edit-category-color">Color</label>
              <div class="color-selection">
                <div class="color-options">
                  {#each colorOptions as colorOption}
                    <button
                      type="button"
                      class="color-option"
                      class:selected={categoryForm.color === colorOption.value}
                      style="background-color: {colorOption.value}"
                      title={colorOption.name}
                      on:click={() => categoryForm.color = colorOption.value}
                    >
                      {#if categoryForm.color === colorOption.value}
                        <span class="check-mark" style="color: {getContrastColor(colorOption.value)}">✓</span>
                      {/if}
                    </button>
                  {/each}
                </div>
                <input 
                  id="edit-category-color"
                  type="color"
                  bind:value={categoryForm.color}
                  class="color-picker"
                />
              </div>
            </div>
            
            <!-- Preview -->
            <div class="form-group">
              <label>Preview</label>
              <div class="category-preview">
                <div 
                  class="preview-badge"
                  style="background-color: {categoryForm.color}; color: {getContrastColor(categoryForm.color)}"
                >
                  {categoryForm.name ? categoryForm.name.charAt(0).toUpperCase() : '?'}
                </div>
                <div class="preview-info">
                  <div class="preview-name">
                    {categoryForm.name || 'Category Name'}
                  </div>
                  {#if categoryForm.description}
                    <div class="preview-description">
                      {categoryForm.description}
                    </div>
                  {/if}
                </div>
              </div>
            </div>
            
            <div class="modal-actions">
              <button 
                type="button" 
                class="btn btn-secondary"
                on:click={() => showEditModal.set(false)}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                class="btn btn-primary"
                disabled={$loading || !categoryForm.name.trim()}
              >
                {$loading ? 'Updating...' : 'Update Category'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .category-manager {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .title-section h2 {
    margin: 0 0 0.5rem 0;
    color: #1f2937;
    font-size: 1.875rem;
    font-weight: 700;
  }
  
  .subtitle {
    margin: 0;
    color: #6b7280;
    font-size: 1rem;
  }
  
  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    font-weight: 600;
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
  
  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 4rem 2rem;
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
  
  .categories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }
  
  .category-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    transition: all 0.2s;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .category-card:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
  }
  
  .category-card.selected {
    border-color: #3b82f6;
    background: #f8fafc;
    box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.1);
  }
  
  .category-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }
  
  .category-info {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    flex: 1;
  }
  
  .category-color-badge {
    width: 3rem;
    height: 3rem;
    border-radius: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    font-weight: 700;
    flex-shrink: 0;
  }
  
  .category-details {
    flex: 1;
    min-width: 0;
  }
  
  .category-name {
    margin: 0 0 0.5rem 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    word-break: break-word;
  }
  
  .category-description {
    margin: 0;
    color: #6b7280;
    font-size: 0.875rem;
    line-height: 1.5;
    word-break: break-word;
  }
  
  .category-actions {
    display: flex;
    gap: 0.5rem;
    flex-shrink: 0;
  }
  
  .action-btn {
    width: 2rem;
    height: 2rem;
    border: 1px solid #e5e7eb;
    border-radius: 0.375rem;
    background: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    transition: all 0.2s;
  }
  
  .action-btn:hover:not(:disabled) {
    background: #f9fafb;
    border-color: #d1d5db;
  }
  
  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .delete-btn:hover:not(:disabled) {
    background: #fee2e2;
    border-color: #fca5a5;
  }
  
  .category-meta {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.75rem;
    color: #9ca3af;
    margin-bottom: 1rem;
  }
  
  .select-btn {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 0.5rem;
    background: white;
    color: #374151;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .select-btn:hover {
    background: #f9fafb;
    border-color: #9ca3af;
  }
  
  .select-btn.selected {
    background: #3b82f6;
    color: white;
    border-color: #3b82f6;
  }
  
  .select-btn.selected:hover {
    background: #2563eb;
    border-color: #2563eb;
  }
  
  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
  }
  
  .empty-content h3 {
    margin: 0 0 0.75rem 0;
    color: #9ca3af;
    font-size: 1.5rem;
  }
  
  .empty-content p {
    margin: 0 0 1.5rem 0;
    color: #6b7280;
    max-width: 24rem;
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
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .modal-header h3 {
    margin: 0;
    color: #1f2937;
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  .modal-content {
    padding: 1.5rem;
  }
  
  .form-group {
    margin-bottom: 1.5rem;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #374151;
    font-size: 0.875rem;
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
  
  .color-selection {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .color-options {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .color-option {
    width: 2.5rem;
    height: 2.5rem;
    border: 2px solid transparent;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .color-option:hover {
    transform: scale(1.1);
  }
  
  .color-option.selected {
    border-color: #1f2937;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
  }
  
  .check-mark {
    font-size: 1rem;
    font-weight: bold;
  }
  
  .color-picker {
    width: 3rem !important;
    height: 2.5rem;
    padding: 0 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 0.375rem;
    cursor: pointer;
  }
  
  .category-preview {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
  }
  
  .preview-badge {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    font-weight: 600;
  }
  
  .preview-name {
    font-weight: 500;
    color: #1f2937;
    margin-bottom: 0.25rem;
  }
  
  .preview-description {
    font-size: 0.875rem;
    color: #6b7280;
  }
  
  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
  
  @media (max-width: 768px) {
    .categories-grid {
      grid-template-columns: 1fr;
    }
    
    .header {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }
    
    .category-info {
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 0.75rem;
    }
    
    .category-actions {
      justify-content: center;
    }
    
    .color-options {
      justify-content: center;
    }
    
    .color-selection {
      flex-direction: column;
      align-items: stretch;
      gap: 1rem;
    }
  }
</style>