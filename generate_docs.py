import os
import markdown

def main():
    md_path = r'c:\Users\Admin\Desktop\GitHub\Auto-Task-Generator\project_documentation.md'
    html_path = r'c:\Users\Admin\Desktop\GitHub\Auto-Task-Generator\project_documentation.html'
    
    if not os.path.exists(md_path):
        print(f"Error: {md_path} not found.")
        return
        
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
        
    # Convert Markdown to HTML with extensions
    # 'fenced_code' handles ``` block code formatting
    # 'tables' parses Markdown table syntax
    # 'toc' helps structure document hierarchy (we will also build client-side sidebar)
    html_body = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
    
    # Beautiful responsive glassmorphism dark/light mode documentation template
    template = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto-Task-Generator Documentation</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    
    <!-- Highlight.js for Code Highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css" id="hljs-theme">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/javascript.min.js"></script>
    
    <!-- Mermaid.js for Diagrams -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    
    <style>
        /* Design System & Themes */
        :root[data-theme="dark"] {
            --bg-main: #0b0f19;
            --bg-card: rgba(17, 24, 39, 0.7);
            --bg-sidebar: rgba(15, 23, 42, 0.9);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            --accent-glow: rgba(99, 102, 241, 0.25);
            --code-bg: #1e293b;
            --table-header-bg: #1e293b;
            --table-row-even: #111827;
            --toc-hover-bg: rgba(255, 255, 255, 0.04);
            --toc-active-bg: rgba(99, 102, 241, 0.1);
        }
        
        :root[data-theme="light"] {
            --bg-main: #f8fafc;
            --bg-card: rgba(255, 255, 255, 0.8);
            --bg-sidebar: rgba(241, 245, 249, 0.95);
            --border-color: rgba(0, 0, 0, 0.08);
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --accent-primary: #4f46e5;
            --accent-secondary: #7c3aed;
            --accent-gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            --accent-glow: rgba(79, 70, 229, 0.15);
            --code-bg: #f1f5f9;
            --table-header-bg: #e2e8f0;
            --table-row-even: #f8fafc;
            --toc-hover-bg: rgba(0, 0, 0, 0.04);
            --toc-active-bg: rgba(79, 70, 229, 0.08);
        }
        
        /* Global Reset */
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-main);
            color: var(--text-primary);
            display: flex;
            min-height: 100vh;
            line-height: 1.625;
            transition: background-color 0.3s, color 0.3s;
        }
        
        /* Layout Structure */
        .sidebar {
            width: 320px;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border-color);
            position: fixed;
            top: 0;
            bottom: 0;
            left: 0;
            display: flex;
            flex-direction: column;
            padding: 2.5rem 1.5rem 1.5rem;
            z-index: 10;
            backdrop-filter: blur(16px);
        }
        
        .main-content {
            margin-left: 320px;
            flex: 1;
            padding: 4rem 5rem;
            max-width: 1100px;
            margin-right: auto;
        }
        
        /* Brand Logo */
        .logo-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 2rem;
        }
        
        .logo-icon {
            width: 2.5rem;
            height: 2.5rem;
            background: var(--accent-gradient);
            border-radius: 0.625rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 800;
            box-shadow: 0 4px 14px var(--accent-glow);
            font-size: 1.15rem;
        }
        
        .logo-title {
            font-weight: 800;
            font-size: 1.35rem;
            letter-spacing: -0.03em;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Sidebar Navigation List */
        .toc-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--text-muted);
            margin-bottom: 0.75rem;
            font-weight: 700;
            padding-left: 0.5rem;
        }
        
        .toc-container {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 1.5rem;
            padding-right: 0.25rem;
        }
        
        .toc-container ul {
            list-style: none;
            padding-left: 0;
        }
        
        .toc-container li {
            margin-bottom: 0.25rem;
        }
        
        .toc-container a {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.9rem;
            display: block;
            padding: 0.5rem 0.75rem;
            border-radius: 0.5rem;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .toc-container a:hover {
            color: var(--text-primary);
            background-color: var(--toc-hover-bg);
            padding-left: 1rem;
        }
        
        .toc-container .toc-active {
            color: var(--accent-primary);
            background-color: var(--toc-active-bg);
            font-weight: 600;
            box-shadow: inset 3px 0 0 var(--accent-primary);
            padding-left: 1rem;
        }
        
        .toc-container ul ul {
            padding-left: 1rem;
            margin-top: 0.25rem;
            border-left: 1px solid var(--border-color);
            margin-left: 0.5rem;
        }
        
        .toc-container ul ul a {
            font-size: 0.85rem;
            padding: 0.35rem 0.75rem;
        }
        
        /* Sidebar Action Bar */
        .sidebar-footer {
            border-top: 1px solid var(--border-color);
            padding-top: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .theme-toggle-btn {
            background: none;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 0.6rem;
            border-radius: 0.5rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }
        
        .theme-toggle-btn:hover {
            color: var(--text-primary);
            border-color: var(--text-secondary);
            background-color: var(--toc-hover-bg);
            transform: scale(1.05);
        }
        
        /* Markdown / Typography Styles */
        h1, h2, h3, h4 {
            font-weight: 700;
            color: var(--text-primary);
            margin-top: 2.75rem;
            margin-bottom: 1.25rem;
            letter-spacing: -0.025em;
        }
        
        h1 {
            font-size: 2.65rem;
            font-weight: 800;
            margin-top: 0;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.25rem;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2.25rem;
        }
        
        h2 {
            font-size: 1.75rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.6rem;
            margin-top: 3.5rem;
        }
        
        h3 {
            font-size: 1.3rem;
            margin-top: 2.25rem;
        }
        
        p {
            margin-bottom: 1.5rem;
            color: var(--text-secondary);
            font-size: 1.05rem;
            word-wrap: break-word;
        }
        
        /* Lists formatting */
        ul, ol {
            margin-bottom: 1.5rem;
            padding-left: 1.5rem;
            color: var(--text-secondary);
        }
        
        li {
            margin-bottom: 0.5rem;
            font-size: 1.05rem;
        }
        
        /* Code & Preformatted Blocks */
        pre {
            background-color: var(--code-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1.25rem;
            margin-bottom: 1.75rem;
            overflow-x: auto;
            position: relative;
        }
        
        code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.925rem;
        }
        
        p code, li code {
            background-color: var(--code-bg);
            padding: 0.2rem 0.45rem;
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            font-size: 0.85em;
            color: var(--accent-secondary);
            word-wrap: break-word;
        }
        
        /* Copy to Clipboard Button */
        .copy-btn {
            position: absolute;
            top: 0.6rem;
            right: 0.6rem;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-color);
            color: #d1d5db;
            padding: 0.3rem 0.6rem;
            font-size: 0.75rem;
            font-weight: 500;
            border-radius: 0.375rem;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s, background 0.2s, color 0.2s;
            backdrop-filter: blur(4px);
        }
        
        pre:hover .copy-btn {
            opacity: 1;
        }
        
        .copy-btn:hover {
            background: var(--accent-primary);
            color: white;
            border-color: transparent;
        }
        
        /* Interactive Mermaid Diagrams */
        .mermaid {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 2rem 1.5rem;
            margin: 2rem 0;
            display: flex;
            justify-content: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        
        /* Elegant Table Designs */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 2rem 0;
            font-size: 0.95rem;
            border-radius: 0.75rem;
            overflow: hidden;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }
        
        th, td {
            padding: 0.9rem 1.2rem;
            text-align: left;
        }
        
        th {
            background-color: var(--table-header-bg);
            color: var(--text-primary);
            font-weight: 600;
            border-bottom: 2px solid var(--border-color);
            letter-spacing: 0.02em;
        }
        
        td {
            border-bottom: 1px solid var(--border-color);
            color: var(--text-secondary);
        }
        
        tr:nth-child(even) {
            background-color: var(--table-row-even);
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        /* Miscellaneous styles */
        hr {
            border: 0;
            height: 1px;
            background-color: var(--border-color);
            margin: 3.5rem 0;
        }
        
        /* Scrollbar customizing */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }
        
        /* Responsive Mobile/Tablet Layouts */
        @media (max-width: 1024px) {
            .main-content {
                padding: 3rem 2.5rem;
            }
        }
        
        @media (max-width: 900px) {
            body {
                flex-direction: column;
            }
            .sidebar {
                width: 100%;
                position: relative;
                height: auto;
                padding: 1.5rem;
                border-right: none;
                border-bottom: 1px solid var(--border-color);
            }
            .main-content {
                margin-left: 0;
                padding: 2.5rem 1.5rem;
                max-width: 100%;
            }
        }
    </style>
</head>
<body>
    <aside class="sidebar">
        <div class="logo-container">
            <div class="logo-icon">⚙️</div>
            <div class="logo-title">Auto-Task</div>
        </div>
        <div class="toc-title">Documentation</div>
        <nav class="toc-container" id="toc">
            <!-- Table of contents will be generated here -->
        </nav>
        <div class="sidebar-footer">
            <button class="theme-toggle-btn" id="theme-toggle" title="Toggle theme">
                <svg id="theme-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="5"></circle>
                    <line x1="12" y1="1" x2="12" y2="3"></line>
                    <line x1="12" y1="21" x2="12" y2="23"></line>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                    <line x1="1" y1="12" x2="3" y2="12"></line>
                    <line x1="21" y1="12" x2="23" y2="12"></line>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                </svg>
            </button>
            <span style="font-size: 0.75rem; color: var(--text-muted);">Auto-Task v1.0.0</span>
        </div>
    </aside>
    
    <main class="main-content">
        <article class="markdown-body">
<!-- RENDERED_MARKDOWN_HERE -->
        </article>
    </main>
    
    <script>
        // Init highlight.js code highlighting
        hljs.highlightAll();
        
        // Transform fenced markdown mermaid code blocks to styled divs
        document.querySelectorAll('pre code.language-mermaid').forEach(el => {
            const pre = el.parentElement;
            const div = document.createElement('div');
            div.className = 'mermaid';
            div.textContent = el.textContent;
            
            // Remove code copy button if present
            const btn = pre.querySelector('.copy-btn');
            if (btn) btn.remove();
            
            pre.replaceWith(div);
        });
        
        // Initialize Mermaid
        mermaid.initialize({ 
            startOnLoad: true, 
            theme: document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'default',
            securityLevel: 'loose'
        });
        
        // Add Copy Buttons to non-mermaid Code Blocks
        document.querySelectorAll('pre').forEach(pre => {
            if (pre.querySelector('.mermaid')) return;
            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.textContent = 'Copy';
            btn.addEventListener('click', () => {
                const code = pre.querySelector('code');
                navigator.clipboard.writeText(code.textContent).then(() => {
                    btn.textContent = 'Copied!';
                    setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
                });
            });
            pre.appendChild(btn);
        });
        
        // Theme Manager
        const toggleBtn = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        
        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            
            // Reinitialize mermaid with the proper theme
            if (window.mermaid) {
                mermaid.initialize({ 
                    theme: theme === 'dark' ? 'dark' : 'default' 
                });
                // Note: to update already rendered SVG colors, a page reload is usually cleanest, 
                // but setting theme will make new rendering correct.
            }
            
            // Toggle highlight.js styles
            const hljsTheme = document.getElementById('hljs-theme');
            if (hljsTheme) {
                hljsTheme.href = theme === 'dark' 
                    ? 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css'
                    : 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css';
            }
            
            // Toggle Theme Button SVG Icon
            if (theme === 'dark') {
                themeIcon.innerHTML = `
                    <circle cx="12" cy="12" r="5"></circle>
                    <line x1="12" y1="1" x2="12" y2="3"></line>
                    <line x1="12" y1="21" x2="12" y2="23"></line>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                    <line x1="1" y1="12" x2="3" y2="12"></line>
                    <line x1="21" y1="12" x2="23" y2="12"></line>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                `;
            } else {
                themeIcon.innerHTML = `
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                `;
            }
        }
        
        // Initial setup on theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            setTheme(savedTheme);
        } else {
            setTheme(prefersDark.matches ? 'dark' : 'light');
        }
        
        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            setTheme(currentTheme === 'dark' ? 'light' : 'dark');
        });
        
        // Generate Sidebar Table of Contents
        const tocContainer = document.getElementById('toc');
        const headings = document.querySelectorAll('.markdown-body h2, .markdown-body h3');
        if (headings.length > 0) {
            const ul = document.createElement('ul');
            let currentH2Li = null;
            let currentH2Ul = null;
            
            headings.forEach((heading) => {
                if (!heading.id) {
                    heading.id = heading.textContent.toLowerCase()
                        .replace(/[^\w\s-]/g, '')
                        .trim()
                        .replace(/\s+/g, '-');
                }
                
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = '#' + heading.id;
                a.textContent = heading.textContent.replace(/^[^\w\s]+/, '').trim();
                
                if (heading.tagName === 'H2') {
                    li.appendChild(a);
                    ul.appendChild(li);
                    currentH2Li = li;
                    currentH2Ul = null;
                } else if (heading.tagName === 'H3' && currentH2Li) {
                    if (!currentH2Ul) {
                        currentH2Ul = document.createElement('ul');
                        currentH2Li.appendChild(currentH2Ul);
                    }
                    li.appendChild(a);
                    currentH2Ul.appendChild(li);
                }
            });
            tocContainer.appendChild(ul);
        }
        
        // Track Scroll for Table of Contents Highlights
        const tocLinks = document.querySelectorAll('.toc-container a');
        const sections = Array.from(headings);
        
        function scrollHandler() {
            let currentSection = null;
            const scrollPos = window.scrollY + 100;
            
            for (let section of sections) {
                if (section.offsetTop <= scrollPos) {
                    currentSection = section;
                } else {
                    break;
                }
            }
            
            tocLinks.forEach(link => {
                link.classList.remove('toc-active');
                if (currentSection && link.getAttribute('href') === '#' + currentSection.id) {
                    link.classList.add('toc-active');
                }
            });
        }
        
        window.addEventListener('scroll', scrollHandler);
        scrollHandler(); // run initially
    </script>
</body>
</html>
"""
    final_html = template.replace('<!-- RENDERED_MARKDOWN_HERE -->', html_body)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print(f"Successfully generated HTML documentation file at: {html_path}")

if __name__ == '__main__':
    main()
