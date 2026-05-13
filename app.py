
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

import streamlit as st
from typing import Optional

from data_layer import DataLayer
from models import (
    User, Product, Sale, Flag,
    InventoryManager, SalesManager, FlagManager, UserManager
)
from service_layer import (
    AuthenticationService, InventoryService,
    SalesService, FlagService
)
from ai_assistant import AIAssistant


st.set_page_config(
    page_title="Small Business Inventory Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    
    .app-header {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .app-header h1 {
        margin: 0;
        color: white;
    }
    
    .app-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .role-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .role-owner {
        background-color: #10b981;
        color: yellow;
    }
    
    .role-employee {
        background-color: #3b82f6;
        color: yellow;
    }
    
    .test-accounts {
        background-color: #f0f9ff;
        border-left: 4px solid #0284c7;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .test-accounts {
        color: #0c4a6e;
    }

    .test-accounts h4 {
        margin-top: 0;
        color: #0c4a6e;
    }
    
    .account-row {
        background: white;
        color: #0c4a6e;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize all session state variables."""
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("current_user", None)
    st.session_state.setdefault("current_page", "dashboard")
    if "data_layer" not in st.session_state:
        st.session_state["data_layer"] = DataLayer()
    
    if "user_manager" not in st.session_state:
        data_layer = st.session_state["data_layer"]
        ok, users, _ = data_layer.load_users()
        st.session_state["user_manager"] = UserManager(users if ok else [])
    
    if "inventory_manager" not in st.session_state:
        data_layer = st.session_state["data_layer"]
        ok, products, _ = data_layer.load_products()
        st.session_state["inventory_manager"] = InventoryManager(products if ok else [])
    
    if "sales_manager" not in st.session_state:
        data_layer = st.session_state["data_layer"]
        ok, sales, _ = data_layer.load_sales()
        st.session_state["sales_manager"] = SalesManager(sales if ok else [])
    
    if "flag_manager" not in st.session_state:
        data_layer = st.session_state["data_layer"]
        ok, flags, _ = data_layer.load_flags()
        st.session_state["flag_manager"] = FlagManager(flags if ok else [])
    if "ai_assistant" not in st.session_state:
        st.session_state["ai_assistant"] = AIAssistant(
            st.session_state["inventory_manager"],
            st.session_state["sales_manager"],
            st.session_state["flag_manager"],
            use_openai=True
        )
    st.session_state.setdefault("chat_history", [
        {
            "role": "assistant",
            "content": st.session_state["ai_assistant"].get_welcome_message()
        }
    ])

def save_all_data():
    """Save all managers' data to JSON files."""
    data_layer = st.session_state["data_layer"]
    
    data_layer.save_users(st.session_state["user_manager"].users)
    data_layer.save_products(st.session_state["inventory_manager"].products)
    data_layer.save_sales(st.session_state["sales_manager"].sales)
    data_layer.save_flags(st.session_state["flag_manager"].flags)

def logout():
    """Handle user logout."""
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = None
    st.session_state["current_page"] = "dashboard"
    st.rerun()

def render_login_page():
    """Render the login and registration page."""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div class='app-header'>
                <h1>Inventory Manager</h1>
                <p>Small Business Inventory Management System</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class='test-accounts'>
                <h4>Test Accounts</h4>
                <div class='account-row'>
                    <strong>Owner Account:</strong><br/>
                    Email: james@test.com | Password: james123
                </div>
                <div class='account-row'>
                    <strong>Employee Account:</strong><br/>
                    Email: random@test.com | Password: random123
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.markdown("---")
        tab_login, tab_register = st.tabs(["Login", "Register"])
        
        with tab_login:
            st.subheader("Login to Your Account")
            
            with st.form("login_form"):
                username = st.text_input("Username/Email", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                
                if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                    auth_service = AuthenticationService(st.session_state["user_manager"])
                    success, user = auth_service.authenticate(username, password)
                    
                    if success and user:
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = user
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
        
        with tab_register:
            st.subheader("Create a New Account")
            
            with st.form("register_form"):
                reg_username = st.text_input("Choose Username", key="reg_username")
                reg_password = st.text_input("Choose Password", type="password", key="reg_password")
                reg_role = st.selectbox("Select Your Role", ["employee", "owner"], key="reg_role")
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    auth_service = AuthenticationService(st.session_state["user_manager"])
                    success, message = auth_service.register_user(reg_username, reg_password, reg_role)
                    
                    if success:
                        save_all_data()
                        st.success("Account created! You can now log in.")
                    else:
                        st.error(f"{message}")

def render_sidebar():
    """Render the sidebar navigation."""
    user = st.session_state["current_user"]
    
    with st.sidebar:
        st.markdown("### Navigation")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**{user.username}**")
        with col2:
            if st.button("Logout", use_container_width=True):
                logout()
        role_class = "role-owner" if user.is_owner() else "role-employee"
        st.markdown(
            f"<div class='role-badge {role_class}'>{user.role.upper()}</div>",
            unsafe_allow_html=True,
        )
        
        st.divider()
        st.subheader("Pages")
        
        if user.is_owner():
            pages = {
                "Dashboard": "dashboard",
                "Inventory": "inventory",
                "Reports": "reports",
                "AI Assistant": "assistant",
            }
        else:
            pages = {
                "Dashboard": "dashboard",
                "Catalog": "catalog",
                "Sales": "sales",
                "Low Stock Flags": "flags",
                "AI Assistant": "assistant",
            }
        
        for label, page_key in pages.items():
            if st.button(label, use_container_width=True, key=f"nav_{page_key}"):
                st.session_state["current_page"] = page_key
                st.rerun()

def render_owner_dashboard():
    """Render owner dashboard."""
    st.markdown("<div class='app-header'><h1>Owner Dashboard</h1><p>Business Performance Overview</p></div>", unsafe_allow_html=True)
    
    inventory_mgr = st.session_state["inventory_manager"]
    sales_mgr = st.session_state["sales_manager"]
    flag_mgr = st.session_state["flag_manager"]
    user_mgr = st.session_state["user_manager"]

    overview_tab, employees_tab = st.tabs(["Overview", "Employee Accounts"])

    with overview_tab:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Active Products", len(inventory_mgr.get_active_products()))
        with col2:
            st.metric("Low Stock Items", len(inventory_mgr.get_low_stock_items(strict=True)))
        with col3:
            st.metric("Total Sales", sales_mgr.get_sales_count())
        with col4:
            st.metric("Open Alerts", flag_mgr.get_open_flag_count())

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Revenue Summary")
            revenue = sales_mgr.get_total_revenue()
            avg_sale = sales_mgr.get_average_sale_value()

            st.metric("Total Revenue", f"${revenue:.2f}")
            st.metric("Average Sale", f"${avg_sale:.2f}")
            st.metric("Inventory Value", f"${inventory_mgr.calculate_total_value():.2f}")
        with col2:
            st.subheader("Recent Alerts")
            open_flags = flag_mgr.get_open_flags()[:5]

            if open_flags:
                for flag in open_flags:
                    with st.expander(f"{flag.product_name}", expanded=False):
                        st.write(f"**Flagged by:** {flag.flagged_by}")
                        st.write(f"**Note:** {flag.note}")
            else:
                st.success("No open alerts!")

    with employees_tab:
        st.subheader("Employee Account Management")

        tab_view, tab_create, tab_delete = st.tabs(["View Employees", "Create Employee", "Delete Employee"])

        with tab_view:
            employees = [user for user in user_mgr.users if user.role == "employee"]
            if employees:
                st.write(f"**Total Employees:** {len(employees)}")
                for emp in employees:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📧 {emp.username}")
                    with col2:
                        st.caption(f"Role: {emp.role.upper()}")
            else:
                st.info("No employees created yet.")

        with tab_create:
            st.write("Create a new employee account")
            with st.form("create_employee_form"):
                emp_username = st.text_input("Employee Username/Email", key="create_emp_username")
                emp_password = st.text_input("Employee Password", type="password", key="create_emp_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="create_emp_confirm")

                if st.form_submit_button("Create Employee Account", use_container_width=True, type="primary"):
                    if not emp_username or not emp_password:
                        st.error("Username and password are required.")
                    elif emp_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        auth_service = AuthenticationService(user_mgr)
                        success, message = auth_service.register_user(emp_username, emp_password, "employee")
                        if success:
                            save_all_data()
                            st.success(f"Employee account '{emp_username}' created successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to create account: {message}")

        with tab_delete:
            st.write("Delete an employee account")
            employees = [user for user in user_mgr.users if user.role == "employee"]

            if employees:
                emp_to_delete = st.selectbox(
                    "Select employee to delete",
                    options=employees,
                    format_func=lambda x: x.username,
                    key="delete_emp_select"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Delete Employee", use_container_width=True, type="secondary"):
                        user_mgr.users = [u for u in user_mgr.users if u.username != emp_to_delete.username]
                        save_all_data()
                        st.success(f"Employee account '{emp_to_delete.username}' has been deleted.")
                        st.rerun()
                with col2:
                    st.caption("⚠️ This action cannot be undone")
            else:
                st.info("No employees to delete.")

def render_owner_inventory():
    """Render owner inventory management page."""
    st.markdown("<div class='app-header'><h1>Inventory Management</h1><p>Add, Update, and Manage Products</p></div>", unsafe_allow_html=True)
    
    inventory_mgr = st.session_state["inventory_manager"]
    inventory_service = InventoryService(inventory_mgr)
    
    col_add, col_update = st.columns(2)
    with col_add:
        with st.container(border=True):
            st.subheader("Add New Product")
            
            with st.form("add_product_form"):
                name = st.text_input("Product Name")
                category = st.text_input("Category", value="General")
                price = st.number_input("Price ($)", min_value=0.01, step=0.25)
                stock = st.number_input("Initial Stock", min_value=0, step=1)
                threshold = st.number_input("Low Stock Threshold", min_value=1, value=5, step=1)
                
                if st.form_submit_button("Add Product", use_container_width=True, type="primary"):
                    success, message = inventory_service.add_product(name, category, price, stock, threshold)
                    if success:
                        save_all_data()
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    with col_update:
        with st.container(border=True):
            st.subheader("Update Product")
            
            active_products = inventory_mgr.get_active_products()
            if not active_products:
                st.info("No products to update yet.")
            else:
                selected_product = st.selectbox(
                    "Select Product",
                    options=active_products,
                    format_func=lambda p: p.name,
                    key="update_product_select"
                )
                
                with st.form("update_product_form"):
                    new_price = st.number_input("Price ($)", min_value=0.01, value=selected_product.price, step=0.25)
                    new_stock = st.number_input("Stock", min_value=0, value=selected_product.stock, step=1)
                    new_threshold = st.number_input("Threshold", min_value=1, value=selected_product.low_stock_threshold, step=1)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Save Changes", use_container_width=True):
                            success, message = inventory_service.update_product(
                                selected_product.product_id, new_price, new_stock, new_threshold
                            )
                            if success:
                                save_all_data()
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    
                    with col2:
                        if st.form_submit_button("Discontinue", use_container_width=True):
                            success, message = inventory_service.discontinue_product(selected_product.product_id)
                            if success:
                                save_all_data()
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
    st.divider()
    st.subheader("Active Catalog")
    active = inventory_mgr.get_active_products()
    
    if active:
        data = [
            {
                "Product": p.name,
                "Category": p.category,
                "Price": f"${p.price:.2f}",
                "Stock": p.stock,
                "Threshold": p.low_stock_threshold,
                "Status": "LOW" if p.is_low_stock() else "OK"
            }
            for p in active
        ]
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.info("No active products yet.")

def render_owner_reports():
    """Render owner reports page."""
    st.markdown("<div class='app-header'><h1>Reports</h1><p>Sales & Inventory Analytics</p></div>", unsafe_allow_html=True)
    
    sales_mgr = st.session_state["sales_manager"]
    flag_mgr = st.session_state["flag_manager"]
    
    tab_sales, tab_flags = st.tabs(["Sales Report", "Flag Report"])
    
    with tab_sales:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Sales", sales_mgr.get_sales_count())
        with col2:
            st.metric("Total Revenue", f"${sales_mgr.get_total_revenue():.2f}")
        with col3:
            st.metric("Avg Sale Value", f"${sales_mgr.get_average_sale_value():.2f}")
        
        st.subheader("Sales Log")
        if sales_mgr.sales:
            data = [
                {
                    "Product": s.product_name,
                    "Qty": s.quantity,
                    "Unit Price": f"${s.unit_price:.2f}",
                    "Total": f"${s.total:.2f}",
                    "Sold By": s.sold_by,
                    "Date": s.created_at[:10]
                }
                for s in sales_mgr.sales
            ]
            st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.info("No sales recorded yet.")
    
    with tab_flags:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Flags", len(flag_mgr.flags))
        with col2:
            st.metric("Open Flags", flag_mgr.get_open_flag_count())
        with col3:
            st.metric("Resolved", len(flag_mgr.flags) - flag_mgr.get_open_flag_count())
        
        st.subheader("Low Stock Flags")
        if flag_mgr.flags:
            data = [
                {
                    "Product": f.product_name,
                    "Status": f.status.upper(),
                    "Flagged By": f.flagged_by,
                    "Note": f.note,
                    "Date": f.created_at[:10]
                }
                for f in flag_mgr.flags
            ]
            st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.info("No flags submitted yet.")

def render_employee_dashboard():
    """Render employee dashboard."""
    st.markdown("<div class='app-header'><h1>Employee Dashboard</h1><p>Your Daily Operations</p></div>", unsafe_allow_html=True)
    
    user = st.session_state["current_user"]
    inventory_mgr = st.session_state["inventory_manager"]
    sales_mgr = st.session_state["sales_manager"]
    flag_mgr = st.session_state["flag_manager"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Products Available", len(inventory_mgr.get_active_products()))
    with col2:
        st.metric("Your Sales", len(sales_mgr.get_sales_by_employee(user.username)))
    with col3:
        st.metric("Your Flags", len(flag_mgr.get_flags_by_employee(user.username)))
    with col4:
        st.metric("Low Stock Items", len(inventory_mgr.get_low_stock_items()))
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Low Stock Inventory")
        low_stock = inventory_mgr.get_low_stock_items()
        
        if low_stock:
            data = [
                {
                    "Product": p.name,
                    "Stock": p.stock,
                    "Threshold": p.low_stock_threshold,
                    "Category": p.category
                }
                for p in low_stock
            ]
            st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.success("No items below threshold!")
    with col2:
        st.subheader("Your Recent Sales")
        my_sales = sales_mgr.get_sales_by_employee(user.username)
        
        if my_sales:
            data = [
                {
                    "Product": s.product_name,
                    "Qty": s.quantity,
                    "Total": f"${s.total:.2f}",
                    "Date": s.created_at[:10]
                }
                for s in my_sales[-5:]
            ]
            st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.info("No sales recorded yet.")

def render_employee_catalog():
    """Render employee product catalog."""
    st.markdown("<div class='app-header'><h1>Product Catalog</h1><p>Browse Available Products</p></div>", unsafe_allow_html=True)
    
    inventory_mgr = st.session_state["inventory_manager"]
    
    col_search, col_count = st.columns([2, 1])
    with col_search:
        search = st.text_input("Search by name or category").lower().strip()
    with col_count:
        filtered = inventory_mgr.get_catalog_for_employee(search)
        st.metric("Products Found", len(filtered))
    
    if filtered:
        data = [
            {
                "Product": p.name,
                "Category": p.category,
                "Price": f"${p.price:.2f}",
                "Stock": p.stock,
                "Available": "In Stock" if p.stock > 0 else "Out"
            }
            for p in filtered
        ]
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.info("No products match your search.")

def render_employee_sales():
    """Render employee sales recording page."""
    st.markdown("<div class='app-header'><h1>Record Sale</h1><p>Log Customer Purchases</p></div>", unsafe_allow_html=True)
    
    user = st.session_state["current_user"]
    inventory_mgr = st.session_state["inventory_manager"]
    sales_mgr = st.session_state["sales_manager"]
    sales_service = SalesService(sales_mgr, inventory_mgr)
    
    active = inventory_mgr.get_active_products()
    
    if not active:
        st.warning("No inventory available. Ask the owner to add products first.")
        return
    with st.container(border=True):
        st.subheader("New Sale")
        
        with st.form("record_sale_form"):
            selected = st.selectbox(
                "Select Product",
                options=active,
                format_func=lambda p: f"{p.name} (${p.price:.2f})",
                key="sales_product"
            )
            
            quantity = st.number_input("Quantity", min_value=1, value=1)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Current Stock:** {selected.stock}")
            with col2:
                st.write(f"**Sale Total:** ${selected.price * quantity:.2f}")
            
            if st.form_submit_button("Record Sale", use_container_width=True, type="primary"):
                success, message = sales_service.record_sale(selected.product_id, quantity, user.username)
                if success:
                    save_all_data()
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    st.divider()
    st.subheader("Your Sales History")
    my_sales = sales_mgr.get_sales_by_employee(user.username)
    
    if my_sales:
        data = [
            {
                "Product": s.product_name,
                "Qty": s.quantity,
                "Unit Price": f"${s.unit_price:.2f}",
                "Total": f"${s.total:.2f}",
                "Date": s.created_at[:10]
            }
            for s in my_sales
        ]
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.info("You haven't recorded any sales yet.")

def render_employee_flags():
    """Render employee low-stock flag page."""
    st.markdown("<div class='app-header'><h1>Low Stock Alerts</h1><p>Report Inventory Issues</p></div>", unsafe_allow_html=True)
    
    user = st.session_state["current_user"]
    inventory_mgr = st.session_state["inventory_manager"]
    flag_mgr = st.session_state["flag_manager"]
    flag_service = FlagService(flag_mgr, inventory_mgr)
    
    col_form, col_items = st.columns([1, 2])
    with col_form:
        with st.container(border=True):
            st.subheader("Submit Flag")
            
            low_stock = flag_service.get_low_stock_items()
            
            if not low_stock:
                st.info("✓ No low-stock items.")
            else:
                with st.form("flag_form"):
                    product = st.selectbox(
                        "Select Item",
                        options=low_stock,
                        format_func=lambda p: f"{p.name} ({p.stock}/{p.low_stock_threshold})",
                        key="flag_product"
                    )
                    
                    note = st.text_area("Note (optional)", max_chars=250, key="flag_note")
                    
                    if st.form_submit_button("Submit Flag", use_container_width=True, type="primary"):
                        success, message = flag_service.submit_flag(product.name, note, user.username)
                        if success:
                            save_all_data()
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
    with col_items:
        st.subheader("Items Below Threshold")
        
        low_stock = flag_service.get_low_stock_items()
        if low_stock:
            data = [
                {
                    "Product": p.name,
                    "Stock": p.stock,
                    "Threshold": p.low_stock_threshold,
                    "Category": p.category
                }
                for p in low_stock
            ]
            st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.success("No items below threshold!")
    st.divider()
    st.subheader("Your Flags")
    my_flags = flag_mgr.get_flags_by_employee(user.username)
    
    if my_flags:
        data = [
            {
                "Product": f.product_name,
                "Status": f.status.upper(),
                "Note": f.note,
                "Date": f.created_at[:10]
            }
            for f in my_flags
        ]
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.info("You haven't submitted any flags yet.")

def render_ai_assistant():
    """Render the AI assistant page."""
    st.markdown("<div class='app-header'><h1>AI Assistant</h1><p>Get Help with Inventory Management</p></div>", unsafe_allow_html=True)
    
    assistant = st.session_state["ai_assistant"]
    
    col_clear, col_info = st.columns([1, 3])
    with col_clear:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state["chat_history"] = [
                {
                    "role": "assistant",
                    "content": assistant.get_welcome_message()
                }
            ]
            st.rerun()
    
    with col_info:
        st.info("Ask me anything about inventory, sales, stock levels, or operational guidance.")
    with st.container(border=True, height=400):
        for message in st.session_state["chat_history"]:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    user_input = st.chat_input("Ask your question...")
    
    if user_input:
        st.session_state["chat_history"].append({
            "role": "user",
            "content": user_input
        })
        
        response = assistant.generate_response(user_input)
        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": response
        })
        
        st.rerun()

def main():
    """Main application logic."""
    initialize_session_state()
    
    if not st.session_state["authenticated"]:
        render_login_page()
    else:
        user = st.session_state["current_user"]
        
        render_sidebar()
        
        page = st.session_state.get("current_page", "dashboard")
        
        if page == "dashboard":
            if user.is_owner():
                render_owner_dashboard()
            else:
                render_employee_dashboard()
        
        elif page == "inventory":
            if user.is_owner():
                render_owner_inventory()
            else:
                st.error("Access denied.")
        
        elif page == "reports":
            if user.is_owner():
                render_owner_reports()
            else:
                st.error("Access denied.")
        
        elif page == "catalog":
            if user.is_employee():
                render_employee_catalog()
            else:
                st.error("Access denied.")
        
        elif page == "sales":
            if user.is_employee():
                render_employee_sales()
            else:
                st.error("Access denied.")
        
        elif page == "flags":
            if user.is_employee():
                render_employee_flags()
            else:
                st.error("Access denied.")
        
        elif page == "assistant":
            render_ai_assistant()
        
        else:
            st.error(f"Unknown page: {page}")

if __name__ == "__main__":
    main()
