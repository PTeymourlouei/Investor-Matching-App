# Investor-Matching-App
InvestorMatch is a Python-based desktop GUI application that helps startups identify the top 10 investors most aligned with their business profile. Using an intelligent AI ranking system powered by Cohere, the app filters and ranks investors based on industry, stage, geography, and a brief startup description.

---

## Features

- Input startup details directly through the GUI
- Filters for industry, investment stage, and location
- AI-powered matching using Cohere embeddings
- View raw investor descriptions for transparency
- No internet required after setup (except Cohere API use)

---

## Requirements

- Python 3.8 or higher
- Dependencies:
  - `pandas`
  - `tkinter` (included with Python)
  - `cohere`
  - `openpyxl` (if using Excel files)

Install dependencies with:

```bash
pip install pandas cohere openpyxl
