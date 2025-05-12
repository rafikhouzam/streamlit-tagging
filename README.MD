# 🏷️ Streamlit Image Tagging UI

A fast, production-ready Streamlit app for tagging jewelry product images stored on Amazon S3. Built to streamline metadata entry for internal cataloging, merchandising, and e-commerce prep.

---

## 🔧 Features

- Randomized image presentation (locked per session)
- Tagging UI with dropdowns for:
  - Style Category
  - Ring Type
  - Chain Type
  - Metal Color
  - Gender
  - Is Set
- Progress tracking and autosave
- "Fetch New Image" to skip without tagging
- Persists tags to `tagged_data.csv`
- Loads images via public S3 URLs (no local storage needed)

---
