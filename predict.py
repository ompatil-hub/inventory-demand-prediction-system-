import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Global store for the latest prediction state across pages
latest_prediction = {"demand": None, "inventory": None, "ordered": None, "product_id": None}

def load_predict_page(parent_frame, model, encoders, db_connection_func, current_username, *args, **kwargs):
    for widget in parent_frame.winfo_children():
        widget.destroy()

    parent_frame.option_add('*TCombobox*Listbox.background', '#ffffff')
    parent_frame.option_add('*TCombobox*Listbox.selectBackground', '#2563eb')
    parent_frame.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')

    container = tk.Frame(parent_frame, bg="#f8fafc")
    container.pack(fill="both", expand=True, padx=20, pady=15)

    left_frame = tk.LabelFrame(
        container, text=" Parameters & Stock Management ", 
        font=("Segoe UI", 11, "bold"), fg="#1e293b", bg="white", 
        highlightbackground="#cbd5e1", highlightthickness=1, padx=24, pady=20
    )
    left_frame.pack(fill="both", expand=True)

    form_grid = tk.Frame(left_frame, bg="white")
    form_grid.pack(fill="x", pady=(0, 16))

    fields = [
        ("Date (YYYY-MM-DD):", 0, 0),
        ("Store Name:", 0, 1),
        ("Product ID:", 1, 0),
        ("Category:", 1, 1),
        ("Inventory Level:", 2, 0),
        ("Units Ordered:", 2, 1),
        ("Price:", 3, 0)
    ]

    entries = {}
    for label_text, r, c in fields:
        sub_box = tk.Frame(form_grid, bg="white")
        sub_box.grid(row=r, column=c, padx=10, pady=8, sticky="ew")
        form_grid.columnconfigure(c, weight=1)

        tk.Label(sub_box, text=label_text, font=("Segoe UI", 9, "bold"), fg="#475569", bg="white").pack(anchor="w", pady=(0, 4))

        if "Category" in label_text:
            cat_options = ["Electronics", "Clothing", "Grocery", "Home & Kitchen", "Beauty & Personal Care", "Sports"]
            if encoders and 'Category' in encoders:
                cat_enc_obj = encoders['Category']
                if hasattr(cat_enc_obj, 'classes_'): cat_options = list(cat_enc_obj.classes_)
                elif isinstance(cat_enc_obj, (list, tuple)): cat_options = list(cat_enc_obj)
            
            entry = ttk.Combobox(sub_box, values=cat_options, state="readonly", font=("Segoe UI", 10))
            if cat_options: entry.set(cat_options[0])
        elif "Store Name" in label_text:
            entry = tk.Entry(sub_box, font=("Segoe UI", 10), highlightbackground="#cbd5e1", highlightthickness=1, bd=0)
        else:
            entry = tk.Entry(sub_box, font=("Segoe UI", 10), highlightbackground="#cbd5e1", highlightthickness=1, bd=0)
            if "Date" in label_text:
                entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        entry.pack(fill="x", ipady=5)
        entries[label_text] = entry

    def log_history_event(action_type, product_id, summary, predicted_demand=None, recommendation=None):
        date_str = entries["Date (YYYY-MM-DD):"].get().strip()
        conn = db_connection_func()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO history (username, action_type, product_id, input_summary, predicted_demand, recommendation, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (current_username, action_type, str(product_id), summary, predicted_demand, recommendation, date_str))
                conn.commit()
                conn.close()
            except Exception:
                pass

    def run_prediction():
        try:
            date_str = entries["Date (YYYY-MM-DD):"].get().strip()
            store_name = entries["Store Name:"].get().strip()
            product_id = entries["Product ID:"].get().strip()
            category = entries["Category:"].get()
            inv_level = float(entries["Inventory Level:"].get().strip())
            units_ordered = float(entries["Units Ordered:"].get().strip())
            price = float(entries["Price:"].get().strip())

            if not store_name or not product_id:
                messagebox.showwarning("Input Error", "Please fill in all mandatory fields.")
                return

            dt = datetime.strptime(date_str, "%Y-%m-%d")
            year, month, day, day_of_week = dt.year, dt.month, dt.day, dt.weekday()

            cat_enc = 0
            if encoders and 'Category' in encoders:
                encoder_obj = encoders['Category']
                if hasattr(encoder_obj, 'transform'):
                    try: cat_enc = encoder_obj.transform([category])[0]
                    except Exception: pass
                elif isinstance(encoder_obj, (list, tuple)) and category in encoder_obj:
                    cat_enc = encoder_obj.index(category)

            store_name_enc = 0
            if encoders and 'Store Name' in encoders:
                encoder_obj = encoders['Store Name']
                if hasattr(encoder_obj, 'transform'):
                    try: store_name_enc = encoder_obj.transform([store_name])[0]
                    except Exception: pass
                elif isinstance(encoder_obj, (list, tuple)) and store_name in encoder_obj:
                    store_name_enc = encoder_obj.index(store_name)

            prod_enc = 0
            if encoders and 'Product ID' in encoders:
                encoder_obj = encoders['Product ID']
                if hasattr(encoder_obj, 'transform') and hasattr(encoder_obj, 'classes_'):
                    if product_id in encoder_obj.classes_: prod_enc = encoder_obj.transform([product_id])[0]
                elif isinstance(encoder_obj, (list, tuple)) and product_id in encoder_obj:
                    prod_enc = encoder_obj.index(product_id)

            features = np.array([[prod_enc, cat_enc, store_name_enc, inv_level, units_ordered, price, year, month, day, day_of_week]])
            pred_val = float(model.predict(features)[0]) if model else (inv_level * 0.85 + units_ordered * 0.15)
            pred_val = max(0.0, pred_val)

            global latest_prediction
            latest_prediction["demand"] = pred_val
            latest_prediction["inventory"] = inv_level
            latest_prediction["ordered"] = units_ordered
            latest_prediction["product_id"] = product_id

            if inv_level < pred_val:
                rec_text = f"⚠️ Low Stock Alert: Current stock ({inv_level:.0f}) is below target demand ({pred_val:.2f}). Reorder recommended."
            elif inv_level > pred_val * 1.5:
                rec_text = f"📦 Overstock Warning: Current stock ({inv_level:.0f}) significantly exceeds target demand ({pred_val:.2f})."
            else:
                rec_text = f"✅ Optimal Stock: Current stock ({inv_level:.0f}) satisfies predicted demand ({pred_val:.2f})."

            conn = db_connection_func()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO products (product_id, category, price) 
                        VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE category=%s, price=%s
                    """, (product_id, category, price, category, price))
                    cursor.execute("INSERT INTO predictions (product_id, prediction_date, predicted_demand) VALUES (%s, %s, %s)",
                                   (product_id, date_str, pred_val))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass

            summary_str = f"Store Name: {store_name}, Stock: {inv_level:.0f}, Ordered: {units_ordered:.0f}, Price: ${price:.2f}"
            log_history_event("Prediction Run", product_id, summary_str, pred_val, rec_text)
            messagebox.showinfo("Success", f"Demand predicted successfully: {pred_val:.2f} Units!\nCheck Analytics page for reports.")

        except ValueError as ve:
            messagebox.showerror("Validation Error", f"Please check numerical fields and date format (YYYY-MM-DD):\n{ve}")
        except Exception as e:
            messagebox.showerror("Prediction Error", str(e))

    tk.Button(
        left_frame, text="⚡ RUN DEMAND PREDICTION", bg="#2563eb", fg="white", 
        font=("Segoe UI", 10, "bold"), bd=0, cursor="hand2", pady=11, command=run_prediction
    ).pack(fill="x", pady=(10, 14))

    crud_box = tk.Frame(left_frame, bg="white")
    crud_box.pack(fill="x")

    def add_item():
        p_id, s_name = entries["Product ID:"].get().strip(), entries["Store Name:"].get().strip()
        if not p_id or not s_name:
            messagebox.showwarning("Input Error", "Please fill Product ID and Store Name.")
            return
        conn = db_connection_func()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO inventory (product_id, store_id, record_date, store_name, inventory_level, units_ordered)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE inventory_level=%s, units_ordered=%s
                """, (p_id, s_name, entries["Date (YYYY-MM-DD):"].get().strip(), s_name,
                      entries["Inventory Level:"].get().strip() or 0, entries["Units Ordered:"].get().strip() or 0,
                      entries["Inventory Level:"].get().strip() or 0, entries["Units Ordered:"].get().strip() or 0))
                conn.commit()
                conn.close()
                log_history_event("Add Item", p_id, f"Added stock for Store {s_name}")
                messagebox.showinfo("Success", f"Product '{p_id}' added/updated in database.")
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

    def update_item():
        p_id, s_name = entries["Product ID:"].get().strip(), entries["Store Name:"].get().strip()
        if not p_id or not s_name:
            messagebox.showwarning("Input Error", "Please specify Product ID and Store Name to update.")
            return
        conn = db_connection_func()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE inventory SET inventory_level = %s, units_ordered = %s, record_date = %s
                    WHERE product_id = %s AND store_name = %s
                """, (entries["Inventory Level:"].get().strip() or 0, entries["Units Ordered:"].get().strip() or 0,
                      entries["Date (YYYY-MM-DD):"].get().strip(), p_id, s_name))
                conn.commit()
                conn.close()
                log_history_event("Update Item", p_id, f"Updated stock for Store {s_name}")
                messagebox.showinfo("Success", f"Record for '{p_id}' updated.")
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

    def delete_item():
        p_id, s_name = entries["Product ID:"].get().strip(), entries["Store Name:"].get().strip()
        if not p_id or not s_name:
            messagebox.showwarning("Input Error", "Please specify Product ID and Store Name to delete.")
            return
        if messagebox.askyesno("Confirm Delete", f"Remove item '{p_id}' at store '{s_name}'?"):
            conn = db_connection_func()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM inventory WHERE product_id = %s AND store_name = %s", (p_id, s_name))
                    conn.commit()
                    conn.close()
                    log_history_event("Delete Item", p_id, f"Deleted item from Store {s_name}")
                    messagebox.showinfo("Success", f"Item '{p_id}' removed.")
                except Exception as e:
                    messagebox.showerror("Database Error", str(e))

    tk.Button(crud_box, text="Add Item", bg="#10b981", fg="white", font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2", pady=8, command=add_item).pack(side="left", fill="x", expand=True, padx=(0, 6))
    tk.Button(crud_box, text="Update", bg="#d97706", fg="white", font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2", pady=8, command=update_item).pack(side="left", fill="x", expand=True, padx=3)
    tk.Button(crud_box, text="Delete", bg="#ef4444", fg="white", font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2", pady=8, command=delete_item).pack(side="left", fill="x", expand=True, padx=(6, 0))


def load_analytics_page(parent_frame, current_username, *args, **kwargs):
    def refresh_page():
        load_analytics_page(parent_frame, current_username, *args, **kwargs)

    for widget in parent_frame.winfo_children():
        widget.destroy()

    container = tk.Frame(parent_frame, bg="#f8fafc")
    container.pack(fill="both", expand=True, padx=20, pady=15)

    right_frame = tk.LabelFrame(
        container, text=" Predictive Analytics & Reports ", 
        font=("Segoe UI", 11, "bold"), fg="#1e293b", bg="white", 
        highlightbackground="#cbd5e1", highlightthickness=1, padx=24, pady=20
    )
    right_frame.pack(fill="both", expand=True)

    top_bar = tk.Frame(right_frame, bg="white")
    top_bar.pack(fill="x", pady=(0, 10))

    tk.Button(
        top_bar, text="🔄 Refresh Data", bg="#0ea5e9", fg="white", 
        font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2", padx=12, pady=6, command=refresh_page
    ).pack(side="right")

    card_top = tk.Frame(right_frame, bg="#f0f9ff", highlightbackground="#bae6fd", highlightthickness=1, padx=16, pady=14)
    card_top.pack(fill="x", pady=(0, 14))

    tk.Label(card_top, text="PROJECTED DEMAND FORECAST", font=("Segoe UI", 9, "bold"), fg="#0284c7", bg="#f0f9ff").pack(anchor="w")
    
    demand_val = f"{latest_prediction['demand']:.2f} Units" if latest_prediction["demand"] is not None else "-- Units"
    forecast_label = tk.Label(card_top, text=demand_val, font=("Segoe UI", 24, "bold"), fg="#0369a1", bg="#f0f9ff")
    forecast_label.pack(anchor="w", pady=(6, 0))

    rec_box = tk.Frame(right_frame, bg="#f8fafc", highlightbackground="#e2e8f0", highlightthickness=1, padx=16, pady=14)
    rec_box.pack(fill="x", pady=(0, 16))

    tk.Label(rec_box, text="ACTIONABLE RECOMMENDATION", font=("Segoe UI", 9, "bold"), fg="#475569", bg=rec_box["bg"]).pack(anchor="w")
    
    if latest_prediction["demand"] is not None:
        inv = latest_prediction["inventory"]
        dem = latest_prediction["demand"]
        if inv < dem:
            rec_text = f"⚠️ Low Stock Alert: Current stock ({inv:.0f}) is below target demand ({dem:.2f}). Reorder recommended."
        elif inv > dem * 1.5:
            rec_text = f"📦 Overstock Warning: Current stock ({inv:.0f}) significantly exceeds target demand ({dem:.2f})."
        else:
            rec_text = f"✅ Optimal Stock: Current stock ({inv:.0f}) satisfies predicted demand ({dem:.2f})."
    else:
        rec_text = "Run demand prediction on the Predictor page to evaluate stock parameters..."

    rec_label = tk.Label(rec_box, text=rec_text, font=("Segoe UI", 10), fg="#334155", bg=rec_box["bg"], justify="left")
    rec_label.pack(anchor="w", pady=(6, 0))

    def plot_analytics():
        if latest_prediction["demand"] is None:
            messagebox.showwarning("No Data", "Please run a demand prediction first on the Predictor page.")
            return

        fig, ax = plt.subplots(figsize=(7, 4.5))
        categories = ['Current Inventory', 'Units Ordered', 'Predicted Demand']
        values = [latest_prediction["inventory"], latest_prediction["ordered"], latest_prediction["demand"]]
        colors = ['#64748b', '#0284c7', '#2563eb']

        bars = ax.bar(categories, values, color=colors, width=0.5)
        ax.set_ylabel('Quantity Units', fontsize=10, fontweight='bold')
        ax.set_title(f'Inventory Metrics Comparison (Product #{latest_prediction["product_id"]})', fontsize=11, fontweight='bold')
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, yval + (max(values)*0.02), f'{yval:.1f}', ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        plt.show()

    def download_report():
        if latest_prediction["demand"] is None:
            messagebox.showwarning("No Data", "Run a demand prediction first on the Predictor page.")
            return
        
        report_content = f"""==================================================
