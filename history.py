import tkinter as tk
from tkinter import ttk, messagebox
import csv
from tkinter import filedialog

def load_history_page(parent_container, get_db_connection):
    for widget in parent_container.winfo_children():
        widget.destroy()

    top_frame = tk.Frame(parent_container, bg="#f8fafc")
    top_frame.pack(fill="x", pady=(0, 10))

    tk.Label(top_frame, text="System Activity Audit Logs", font=("Segoe UI", 16, "bold"), bg="#f8fafc", fg="#0f172a").pack(anchor="w")
    tk.Label(top_frame, text="Track, filter, and export administrative operations and system inferences.", font=("Segoe UI", 9), bg="#f8fafc", fg="#64748b").pack(anchor="w")

    # Filters frame
    filter_frame = tk.Frame(parent_container, bg="#f8fafc")
    filter_frame.pack(fill="x", pady=10)

    # Fetch distinct values for filters from DB
    actions_list = ["All Actions"]
    users_list = ["All Users"]
    ids_list = ["All IDs"]
    dates_list = ["All Dates"]

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT action_type FROM history WHERE action_type IS NOT NULL")
            actions_list += [row[0] for row in cursor.fetchall() if row[0]]

            cursor.execute("SELECT DISTINCT COALESCE(username, user) FROM history WHERE COALESCE(username, user) IS NOT NULL")
            users_list += [str(row[0]) for row in cursor.fetchall() if row[0]]

            cursor.execute("SELECT DISTINCT COALESCE(history_id, id) FROM history WHERE COALESCE(history_id, id) IS NOT NULL")
            ids_list += [str(row[0]) for row in cursor.fetchall() if row[0]]

            cursor.execute("SELECT DISTINCT DATE(COALESCE(timestamp, created_at)) FROM history WHERE COALESCE(timestamp, created_at) IS NOT NULL")
            dates_list += [str(row[0]) for row in cursor.fetchall() if row[0]]
            conn.close()
        except Exception:
            pass

    # Action Filter
    tk.Label(filter_frame, text="Action:", font=("Segoe UI", 9, "bold"), bg="#f8fafc", fg="#334155").pack(side="left", padx=(0, 4))
    action_cb = ttk.Combobox(filter_frame, values=actions_list, width=14, state="readonly")
    action_cb.set("All Actions")
    action_cb.pack(side="left", padx=(0, 10))

    # User Filter
    tk.Label(filter_frame, text="User:", font=("Segoe UI", 9, "bold"), bg="#f8fafc", fg="#334155").pack(side="left", padx=(0, 4))
    user_cb = ttk.Combobox(filter_frame, values=users_list, width=12, state="readonly")
    user_cb.set("All Users")
    user_cb.pack(side="left", padx=(0, 10))

    # ID Filter
    tk.Label(filter_frame, text="ID:", font=("Segoe UI", 9, "bold"), bg="#f8fafc", fg="#334155").pack(side="left", padx=(0, 4))
    id_cb = ttk.Combobox(filter_frame, values=ids_list, width=8, state="readonly")
    id_cb.set("All IDs")
    id_cb.pack(side="left", padx=(0, 10))

    # Date Filter
    tk.Label(filter_frame, text="Date:", font=("Segoe UI", 9, "bold"), bg="#f8fafc", fg="#334155").pack(side="left", padx=(0, 4))
    date_cb = ttk.Combobox(filter_frame, values=dates_list, width=12, state="readonly")
    date_cb.set("All Dates")
    date_cb.pack(side="left", padx=(0, 15))

    def apply_filter():
        fetch_logs()

    tk.Button(filter_frame, text="Apply Filter", bg="#2563eb", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=12, pady=4, command=apply_filter).pack(side="left", padx=5)

    def export_csv():
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "User", "Action", "Product ID", "Summary", "Demand", "Date"])
                    for row_id in tree.get_children():
                        writer.writerow(tree.item(row_id)["values"])
                messagebox.showinfo("Success", "Audit logs exported successfully!")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export CSV:\n{e}")

    tk.Button(filter_frame, text="Export CSV", bg="#10b981", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=12, pady=4, command=export_csv).pack(side="right")

    table_frame = tk.Frame(parent_container, bg="white", highlightbackground="#e2e8f0", highlightthickness=1)
    table_frame.pack(fill="both", expand=True, pady=10)

    columns = ("id", "user", "action", "product_id", "summary", "demand", "created_at")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
    
    tree.heading("id", text="ID")
    tree.heading("user", text="User")
    tree.heading("action", text="Action")
    tree.heading("product_id", text="Product ID")
    tree.heading("summary", text="Summary")
    tree.heading("demand", text="Demand")
    tree.heading("created_at", text="Date")

    tree.column("id", width=50, anchor="center")
    tree.column("user", width=120, anchor="w")
    tree.column("action", width=140, anchor="w")
    tree.column("product_id", width=100, anchor="center")
    tree.column("summary", width=350, anchor="w")
    tree.column("demand", width=90, anchor="center")
    tree.column("created_at", width=150, anchor="center")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def fetch_logs():
        for row in tree.get_children():
            tree.delete(row)
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                
                query = """
                    SELECT 
                        COALESCE(history_id, id) AS id_val,
                        COALESCE(username, user, '-') AS user_val,
                        COALESCE(action_type, '-') AS action_val,
                        COALESCE(product_id, '-') AS prod_val,
                        COALESCE(input_summary, '-') AS sum_val,
                        COALESCE(predicted_demand, '-') AS dem_val,
                        COALESCE(timestamp, created_at, NOW()) AS date_val
                    FROM history
                    WHERE 1=1
                """
                params = []

                selected_action = action_cb.get()
                if selected_action != "All Actions":
                    query += " AND action_type = %s"
                    params.append(selected_action)

                selected_user = user_cb.get()
                if selected_user != "All Users":
                    query += " AND (username = %s OR user = %s)"
                    params.extend([selected_user, selected_user])

                selected_id = id_cb.get()
                if selected_id != "All IDs":
                    query += " AND (history_id = %s OR id = %s)"
                    params.extend([selected_id, selected_id])

                selected_date = date_cb.get()
                if selected_date != "All Dates":
                    query += " AND DATE(COALESCE(timestamp, created_at)) = %s"
                    params.append(selected_date)

                query += " ORDER BY COALESCE(timestamp, created_at) DESC"

                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()
                
                for r in rows:
                    row_values = (
                        r.get("id_val", "-"),
                        r.get("user_val", "-"),
                        r.get("action_val", "-"),
                        r.get("prod_val", "-"),
                        r.get("sum_val", "-"),
                        r.get("dem_val", "-"),
                        r.get("date_val", "-")
                    )
                    tree.insert("", "end", values=row_values)
                conn.close()
            except Exception as err:
                messagebox.showerror("Database Error", f"Could not load audit logs:\n{err}")

    fetch_logs()