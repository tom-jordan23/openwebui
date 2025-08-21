<!--
  Theme Selector Component
  Allows users to switch between Original and Blueprint themes
  Integrates with tojo.world branding
-->
<script>
  import { currentTheme, setTheme, getAvailableThemes, THEMES } from '../stores/theme.js';
  import '../styles/blueprint-theme.css';
  import '../styles/blueprint-components.css';
  
  // Get available themes
  const themes = getAvailableThemes();
  
  // Component state
  let isOpen = false;
  let selectedTheme = $currentTheme;
  
  // Handle theme change
  function handleThemeChange(themeId) {
    setTheme(themeId);
    selectedTheme = themeId;
    isOpen = false;
  }
  
  // Toggle dropdown
  function toggleDropdown() {
    isOpen = !isOpen;
  }
  
  // Close dropdown when clicking outside
  function handleClickOutside(event) {
    if (!event.target.closest('.theme-selector')) {
      isOpen = false;
    }
  }
  
  // Format theme name for display
  function getThemeDisplayName(theme) {
    if (theme.id === THEMES.BLUEPRINT) {
      return `${theme.name} (tojo.world)`;
    }
    return theme.name;
  }
</script>

<svelte:window on:click={handleClickOutside} />

<div class="theme-selector" class:blueprint={$currentTheme === THEMES.BLUEPRINT}>
  <button 
    class="theme-toggle"
    class:blueprint-button={$currentTheme === THEMES.BLUEPRINT}
    on:click={toggleDropdown}
    aria-label="Select theme"
  >
    <div class="theme-icon">
      {#if $currentTheme === THEMES.BLUEPRINT}
        <div class="tojo-compass"></div>
      {:else}
        🎨
      {/if}
    </div>
    <span class="theme-name">
      {themes.find(t => t.id === selectedTheme)?.name || 'Theme'}
    </span>
    <div class="dropdown-arrow" class:open={isOpen}>▼</div>
  </button>
  
  {#if isOpen}
    <div 
      class="theme-dropdown"
      class:blueprint-modal={$currentTheme === THEMES.BLUEPRINT}
    >
      <div class="dropdown-header">
        <span class="dropdown-title">Select Theme</span>
        {#if $currentTheme === THEMES.BLUEPRINT}
          <div class="tojo-brand-element">
            <div class="tojo-logo-mini"></div>
            <span>tojo.world</span>
          </div>
        {/if}
      </div>
      
      <div class="theme-options">
        {#each themes as theme}
          <button
            class="theme-option"
            class:active={theme.id === selectedTheme}
            class:blueprint-nav-item={$currentTheme === THEMES.BLUEPRINT}
            on:click={() => handleThemeChange(theme.id)}
          >
            <div class="option-icon">
              {#if theme.id === THEMES.BLUEPRINT}
                <div class="tojo-compass"></div>
              {:else}
                🎨
              {/if}
            </div>
            <div class="option-content">
              <div class="option-name">{getThemeDisplayName(theme)}</div>
              <div class="option-description">{theme.description}</div>
            </div>
            {#if theme.id === selectedTheme}
              <div class="option-check">✓</div>
            {/if}
          </button>
        {/each}
      </div>
      
      {#if $currentTheme === THEMES.BLUEPRINT}
        <div class="dropdown-footer">
          <div class="blueprint-info">
            <div class="info-title">Blueprint Theme</div>
            <div class="info-text">
              Technical drawing inspired interface designed for precision and clarity.
              Subtly branded for tojo.world deployment.
            </div>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .theme-selector {
    position: relative;
    display: inline-block;
  }
  
  .theme-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 120px;
  }
  
  .theme-toggle:hover {
    background: #f9fafb;
    border-color: #d1d5db;
  }
  
  .theme-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    font-size: 14px;
  }
  
  .theme-name {
    flex: 1;
    text-align: left;
    font-weight: 500;
    color: #374151;
  }
  
  .dropdown-arrow {
    font-size: 10px;
    color: #9ca3af;
    transition: transform 0.2s ease;
  }
  
  .dropdown-arrow.open {
    transform: rotate(180deg);
  }
  
  .theme-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    z-index: 1000;
    margin-top: 4px;
    overflow: hidden;
  }
  
  .dropdown-header {
    padding: 12px 16px;
    border-bottom: 1px solid #f3f4f6;
    background: #f9fafb;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .dropdown-title {
    font-weight: 600;
    color: #374151;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  
  .theme-options {
    max-height: 300px;
    overflow-y: auto;
  }
  
  .theme-option {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: none;
    border: none;
    text-align: left;
    cursor: pointer;
    transition: background 0.2s ease;
    border-bottom: 1px solid #f3f4f6;
  }
  
  .theme-option:last-child {
    border-bottom: none;
  }
  
  .theme-option:hover {
    background: #f9fafb;
  }
  
  .theme-option.active {
    background: #eff6ff;
    color: #2563eb;
  }
  
  .option-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }
  
  .option-content {
    flex: 1;
    min-width: 0;
  }
  
  .option-name {
    font-weight: 500;
    color: #374151;
    font-size: 14px;
    margin-bottom: 2px;
  }
  
  .option-description {
    font-size: 12px;
    color: #6b7280;
    line-height: 1.3;
  }
  
  .option-check {
    font-size: 14px;
    color: #10b981;
    font-weight: 600;
  }
  
  .dropdown-footer {
    padding: 12px 16px;
    border-top: 1px solid #f3f4f6;
    background: #fafafa;
  }
  
  .blueprint-info {
    text-align: left;
  }
  
  .info-title {
    font-weight: 600;
    color: #374151;
    font-size: 12px;
    margin-bottom: 4px;
  }
  
  .info-text {
    font-size: 11px;
    color: #6b7280;
    line-height: 1.4;
  }
  
  /* Blueprint theme overrides */
  .theme-selector.blueprint .theme-toggle {
    background: var(--paper-base);
    border: var(--border-weight-thin) solid var(--line-construction);
    border-bottom: var(--border-weight-medium) solid var(--blueprint-primary);
    font-family: var(--font-technical);
    font-size: 12px;
  }
  
  .theme-selector.blueprint .theme-toggle:hover {
    background: var(--paper-secondary);
    border-color: var(--blueprint-primary);
  }
  
  .theme-selector.blueprint .theme-name {
    color: var(--text-primary);
    font-weight: 600;
  }
  
  .theme-selector.blueprint .theme-dropdown {
    background: var(--paper-base);
    border: var(--border-weight-medium) solid var(--blueprint-primary);
    border-radius: 4px;
    box-shadow: var(--shadow-elevation);
  }
  
  .theme-selector.blueprint .dropdown-header {
    background: var(--blueprint-primary);
    color: var(--paper-base);
    border-bottom: var(--border-weight-thin) solid var(--paper-base);
  }
  
  .theme-selector.blueprint .dropdown-title {
    color: var(--paper-base);
    font-family: var(--font-technical);
  }
  
  .theme-selector.blueprint .theme-option {
    border-bottom: var(--border-weight-thin) solid var(--line-construction);
    font-family: var(--font-technical);
    font-size: 11px;
  }
  
  .theme-selector.blueprint .theme-option:hover {
    background: var(--paper-secondary);
  }
  
  .theme-selector.blueprint .theme-option.active {
    background: var(--blueprint-secondary);
    color: var(--paper-base);
  }
  
  .theme-selector.blueprint .option-name {
    color: var(--text-primary);
    font-weight: 600;
  }
  
  .theme-selector.blueprint .theme-option.active .option-name {
    color: var(--paper-base);
  }
  
  .theme-selector.blueprint .option-description {
    color: var(--text-tertiary);
  }
  
  .theme-selector.blueprint .theme-option.active .option-description {
    color: rgba(255, 255, 255, 0.8);
  }
  
  .theme-selector.blueprint .dropdown-footer {
    background: var(--paper-secondary);
    border-top: var(--border-weight-thin) solid var(--line-construction);
  }
  
  .theme-selector.blueprint .info-title {
    color: var(--blueprint-primary);
    font-family: var(--font-technical);
    font-weight: 600;
    text-transform: uppercase;
  }
  
  .theme-selector.blueprint .info-text {
    color: var(--text-secondary);
    font-family: var(--font-body);
  }
  
  /* Responsive adjustments */
  @media (max-width: 640px) {
    .theme-dropdown {
      left: -100px;
      right: -100px;
      width: auto;
    }
    
    .theme-toggle {
      min-width: 100px;
      font-size: 12px;
    }
  }
</style>