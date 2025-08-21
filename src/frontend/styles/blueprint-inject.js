// Blueprint Theme Injection for OpenWebUI on tojo.world
// This script automatically applies the blueprint theme to any OpenWebUI instance

(function() {
    'use strict';
    
    console.log('🎨 Initializing Blueprint Theme for tojo.world...');
    
    // Theme configuration
    const THEME_CONFIG = {
        name: 'Blueprint',
        version: '1.0',
        environment: 'tojo.world',
        colors: {
            primary: '#003d7a',
            secondary: '#0066cc',
            tertiary: '#4da6ff',
            accent: '#ff6b35',
            paperBase: '#fefcf6',
            paperSecondary: '#f8f6f0',
            paperTertiary: '#f0ede5'
        }
    };
    
    // Load CSS files
    function loadCSS(href, id) {
        if (document.getElementById(id)) return;
        
        const link = document.createElement('link');
        link.id = id;
        link.rel = 'stylesheet';
        link.type = 'text/css';
        link.href = href;
        link.onload = () => console.log(`✅ Loaded: ${href}`);
        link.onerror = () => console.warn(`❌ Failed to load: ${href}`);
        document.head.appendChild(link);
    }
    
    // Apply CSS variables
    function applyCSSVariables() {
        const root = document.documentElement;
        Object.entries(THEME_CONFIG.colors).forEach(([key, value]) => {
            const cssVar = `--${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`;
            root.style.setProperty(cssVar, value);
        });
        
        // Additional theme variables
        root.style.setProperty('--blueprint-primary', THEME_CONFIG.colors.primary);
        root.style.setProperty('--blueprint-secondary', THEME_CONFIG.colors.secondary);
        root.style.setProperty('--blueprint-tertiary', THEME_CONFIG.colors.tertiary);
        root.style.setProperty('--blueprint-accent', THEME_CONFIG.colors.accent);
        root.style.setProperty('--paper-base', THEME_CONFIG.colors.paperBase);
        root.style.setProperty('--paper-secondary', THEME_CONFIG.colors.paperSecondary);
        root.style.setProperty('--paper-tertiary', THEME_CONFIG.colors.paperTertiary);
        
        console.log('✅ CSS variables applied');
    }
    
    // Apply theme classes
    function applyThemeClasses() {
        document.documentElement.classList.add('theme-blueprint');
        document.body.classList.add('blueprint-grid');
        console.log('✅ Theme classes applied');
    }
    
    // Add tojo.world watermark
    function addWatermark() {
        if (document.querySelector('.tojo-watermark')) return;
        
        const watermark = document.createElement('div');
        watermark.className = 'tojo-watermark';
        watermark.textContent = 'hosted on tojo.world';
        watermark.style.cssText = `
            position: fixed;
            bottom: 10px;
            right: 10px;
            font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
            font-size: 10px;
            color: rgba(0, 61, 122, 0.6);
            opacity: 0.6;
            user-select: none;
            pointer-events: none;
            z-index: 1000;
            font-weight: 600;
        `;
        document.body.appendChild(watermark);
        console.log('✅ tojo.world watermark added');
    }
    
    // Add compass navigation element
    function addCompassElement() {
        // Look for navigation areas
        const navSelectors = [
            'nav', '.navbar', '.nav', '.navigation', 
            'header', '.header', '.topbar', '.top-bar',
            '.sidebar', '.side-nav'
        ];
        
        let targetNav = null;
        for (const selector of navSelectors) {
            const element = document.querySelector(selector);
            if (element && element.offsetParent !== null) {
                targetNav = element;
                break;
            }
        }
        
        if (targetNav && !targetNav.querySelector('.tojo-compass')) {
            const compass = document.createElement('div');
            compass.className = 'tojo-compass';
            compass.title = 'Blueprint Theme - tojo.world';
            compass.style.cssText = `
                position: relative;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 24px;
                height: 24px;
                margin: 0 8px;
                font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
                font-size: 8px;
                color: ${THEME_CONFIG.colors.primary};
                font-weight: 700;
                border: 1px solid ${THEME_CONFIG.colors.primary};
                border-radius: 50%;
                background: ${THEME_CONFIG.colors.paperBase};
                cursor: pointer;
                transition: all 0.2s ease;
            `;
            compass.innerHTML = 'N';
            compass.addEventListener('click', () => {
                console.log('🧭 Blueprint Theme Active - tojo.world');
            });
            
            targetNav.appendChild(compass);
            console.log('✅ Compass navigation element added');
        }
    }
    
    // Apply background grid pattern
    function applyGridBackground() {
        document.body.style.backgroundImage = `
            linear-gradient(rgba(0, 61, 122, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 61, 122, 0.1) 1px, transparent 1px)
        `;
        document.body.style.backgroundSize = '20px 20px';
        document.body.style.backgroundColor = THEME_CONFIG.colors.paperTertiary;
        console.log('✅ Grid background applied');
    }
    
    // Enhance existing UI elements
    function enhanceUIElements() {
        // Style buttons with blueprint aesthetic
        const buttons = document.querySelectorAll('button:not(.blueprint-enhanced)');
        buttons.forEach(button => {
            button.classList.add('blueprint-enhanced');
            button.style.fontFamily = "'Monaco', 'Consolas', 'Courier New', monospace";
            button.style.fontSize = '12px';
            button.style.fontWeight = '600';
            button.style.textTransform = 'uppercase';
            button.style.letterSpacing = '0.5px';
            button.style.transition = 'all 0.2s ease';
            
            // Add hover effects
            const originalBg = button.style.backgroundColor;
            button.addEventListener('mouseenter', () => {
                button.style.backgroundColor = THEME_CONFIG.colors.secondary;
                button.style.color = THEME_CONFIG.colors.paperBase;
            });
            button.addEventListener('mouseleave', () => {
                button.style.backgroundColor = originalBg;
            });
        });
        
        // Style inputs with technical drawing aesthetic
        const inputs = document.querySelectorAll('input:not(.blueprint-enhanced), textarea:not(.blueprint-enhanced)');
        inputs.forEach(input => {
            input.classList.add('blueprint-enhanced');
            input.style.fontFamily = "'Monaco', 'Consolas', 'Courier New', monospace";
            input.style.fontSize = '13px';
            input.style.borderBottom = `2px solid ${THEME_CONFIG.colors.primary}`;
            input.style.background = THEME_CONFIG.colors.paperBase;
        });
        
        console.log(`✅ Enhanced ${buttons.length} buttons and ${inputs.length} inputs`);
    }
    
    // Monitor for dynamic content changes
    function observeDOMChanges() {
        const observer = new MutationObserver((mutations) => {
            let needsEnhancement = false;
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    needsEnhancement = true;
                }
            });
            
            if (needsEnhancement) {
                setTimeout(() => {
                    enhanceUIElements();
                    addCompassElement();
                }, 500);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('✅ DOM observer active');
    }
    
    // Initialize theme
    function initializeTheme() {
        console.log(`🎨 Initializing ${THEME_CONFIG.name} theme v${THEME_CONFIG.version} for ${THEME_CONFIG.environment}`);
        
        // Load CSS files
        loadCSS('/themes/blueprint/blueprint-theme.css', 'blueprint-theme-css');
        loadCSS('/themes/blueprint/blueprint-components.css', 'blueprint-components-css');
        
        // Apply theme immediately
        applyCSSVariables();
        applyThemeClasses();
        applyGridBackground();
        
        // Add branded elements
        addWatermark();
        
        // Enhance UI elements after a brief delay
        setTimeout(() => {
            enhanceUIElements();
            addCompassElement();
            observeDOMChanges();
        }, 1000);
        
        console.log('🎉 Blueprint theme initialization complete!');
    }
    
    // Start initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeTheme);
    } else {
        initializeTheme();
    }
    
    // Expose theme utilities globally
    window.BlueprintTheme = {
        config: THEME_CONFIG,
        reinitialize: initializeTheme,
        addWatermark: addWatermark,
        addCompass: addCompassElement,
        enhance: enhanceUIElements
    };
    
})();