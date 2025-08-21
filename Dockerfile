# Custom OpenWebUI with Blueprint Theme for tojo.world
FROM ghcr.io/open-webui/open-webui:main

# Metadata
LABEL org.opencontainers.image.title="OpenWebUI with Blueprint Theme"
LABEL org.opencontainers.image.description="OpenWebUI with integrated blueprint theme for tojo.world"
LABEL org.opencontainers.image.vendor="tojo.world"

# Switch to root to install custom theme
USER root

# Create directories for custom frontend files
RUN mkdir -p /app/backend/static/themes/blueprint

# Copy blueprint theme files
COPY src/frontend/styles/blueprint-theme.css /app/backend/static/themes/blueprint/
COPY src/frontend/styles/blueprint-components.css /app/backend/static/themes/blueprint/
COPY src/frontend/stores/theme.js /app/backend/static/themes/blueprint/
COPY src/frontend/components/ThemeSelector.svelte /app/backend/static/themes/blueprint/

# Copy integration files for reference
COPY src/frontend/blueprint-theme-demo.html /app/backend/static/themes/blueprint/
COPY src/frontend/integration-test.html /app/backend/static/themes/blueprint/
COPY src/frontend/BLUEPRINT_THEME_README.md /app/backend/static/themes/blueprint/

# Create a simple theme injection script
RUN cat > /app/backend/static/themes/blueprint/inject-theme.js << 'EOF'
// Blueprint Theme Injection for OpenWebUI
(function() {
    'use strict';
    
    console.log('Injecting Blueprint Theme for tojo.world...');
    
    // Load CSS files
    const blueprintCSS = document.createElement('link');
    blueprintCSS.rel = 'stylesheet';
    blueprintCSS.href = '/themes/blueprint/blueprint-theme.css';
    document.head.appendChild(blueprintCSS);
    
    const blueprintComponentsCSS = document.createElement('link');
    blueprintComponentsCSS.rel = 'stylesheet';
    blueprintComponentsCSS.href = '/themes/blueprint/blueprint-components.css';
    document.head.appendChild(blueprintComponentsCSS);
    
    // Apply blueprint theme class
    document.documentElement.classList.add('theme-blueprint');
    
    // Add tojo.world watermark
    function addWatermark() {
        if (!document.querySelector('.tojo-watermark')) {
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
            `;
            document.body.appendChild(watermark);
        }
    }
    
    // Add compass navigation element
    function addCompassElement() {
        const compass = document.createElement('div');
        compass.className = 'tojo-compass';
        compass.style.cssText = `
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
            font-size: 12px;
            color: #003d7a;
            font-weight: 600;
        `;
        compass.innerHTML = `
            <style>
                .tojo-compass::before {
                    content: '';
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    border: 1px solid #003d7a;
                    border-radius: 50%;
                    background: #fefcf6;
                }
                .tojo-compass::after {
                    content: 'N';
                    position: absolute;
                    top: 2px;
                    font-size: 8px;
                    line-height: 1;
                    z-index: 1;
                }
            </style>
        `;
        
        // Try to add to navigation if it exists
        const nav = document.querySelector('nav') || document.querySelector('.navbar') || document.querySelector('header');
        if (nav) {
            nav.appendChild(compass);
        }
    }
    
    // Apply theme enhancements
    function applyBlueprintEnhancements() {
        // Add grid background
        document.body.style.backgroundImage = `
            linear-gradient(rgba(0, 61, 122, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 61, 122, 0.1) 1px, transparent 1px)
        `;
        document.body.style.backgroundSize = '20px 20px';
        
        // Apply paper background color
        document.body.style.backgroundColor = '#f0ede5';
        
        // Style any existing buttons with blueprint theme
        const buttons = document.querySelectorAll('button');
        buttons.forEach(button => {
            if (!button.classList.contains('blueprint-styled')) {
                button.style.fontFamily = "'Monaco', 'Consolas', 'Courier New', monospace";
                button.style.fontSize = '12px';
                button.style.textTransform = 'uppercase';
                button.style.letterSpacing = '0.5px';
                button.classList.add('blueprint-styled');
            }
        });
    }
    
    // Initialize theme after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                addWatermark();
                addCompassElement();
                applyBlueprintEnhancements();
            }, 1000);
        });
    } else {
        setTimeout(() => {
            addWatermark();
            addCompassElement();
            applyBlueprintEnhancements();
        }, 1000);
    }
    
    console.log('Blueprint theme injection complete for tojo.world');
})();
EOF

# Create a custom index.html injection
RUN cat > /app/backend/static/themes/blueprint/inject-head.html << 'EOF'
<link rel="stylesheet" href="/themes/blueprint/blueprint-theme.css">
<link rel="stylesheet" href="/themes/blueprint/blueprint-components.css">
<script src="/themes/blueprint/inject-theme.js"></script>
<style>
:root {
  --blueprint-primary: #003d7a;
  --blueprint-secondary: #0066cc;
  --blueprint-tertiary: #4da6ff;
  --blueprint-accent: #ff6b35;
  --paper-base: #fefcf6;
  --paper-secondary: #f8f6f0;
  --paper-tertiary: #f0ede5;
}
body {
  background: var(--paper-tertiary) !important;
}
.theme-blueprint {
  font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}
</style>
EOF

# Create a startup script to inject theme
RUN cat > /app/inject-blueprint-theme.sh << 'EOF'
#!/bin/bash
echo "Injecting Blueprint Theme for tojo.world..."

# Try to find and inject into HTML files with better error handling
find /app -name "*.html" -type f -writable 2>/dev/null | while read file; do
    if grep -q "<head>" "$file" && ! grep -q "blueprint-theme.css" "$file"; then
        echo "Injecting theme into $file"
        # Use a more robust injection method
        if cp "$file" "$file.bak" 2>/dev/null; then
            awk '/<head>/{print; print "    <link rel=\"stylesheet\" href=\"/themes/blueprint/blueprint-theme.css\">"; print "    <link rel=\"stylesheet\" href=\"/themes/blueprint/blueprint-components.css\">"; print "    <script src=\"/themes/blueprint/blueprint-inject.js\"></script>"; next}1' "$file.bak" > "$file" 2>/dev/null || cp "$file.bak" "$file"
            rm -f "$file.bak"
        fi
    fi
done

echo "Blueprint theme injection complete!"
EOF

RUN chmod +x /app/inject-blueprint-theme.sh

# Switch back to the original user
USER 1000

# Set environment variable to indicate blueprint theme is available
ENV BLUEPRINT_THEME_ENABLED=true
ENV TOJO_WORLD_BRANDING=true

# Expose the same port as the base image
EXPOSE 8080

# Use the original command but inject our theme first
CMD ["/bin/bash", "-c", "/app/inject-blueprint-theme.sh && exec bash start.sh"]