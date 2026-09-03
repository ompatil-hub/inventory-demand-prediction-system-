The **Inventory Demand Prediction System** is a desktop application built using Python, Tkinter, MySQL, and Machine Learning that forecasts future product demand based on historical inventory and sales records.

### **The Problem It Solves**

Retail stores and supply chain businesses frequently struggle with two major inventory issues:

* **Overstocking:** Ties up company capital and leads to product wastage or high holding costs.


* **Understocking:** Results in product shortages, missed sales, and dissatisfied customers.


* Traditional estimation relies on manual calculations or simple lookups of past sales, which are often inaccurate and fail to capture shifting market demands. This system automates forecasting to optimize inventory levels and minimize human error.



### **Core Features**

* **Secure User Authentication:** Admin login and user registration backed by a MySQL database (`admin_users` table).


* **Interactive Dashboard:** High-level summary view providing quick navigation, metric cards, and system status insights.


* **Data Management (CRUD):** Allows administrators to add, view, update, and delete product catalog entries and inventory levels directly in the database.


* **Machine Learning Demand Forecasting:** Utilizes a Scikit-Learn regression pipeline (Multiple Linear Regression) and One-Hot Encoding to process historical attributes, extract temporal features, and predict future product units needed.


* **Automated Stock Status Evaluation:** Compares current stock against the model's demand output to instantly trigger visual alerts such as **Reorder Needed**, **Overstock Alert**, or **Optimal Level**.


* **Data Visualization:** Generates integrated Matplotlib charts comparing current inventory, ordered stock, and predicted demand.


* **Audit Logs & History:** Automatically logs all transactions, user actions, and predictions into a persistent history table with filtering and export capabilities.
