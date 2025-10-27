# Local JOSS Paper Compilation Guide

## What Was Wrong

Your GitHub Actions workflow was failing due to **citation syntax errors** in `paper.md`:

1. **Line 34**: `` `[@lin:2012; @spector:1998; [@verharen:2019]` ``
   - **Problem**: Double opening bracket `[@` before `verharen:2019`
   - **Fixed to**: `` `[@lin:2012; @spector:1998; @verharen:2019]` ``

2. **Line 36**: `` `[@johnson:2010;@volcko:2020]` ``
   - **Problem**: Missing space after semicolon
   - **Fixed to**: `` `[@johnson:2010; @volcko:2020]` ``

These errors caused LaTeX to produce the error: `! Undefined control sequence. l.585 entry below for (\citeproc`

## ✅ Errors Have Been Fixed

The citation errors have already been corrected in your `paper.md` file. You can now:
- Commit these changes and push to GitHub (the workflow should now succeed)
- OR compile locally first to verify (see below)

## How to Compile Locally (Without Extra Commits)

### Option 1: Using the Provided Script (Recommended)

1. **Install Docker Desktop** (if not already installed):
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

2. **Run the compilation script**:
   ```cmd
   cd c:\Github\lickcalc\paper
   compile_locally.bat
   ```

3. **Check the output**:
   - If successful, you'll find `paper.pdf` in the `paper/` directory
   - If errors occur, they'll be displayed in the terminal

### Option 2: Manual Docker Command

If you prefer to run the Docker command manually:

```cmd
cd c:\Github\lickcalc\paper
docker run --rm -v "%cd%:/data" openjournals/inara -o pdf,crossref /data/paper.md
```

### Option 3: Using Pandoc (Without Docker)

If you have Pandoc installed locally with LaTeX support:

```cmd
cd c:\Github\lickcalc\paper
pandoc paper.md --citeproc --bibliography=paper.bib -o paper.pdf
```

**Note**: This may not produce identical output to the JOSS format, but it's useful for quick syntax checking.

## What the GitHub Actions Workflow Does

Your workflow (`.github/workflows/draft-pdf.yml`) runs on every push that changes files in the `paper/` directory. It:

1. Uses the `openjournals/openjournals-draft-action` to compile `paper.md`
2. Generates a PDF in JOSS journal format
3. Uploads the PDF as an artifact
4. Commits the PDF back to the repository

## Testing Your Changes

### Before Committing:

1. **Compile locally** using one of the methods above
2. **Check the PDF** to ensure it looks correct
3. **Verify citations** appear properly formatted

### After Committing:

1. Push your changes to GitHub
2. Go to **Actions** tab in your repository
3. Watch the "Draft PDF" workflow run
4. Download the artifact or check the committed PDF

## Common Citation Syntax Issues

To avoid similar errors in the future:

### ✅ Correct Citation Formats:

```markdown
`@author:year`                          → Author et al. (year)
`[@author:year]`                        → (Author et al., year)
`[@author1:year1; @author2:year2]`     → (Author1 et al., year1; Author2 et al., year2)
```

### ❌ Common Mistakes:

```markdown
`[@author:year;@other:year]`   ❌ Missing space after semicolon
`[@author:year; [@other:year]` ❌ Double opening bracket
`[@author:year]]`               ❌ Double closing bracket
[@author:year]                  ❌ Missing backticks
```

## Troubleshooting

### Docker Issues

**Problem**: "Docker is not installed or not in PATH"
- **Solution**: Install Docker Desktop and ensure it's running

**Problem**: "docker: Error response from daemon"
- **Solution**: Make sure Docker Desktop is running (check system tray)

### Compilation Errors

**Problem**: Citation errors
- **Solution**: Check all `@author:year` references are properly formatted
- **Solution**: Ensure all cited works exist in `paper.bib`

**Problem**: BibTeX errors
- **Solution**: Validate your `paper.bib` file syntax
- **Solution**: Ensure all required fields are present for each entry

**Problem**: LaTeX errors
- **Solution**: Check for special characters that need escaping: `& % $ # _ { } ~ ^ \`
- **Solution**: Use backticks for inline code: `` `code` ``

## Quick Validation Checklist

Before pushing changes to `paper.md`:

- [ ] All citations use proper syntax with backticks
- [ ] Semicolons in multi-citation brackets have spaces after them
- [ ] No double brackets in citations
- [ ] All cited works exist in `paper.bib`
- [ ] Special characters are properly escaped
- [ ] Compiles successfully locally

## Additional Resources

- [JOSS Submission Guide](https://joss.readthedocs.io/en/latest/submitting.html)
- [Pandoc Citation Syntax](https://pandoc.org/MANUAL.html#citations)
- [rMarkdown Citations](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
