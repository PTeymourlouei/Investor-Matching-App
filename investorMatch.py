import tkinter as tk
from tkinter import ttk, messagebox
import cohere
import pandas as pd
import os
import sys

# --- Setup Cohere client ---
co = cohere.Client("kjnSJq8XtaMWXRTwadzTZAejPt3f8BBqPHszeTWk")  # Replace with your API key

# --- Load CSV (bundled inside app) ---
def get_csv_path(filename):
    if getattr(sys, 'frozen', False):
        # If the app is bundled by PyInstaller
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

csv_path = get_csv_path("investors.csv")

try:
    df = pd.read_csv(csv_path)
except FileNotFoundError:
    messagebox.showerror("Error", f"Could not find investors.csv at {csv_path}")
    sys.exit(1)
df.columns = df.columns.str.strip()
df.fillna("Unknown", inplace=True)  # Handle missing data

# --- Get dropdown options from CSV ---
def get_unique_options(column):
    options = set()
    for items in df[column].dropna():
        for item in items.split(','):
            options.add(item.strip())
    return sorted(options)

stage_options = get_unique_options('Stages of Investing')
market_options = get_unique_options('Market')
geo_options = get_unique_options('Geo')

# --- Main window ---
root = tk.Tk()
root.title("Startup Investor Matcher")

# --- Helper for labeled multi-select listboxes ---
def create_multiselect_listbox(parent, options, row, col):
    label = tk.Label(parent, text=f"Select Startup {options['label']}:")
    label.grid(row=row, column=col*2, sticky="nw", padx=5, pady=5)
    listbox = tk.Listbox(parent, selectmode='multiple', height=6, exportselection=False)
    for option in options['values']:
        listbox.insert(tk.END, option)
    listbox.grid(row=row, column=col*2+1, sticky="w", padx=5, pady=5)
    return listbox

# --- Input widgets ---
stage_listbox = create_multiselect_listbox(root, {'label': 'Stage(s)', 'values': stage_options}, 0, 0)
market_listbox = create_multiselect_listbox(root, {'label': 'Market(s)', 'values': market_options}, 1, 0)
geo_listbox = create_multiselect_listbox(root, {'label': 'Geography(ies)', 'values': geo_options}, 2, 0)

tk.Label(root, text="Select number of top investors to show:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
top_n_var = tk.StringVar(value="10")
top_n_combo = ttk.Combobox(root, textvariable=top_n_var, values=["5", "10", "15", "20"], state="readonly", width=5)
top_n_combo.grid(row=3, column=1, sticky="w", padx=5, pady=5)

result_text = tk.Text(root, height=20, width=100)
result_text.grid(row=4, column=0, columnspan=4, padx=10, pady=10)

# --- Store descriptions globally for debug viewer ---
global_descriptions = []  # Will hold tuples (investor_name, description)

def get_selected_items(listbox):
    selected_indices = listbox.curselection()
    return [listbox.get(i) for i in selected_indices]

# --- Search and rerank investors ---
def search_investors():
    global global_descriptions
    result_text.delete("1.0", tk.END)
    global_descriptions = []  # Reset global list

    selected_stages = get_selected_items(stage_listbox)
    selected_markets = get_selected_items(market_listbox)
    selected_geos = get_selected_items(geo_listbox)

    try:
        top_n = int(top_n_var.get())
    except ValueError:
        messagebox.showerror("Input Error", "Please select a valid number of top investors.")
        return

    def match_any(cell, keywords):
        if not keywords:
            return True
        cell_lower = str(cell).lower()
        return any(kw.lower() in cell_lower for kw in keywords)

    filtered_df = df[
        df["Stages of Investing"].apply(lambda x: match_any(x, selected_stages)) &
        df["Market"].apply(lambda x: match_any(x, selected_markets)) &
        df["Geo"].apply(lambda x: match_any(x, selected_geos))
    ]

    if filtered_df.empty:
        messagebox.showinfo("No Matches", "No investors matched your criteria. Try broader filters.")
        return

    startup_description = "A startup"
    if selected_stages:
        startup_description += f" at stage(s) {', '.join(selected_stages)}"
    if selected_markets:
        startup_description += f" in the market(s) {', '.join(selected_markets)}"
    if selected_geos:
        startup_description += f" based in {', '.join(selected_geos)}"
    startup_description += "."

    investor_descriptions = []
    investor_names = []
    investor_urls = []

    for _, row in filtered_df.iterrows():
        desc = f"Invests in {row['Stages of Investing']} stage {row['Market']} startups in {row['Geo']}."
        investor_descriptions.append(desc)
        investor_names.append(row['Entity'])
        investor_urls.append(row.get('URL', 'No URL'))

    global_descriptions = list(zip(investor_names, investor_descriptions))  # Save names + descriptions

    try:
        response = co.rerank(
            query=startup_description,
            documents=investor_descriptions,
            top_n=min(top_n, len(investor_descriptions))
        )
    except Exception as e:
        messagebox.showerror("API Error", f"Error calling Cohere API:\n{e}")
        return

    result_text.insert(tk.END, f"Top {len(response.results)} Matching Investors:\n")
    result_text.insert(tk.END, "Scores range from 0 to 1 (higher = better match).\n\n")

    for i, result in enumerate(response.results, start=1):
        idx = result.index
        url = investor_urls[idx] if pd.notna(investor_urls[idx]) else "No URL"
        result_text.insert(tk.END,
            f"{i}. {investor_names[idx]} — Score: {result.relevance_score:.2f}\n{url}\n\n"
        )

# --- Show raw investor descriptions used in ranking ---
def show_descriptions():
    if not global_descriptions:
        messagebox.showinfo("No Data", "Please run a search first.")
        return

    desc_win = tk.Toplevel(root)
    desc_win.title("Investor Descriptions Sent to Cohere")

    text_widget = tk.Text(desc_win, width=100, height=30)
    text_widget.pack(padx=10, pady=10)

    for i, (name, desc) in enumerate(global_descriptions, 1):
        text_widget.insert(tk.END, f"{i}. {name}:\n{desc}\n\n")

# --- Buttons ---
search_btn = tk.Button(root, text="Find Investors", command=search_investors)
search_btn.grid(row=3, column=2, padx=10, pady=10)

show_desc_btn = tk.Button(root, text="Show Descriptions Sent to AI", command=show_descriptions)
show_desc_btn.grid(row=3, column=3, padx=10, pady=10)

# --- Run app ---
root.mainloop()
