# Help Documentation Structure

The help documentation has been refactored into a modular structure for easier maintenance and editing.

## Directory Structure

```
lickcalc_webapp/
├── templates/
│   ├── help.html                    # Main template (includes all chapters)
│   └── help_chapters/               # Individual chapter files
│       ├── overview.html
│       ├── getting-started.html
│       ├── file-formats.html
│       ├── session-analysis.html
│       ├── microstructural.html
│       ├── parameters.html
│       ├── data-export.html
│       ├── results-table.html
│       ├── advanced-use.html
│       ├── troubleshooting.html
│       ├── theoretical-practical.html
│       ├── references.html            # Present in folder, not included in help.html
│       └── glossary.html
└── assets/
    └── help_styles.css              # Shared CSS for help pages
```

## Editing the Help Documentation

### To edit a specific chapter:

1. Navigate to `templates/help_chapters/`
2. Open the relevant chapter file (e.g., `parameters.html`)
3. Edit the HTML content
4. Save the file
5. Refresh the help page in your browser

### To add a new chapter:

1. Create a new HTML file in `templates/help_chapters/`
   - Example: `new-feature.html`

2. Add the section content with proper structure:
   ```html
   <section id="new-feature">
       <h2 class="section-header">🆕 New Feature</h2>
       <div class="card">
           <div class="card-body">
               <p>Your content here...</p>
           </div>
       </div>
   </section>
   ```

3. Add the chapter to `templates/help.html`:
   - Add to the sidebar navigation (line ~28):
     ```html
     <li><a href="#new-feature">🆕 New Feature</a></li>
     ```
   - Add the include statement (line ~42):
     ```html
     {% include 'help_chapters/new-feature.html' %}
     ```

### Available CSS Classes:

**Content Boxes:**
- `.card` - Standard content card
- `.parameter-box` - Blue box for parameters
- `.tip-box` - Light blue box for tips
- `.warning-box` - Yellow box for warnings
- `.code-block` - Code/data format examples

**Headers:**
- `.section-header` - Main section title (H2)
- `.card-header` - Card header with blue background

**Layout:**
- Use Bootstrap grid classes: `.row`, `.col-md-6`, etc.
- Use Bootstrap accordion for collapsible sections

## How It Works

1. **Main Template**: `templates/help.html` contains the HTML structure, sidebar, and includes for all chapters

2. **Chapter Files**: Each chapter in `templates/help_chapters/` contains a `<section>` element with:
   - A unique `id` attribute (for navigation)
   - A section header
   - Content using Bootstrap cards and custom CSS classes

3. **Flask Rendering**: The `/help` route uses Flask's `render_template()` to:
   - Load the main template
   - Process Jinja2 `{% include %}` directives
   - Insert chapter content in order
   - Return a single HTML page

4. **JavaScript**: The help page includes JavaScript for:
   - Smooth scrolling to sections
   - Active section highlighting in sidebar
   - Responsive behavior on mobile

## Benefits of This Structure

✅ **Easy to Edit**: Each chapter is a separate file - no need to search through a 1000-line file

✅ **Maintainable**: Adding/removing/reordering chapters is simple

✅ **Version Control Friendly**: Git diffs are cleaner when changes are in separate files

✅ **Reusable**: Can include the same chapter in multiple places if needed

✅ **Organized**: Like a LaTeX document with separate chapter files

## Testing Changes

After editing any chapter:
1. Save the file
2. Restart the Dash app if needed (Flask templates are usually auto-reloaded)
3. Navigate to `http://localhost:8050/help`
4. Verify your changes appear correctly

## Original Backup

The original monolithic `help.html` file has been kept at `assets/help.html` as a backup.
