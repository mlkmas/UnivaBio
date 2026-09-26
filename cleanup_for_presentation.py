# cleanup_for_presentation.py
"""
Quick cleanup script before presentation
Deletes the old Live_Recording page
"""
from pathlib import Path

print("=" * 70)
print("🧹 CLEANUP FOR PRESENTATION")
print("=" * 70)

# Delete old Live_Recording page
old_page = Path("pages/5_Live_Recording.py")

if old_page.exists():
    try:
        old_page.unlink()
        print("✅ Deleted: pages/5_Live_Recording.py")
    except Exception as e:
        print(f"❌ Error deleting file: {e}")
else:
    print("ℹ️  File already deleted: pages/5_Live_Recording.py")

# Also rename Who_Is_This to be page 3
old_who_is_this = Path("pages/4_Who_Is_This.py")
new_who_is_this = Path("pages/4_Who_Is_This.py")

if old_who_is_this.exists():
    print("✅ Who_Is_This page kept at position 4")
else:
    print("⚠️  Who_Is_This page not found")

print()
print("=" * 70)
print("CLEANUP COMPLETE!")
print("=" * 70)
print()
print("NEXT STEPS:")
print("1. Run: poetry run streamlit run app.py")
print("2. Test Patient View auto-refresh (wait 30 seconds)")
print("3. Check Admin page layout")
print("4. Test medication reminder")
print("5. Ready for demo!")
print()
print("=" * 70)