import os
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import mysql.connector

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings("ignore")

CURRENT_USER = None

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root123",
            database="inventorydb"
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Database Connection Error", f"Unable to reach MySQL database server:\n{err}")
        return None

def train_model():
    file_path = r"d:\OM PATIL\INT. PROJECT\PROJECT\Inventry.csv"
    if not os.path.exists(file_path):
        file_path = "Inventry.csv"

    try:
        df = pd.read_csv(file_path)
    except Exception:
        return None, {
            "Category": ["Electronics", "Clothing", "Grocery", "Home & Kitchen", "Beauty & Personal Care", "Sports"], 
            "Store Name": ["Store Alpha", "Store Beta", "Store Gamma"]
        }

    if "Store Name" not in df.columns and "Region" in df.columns:
        df["Store Name"] = df["Region"]

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "Store ID", "Product ID", "Category", "Store Name", "Inventory Level", "Units Sold", "Units Ordered", "Price"])

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day
    df["DayOfWeek"] = df["Date"].dt.dayofweek

    X = df[["Product ID", "Category", "Store Name", "Inventory Level", "Units Ordered", "Price", "Year", "Month", "Day", "DayOfWeek"]]
    y = df["Units Sold"]

    categorical_features = ["Product ID", "Category", "Store Name"]
    numerical_features = ["Inventory Level", "Units Ordered", "Price", "Year", "Month", "Day", "DayOfWeek"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("numerical", "passthrough", numerical_features)
        ]
    )

    model = Pipeline(steps=[("preprocessor", preprocessor), ("regressor", RandomForestRegressor(n_estimators=50, random_state=42))])
    model.fit(X, y)

    encoders = {
        "Category": sorted(df["Category"].astype(str).unique()),
        "Store Name": sorted(df["Store Name"].astype(str).unique()),
        "Product ID": sorted(df["Product ID"].astype(str).unique())
    }

    return model, encoders


