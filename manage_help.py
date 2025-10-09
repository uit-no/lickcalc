"""
Helper script for managing help documentation chapters
"""

import sys
from pathlib import Path

def list_chapters():
    """List all chapter files"""
    chapters_dir = Path('templates/help_chapters')
    if not chapters_dir.exists():
        print("❌ Chapter directory not found!")
        return
    
    print("\n📚 Available Help Chapters:\n")
    chapters = sorted(chapters_dir.glob('*.html'))
    for i, chapter in enumerate(chapters, 1):
        size = chapter.stat().st_size
        print(f"{i:2d}. {chapter.stem:25s} ({size:,} bytes)")
    print(f"\nTotal: {len(chapters)} chapters\n")

def create_chapter(name):
    """Create a new chapter template"""
    chapters_dir = Path('templates/help_chapters')
    chapters_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename
    filename = name.lower().replace(' ', '-').replace('_', '-')
    filepath = chapters_dir / f"{filename}.html"
    
    if filepath.exists():
        print(f"❌ Chapter '{filename}' already exists!")
        return
    
    # Create template content
    title = name.title().replace('-', ' ')
    emoji = "📄"  # Default emoji
    
    template = f'''<!-- {title} Section -->
<section id="{filename}">
    <h2 class="section-header">{emoji} {title}</h2>
    <div class="card">
        <div class="card-body">
            <h5>Section Title</h5>
            <p>Add your content here...</p>
            
            <div class="tip-box">
                <strong>💡 Tip:</strong> Use this box for helpful tips.
            </div>
            
            <div class="warning-box">
                <strong>⚠️ Note:</strong> Use this box for important warnings.
            </div>
        </div>
    </div>
</section>
'''
    
    filepath.write_text(template, encoding='utf-8')
    print(f"✅ Created chapter: {filepath}")
    print(f"\n📝 Next steps:")
    print(f"1. Edit the content in: {filepath}")
    print(f"2. Add to templates/help.html sidebar:")
    print(f"   <li><a href=\"#{filename}\">{emoji} {title}</a></li>")
    print(f"3. Add include to templates/help.html content:")
    print(f"   {{% include 'help_chapters/{filename}.html' %}}")

def show_stats():
    """Show statistics about help documentation"""
    chapters_dir = Path('templates/help_chapters')
    if not chapters_dir.exists():
        print("❌ Chapter directory not found!")
        return
    
    chapters = list(chapters_dir.glob('*.html'))
    total_size = sum(c.stat().st_size for c in chapters)
    total_lines = sum(len(c.read_text(encoding='utf-8').splitlines()) for c in chapters)
    
    print("\n📊 Help Documentation Statistics:\n")
    print(f"Total chapters: {len(chapters)}")
    print(f"Total size:     {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print(f"Total lines:    {total_lines:,}")
    print(f"Avg per chapter: {total_lines//len(chapters) if chapters else 0} lines")
    print()

def main():
    if len(sys.argv) < 2:
        print("""
📚 Help Documentation Chapter Manager

Usage:
    python manage_help.py list              - List all chapters
    python manage_help.py create <name>     - Create a new chapter
    python manage_help.py stats             - Show statistics

Examples:
    python manage_help.py list
    python manage_help.py create advanced-features
    python manage_help.py stats
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_chapters()
    elif command == 'create':
        if len(sys.argv) < 3:
            print("❌ Please provide a chapter name")
            print("Example: python manage_help.py create my-new-chapter")
        else:
            create_chapter(sys.argv[2])
    elif command == 'stats':
        show_stats()
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: list, create, stats")

if __name__ == '__main__':
    main()
