# Quick Start Guide: Editing Help Documentation

## TL;DR

Help documentation is now split into **12 separate chapter files** for easy editing!

## File Locations

```
templates/help_chapters/
├── overview.html           ← App overview
├── getting-started.html    ← Setup instructions  
├── file-formats.html       ← Supported formats
├── session-analysis.html   ← Session graphs
├── microstructural.html    ← Burst analysis
├── parameters.html         ← Parameter docs ⭐ Most edited
├── data-export.html        ← Export features
├── results-table.html      ← Results management
├── advanced-use.html       ← Advanced usage
├── troubleshooting.html    ← Common issues
├── theoretical-practical.html ← Background/context
├── references.html        ← Present in the folder, not linked in help.html
└── glossary.html           ← Terminology
```

## Most Common Tasks

### Edit a Parameter Description

```bash
code templates/help_chapters/parameters.html
```

### Add Troubleshooting Item

```bash
code templates/help_chapters/troubleshooting.html
# Add accordion item following existing pattern
```

### Update Getting Started

```bash
code templates/help_chapters/getting-started.html
```

## Quick Commands

```bash
# List all chapters
python manage_help.py list

# Show statistics  
python manage_help.py stats

# Create new chapter
python manage_help.py create my-new-section
```

## That's It!

Just edit the relevant `.html` file in `templates/help_chapters/` and save. 

No need to search through a 1000-line file anymore! 🎉