class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Enterprise Inventory Demand Intelligence System")
        self.geometry("1240x860")
        self.configure(bg="#f8fafc")
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure("TCombobox", fieldbackground="#ffffff", background="#e2e8f0", borderwidth=1)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#0f172a", foreground="white")
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=30)
        self.style.map("Treeview", background=[("selected", "#2563eb")], foreground=[("selected", "white")])

        model_output = train_model()
        if isinstance(model_output, tuple) and len(model_output) == 2:
            self.model, self.encoders = model_output
        else:
            self.model, self.encoders = None, {
                "Category": ["Electronics", "Clothing", "Grocery", "Home & Kitchen", "Beauty & Personal Care", "Sports"], 
                "Store Name": ["Store Alpha", "Store Beta", "Store Gamma"]
            }

        self.show_login_frame()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def bind_mousewheel(self, widget, canvas):
        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        widget.bind_all("<MouseWheel>", _on_mousewheel)
        widget.bind_all("<Button-4>", _on_mousewheel)
        widget.bind_all("<Button-5>", _on_mousewheel)

    def unbind_mousewheel(self):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def show_login_frame(self):
        self.unbind_mousewheel()
        self.clear_screen()
        
        container = tk.Frame(self, bg="#0f172a")
        container.pack(fill="both", expand=True)

        card = tk.Frame(container, bg="white", bd=0, highlightbackground="#e2e8f0", highlightthickness=1, padx=60, pady=50)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="🛡️ INVENTORY DEMAND PORTAL", font=("Segoe UI", 22, "bold"), bg="white", fg="#0f172a").pack(pady=(0, 2))
        tk.Label(card, text="Inventory Analytics & Demand Prediction Suite", font=("Segoe UI", 9), bg="white", fg="#64748b").pack(pady=(0, 28))

        tk.Label(card, text="Username", font=("Segoe UI", 9, "bold"), bg="white", fg="#334155").pack(anchor="w")
        u_entry = tk.Entry(card, font=("Segoe UI", 11), width=34, bg="#f8fafc", relief="flat", highlightbackground="#cbd5e1", highlightthickness=1)
        u_entry.pack(pady=(4, 16), ipady=7)

        tk.Label(card, text="Password", font=("Segoe UI", 9, "bold"), bg="white", fg="#334155").pack(anchor="w")
        p_entry = tk.Entry(card, font=("Segoe UI", 11), show="*", width=34, bg="#f8fafc", relief="flat", highlightbackground="#cbd5e1", highlightthickness=1)
        p_entry.pack(pady=(4, 28), ipady=7)

        def attempt_login():
            global CURRENT_USER
            u, p = u_entry.get().strip(), p_entry.get().strip()
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE username=%s AND password=%s", (u, p))
                user = cursor.fetchone()
                conn.close()

                if user:
                    CURRENT_USER = user[0]
                    self.show_dashboard()
                else:
                    messagebox.showerror("Access Denied", "Invalid Credentials Provided.")

        tk.Button(card, text="LOGIN", bg="#2563eb", fg="white", activebackground="#1d4ed8", activeforeground="white",
                  font=("Segoe UI", 10, "bold"), width=36, bd=0, cursor="hand2", pady=10, command=attempt_login).pack(pady=5)
        
        tk.Button(card, text="Create NEW account", fg="#2563eb", bg="white", bd=0, 
                  font=("Segoe UI", 9, "underline"), cursor="hand2", command=self.show_register_frame).pack(pady=(18, 0))

    def show_register_frame(self):
        self.unbind_mousewheel()
        self.clear_screen()
        
        container = tk.Frame(self, bg="#0f172a")
        container.pack(fill="both", expand=True)

        card = tk.Frame(container, bg="white", bd=0, highlightbackground="#e2e8f0", highlightthickness=1, padx=60, pady=45)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="📝 Register Account", font=("Segoe UI", 20, "bold"), bg="white", fg="#0f172a").pack(pady=(0, 2))
        tk.Label(card, text="Provision administrative user credentials", font=("Segoe UI", 9), bg="white", fg="#64748b").pack(pady=(0, 24))

        tk.Label(card, text="Full Name", font=("Segoe UI", 9, "bold"), bg="white", fg="#334155").pack(anchor="w")
        fn_entry = tk.Entry(card, font=("Segoe UI", 10), width=36, bg="#f8fafc", relief="flat", highlightbackground="#cbd5e1", highlightthickness=1)
        fn_entry.pack(pady=(2, 12), ipady=6)

        tk.Label(card, text="Username", font=("Segoe UI", 9, "bold"), bg="white", fg="#334155").pack(anchor="w")
        un_entry = tk.Entry(card, font=("Segoe UI", 10), width=36, bg="#f8fafc", relief="flat", highlightbackground="#cbd5e1", highlightthickness=1)
        un_entry.pack(pady=(2, 12), ipady=6)

        tk.Label(card, text="Password", font=("Segoe UI", 9, "bold"), bg="white", fg="#334155").pack(anchor="w")
        pw_entry = tk.Entry(card, font=("Segoe UI", 10), show="*", width=36, bg="#f8fafc", relief="flat", highlightbackground="#cbd5e1", highlightthickness=1)
        pw_entry.pack(pady=(2, 22), ipady=6)

        def save_user():
            fn, un, pw = fn_entry.get().strip(), un_entry.get().strip(), pw_entry.get().strip()
            if not fn or not un or not pw:
                messagebox.showwarning("Incomplete Details", "All fields are required.")
                return
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, password, full_name) VALUES (%s, %s, %s)", (un, pw, fn))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Success", "Account provisioned successfully!")
                    self.show_login_frame()
                except mysql.connector.Error as err:
                    messagebox.showerror("Registration Error", f"Unable to register user:\n{err}")

        tk.Button(card, text="REGISTER ACCOUNT", bg="#10b981", fg="white", activebackground="#059669", activeforeground="white",
                  font=("Segoe UI", 10, "bold"), width=36, bd=0, cursor="hand2", pady=10, command=save_user).pack(pady=8)
        
        tk.Button(card, text="← Return to Portal Login", fg="#64748b", bg="white", bd=0, font=("Segoe UI", 9), cursor="hand2", command=self.show_login_frame).pack(pady=(10, 0))

    def show_dashboard(self):
        self.clear_screen()

        header = tk.Frame(self, bg="#0f172a", height=65)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        brand_box = tk.Frame(header, bg="#0f172a")
        brand_box.pack(side="left", padx=24)
        tk.Label(brand_box, text="⚡ INVENTORY DEMAND PREDICTION SYSTEM", font=("Segoe UI", 12, "bold"), fg="#38bdf8", bg="#0f172a").pack(side="left")

        right_header = tk.Frame(header, bg="#0f172a")
        right_header.pack(side="right", padx=20)

        tk.Button(right_header, text="Logout 🚪", font=("Segoe UI", 9, "bold"), bg="#ef4444", fg="white", activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=14, pady=6, command=self.show_login_frame).pack(side="right", padx=(10, 0))

        def show_user_info():
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT username, full_name FROM users WHERE username=%s", (CURRENT_USER,))
                    user_record = cursor.fetchone()
                    conn.close()
                    if user_record:
                        un, fn = user_record
                        messagebox.showinfo("User Profile Information", f"👤 Username: {un}\n📋 Full Name: {fn}\n🛡️ Role: System Operator")
                    else:
                        messagebox.showinfo("User Profile", f"Current User: {CURRENT_USER}")
                except Exception as e:
                    messagebox.showinfo("User Profile", f"Current User: {CURRENT_USER}\n(Details unavailable: {e})")

        user_badge = tk.Button(
            right_header, text=f"👤 {CURRENT_USER}", font=("Segoe UI", 9, "bold"), 
            fg="#f8fafc", bg="#1e293b", activebackground="#334155", activeforeground="#f8fafc", 
            relief="flat", bd=0, cursor="hand2", padx=10, pady=5, 
            highlightbackground="#334155", highlightthickness=1, command=show_user_info
        )
        user_badge.pack(side="right", padx=(10, 0))

        from predict import load_predict_page, load_analytics_page
        from history import load_history_page

        def open_homepage():
            self.load_homepage()

        def open_predict():
            load_predict_page(self.content_container, self.model, self.encoders, get_db_connection, CURRENT_USER)

        def open_analytics():
            load_analytics_page(self.content_container, CURRENT_USER)

        def open_history():
            load_history_page(self.content_container, get_db_connection)

        tk.Button(right_header, text="📜 HISTORY", font=("Segoe UI", 9, "bold"), bg="#10b981", fg="white", activebackground="#059669", activeforeground="white",
                  bd=0, cursor="hand2", padx=12, pady=6, command=open_history).pack(side="right", padx=4)

        tk.Button(right_header, text="📊 Analytics", font=("Segoe UI", 9, "bold"), bg="#7c3aed", fg="white", activebackground="#6d28d9", activeforeground="white",
                  bd=0, cursor="hand2", padx=12, pady=6, command=open_analytics).pack(side="right", padx=4)

        tk.Button(right_header, text="📈 Demand Predictor", font=("Segoe UI", 9, "bold"), bg="#2563eb", fg="white", activebackground="#1d4ed8", activeforeground="white",
                  bd=0, cursor="hand2", padx=12, pady=6, command=open_predict).pack(side="right", padx=4)

        tk.Button(right_header, text="🏠 HOME", font=("Segoe UI", 9, "bold"), bg="#334155", fg="white", activebackground="#1e293b", activeforeground="white",
                  bd=0, cursor="hand2", padx=12, pady=6, command=open_homepage).pack(side="right", padx=4)

        self.content_container = tk.Frame(self, bg="#f8fafc")
        self.content_container.pack(fill="both", expand=True, padx=22, pady=(15, 15), side="top", anchor="n")

        self.load_homepage()

    def load_homepage(self):
        self.unbind_mousewheel()
        for widget in self.content_container.winfo_children():
            widget.destroy()

        main_canvas = tk.Canvas(self.content_container, bg="#f8fafc", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg="#f8fafc")

        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        canvas_window = main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _configure_canvas(event):
            main_canvas.itemconfig(canvas_window, width=event.width)
        main_canvas.bind('<Configure>', _configure_canvas)

        main_canvas.configure(yscrollcommand=scrollbar.set)
        main_canvas.pack(side="left", fill="both", expand=True, anchor="n")
        scrollbar.pack(side="right", fill="y")

        main_canvas.yview_moveto(0)
        self.bind_mousewheel(main_canvas, main_canvas)

        banner = tk.Frame(scrollable_frame, bg="#0f172a", pady=28, padx=32)
        banner.pack(fill="x", pady=(0, 20), anchor="n")
        tk.Label(banner, text="Enterprise Demand Intelligence Platform", font=("Segoe UI", 18, "bold"), fg="#f8fafc", bg="#0f172a").pack(anchor="w")
        tk.Label(banner, text="Automated demand forecasting, advanced machine learning regressions, and persistent stock audit logging.", font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a").pack(anchor="w", pady=(4, 0))

        def create_card(parent, icon, title, text_items, accent_color):
            card = tk.Frame(parent, bg="white", highlightbackground="#e2e8f0", highlightthickness=1, padx=24, pady=20)
            card.pack(fill="x", pady=8, anchor="n")

            header_box = tk.Frame(card, bg="white")
            header_box.pack(fill="x", pady=(0, 10))

            tk.Label(header_box, text=icon, font=("Segoe UI", 14), bg="white").pack(side="left", padx=(0, 8))
            tk.Label(header_box, text=title, font=("Segoe UI", 11, "bold"), fg=accent_color, bg="white").pack(side="left")

            for bullet in text_items:
                tk.Label(card, text=bullet, font=("Segoe UI", 9), fg="#334155", bg="white", justify="left", anchor="w", wraplength=980).pack(anchor="w", pady=3)

        create_card(scrollable_frame, "📌", "System Architecture & Goals", [
            "• Mitigates stockouts and supply-chain bottlenecks using robust machine-learning demand prediction models.",
            "• Reduces working capital overstock using dynamic threshold warning triggers."
        ], "#2563eb")

        create_card(scrollable_frame, "⚙️", "Core Operations Workflow", [
            "1. Database Operations: Execute item creation, inventory parameter updates, and record removals safely.",
            "2. Pipeline Transformation: Processes dates into temporal metrics and applies OneHotEncoding to discrete categories.",
            "3. Stock Recommendations: Evaluates current inventory against predicted demand to recommend action.",
            "4. Audit Logging: Automatically records all inference queries and inventory updates into MySQL tables."
        ], "#d97706")

        create_card(scrollable_frame, "🛡️", "Key System Features & Security", [
            "• Role-Based Activity Tracking: Every prediction run, item addition, update, and deletion is securely logged with the operator's username.",
            "• Advanced Filtering & Export: Activity audit logs can be filtered by Action, Username, ID, or Date, and exported instantly to CSV format.",
            "• Real-Time Analytics: Instant data visualizations comparing inventory levels, units ordered, and predicted demand."
        ], "#059669")

if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()