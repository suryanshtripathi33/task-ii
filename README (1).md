# Intelligent File Organizer
**Kinetrexa Software Private Limited — Python Development Internship**

### Intern Information
* **Name:** Pratyush
* **Application ID:** 8GNC9PDMA
* **Task:** #3 Automation Script (File Handling)

---

## Project Description
The **Intelligent File Organizer** is a robust automation utility designed to eliminate manual file management. It intelligently scans a target directory and categorizes files into specific sub-folders based on their extensions (e.g., Documents, Images, Code, Media).

This script is built with a **Safety-First** mindset, including collision resolution (to prevent overwriting files with the same name) and a script-protection check to ensure it never moves itself.

## Key Features
* **Automated Categorization:** Handles 50+ file extensions across 10+ categories.
* **Audit Trail:** Generates a timestamped log in `.organizer_logs/organizer.log`.
* **Name Collision Resolution:** Automatically renames duplicates (e.g., `data.pdf` becomes `data_1.pdf`).
* **Dry Run Mode:** Preview the organization process without moving any files.
* **Error Handling:** Robust protection against Permission Denied and OS-level errors.

## How to Run

### 1. Prerequisites
Ensure you have **Python 3.8 or higher** installed on your system.

### 2. Standard Execution
Organize the current directory where the script is located:
```bash
python AutomationScript.py