ENTERPRISE INVENTORY DEMAND REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Logged User: {current_username}
==================================================

Product ID: {latest_prediction['product_id']}
Current Stock Level: {latest_prediction['inventory']:.0f} Units
Units On Order: {latest_prediction['ordered']:.0f} Units
--------------------------------------------------
PREDICTED DEMAND FORECAST: {latest_prediction['demand']:.2f} Units
STATUS: {'REORDER NEEDED' if latest_prediction['inventory'] < latest_prediction['demand'] else 'OPTIMAL STOCK'}
==================================================
"""
        try:
            default_name = f"Restock_Report_Product_{latest_prediction['product_id']}.txt"
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=default_name, title="Save Restock Report", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
            if file_path:
                with open(file_path, "w") as f:
                    f.write(report_content)
                messagebox.showinfo("Report Saved", f"Restock report saved successfully at:\n{file_path}")
        except Exception as e:
            messagebox.showerror("File Error", str(e))

    tk.Button(
        right_frame, text="📊 View Analytics Chart", bg="#7c3aed", fg="white", 
        font=("Segoe UI", 10, "bold"), bd=0, cursor="hand2", pady=10, command=plot_analytics
    ).pack(fill="x", pady=(0, 10))

    tk.Button(
        right_frame, text="📄 Download Restock Report", bg="#059669", fg="white", 
        font=("Segoe UI", 10, "bold"), bd=0, cursor="hand2", pady=10, command=download_report
    ).pack(fill="x")