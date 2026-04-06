import uuid
import streamlit as st

from data_access import DataAccess

st.set_page_config(page_title="Small Business Inventory Manager", layout="wide")

st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1.2rem; padding-bottom: 1.8rem; }
    .app-hero {
        border: 1px solid #d9d9d9; border-radius: 14px; padding: 1rem 1.1rem;
        margin-bottom: 1rem; background: linear-gradient(180deg, #fffef8 0%, #ffffff 100%);
        color: #1f2937;
    }
    .app-hero strong { color: #111827; }
    .role-owner { border-left: 6px solid #3a7d44; }
    .role-employee { border-left: 6px solid #1f6aa5; }
    .section-title { margin-top: 0.4rem; margin-bottom: 0.35rem; font-size: 1.2rem; font-weight: 700; }
    .section-sub { margin-top: 0; margin-bottom: 0.85rem; color: #5f6368; }
    .table-group { margin-top: 0.35rem; }
    .table-group h3 { margin-bottom: 0.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

store = DataAccess()
DATASETS = ["inventory", "sales", "flags", "users"]
ROLE_OPTIONS = ["employee", "owner"]
DEFAULT_CHAT = "Hello! I am your inventory helper. Ask me about low stock, sales logging, or flagging items."
NAV = {
    "owner": {
        "Owner Inventory": "owner_inventory",
        "Owner Reports": "owner_reports",
        "AI Assistant": "assistant",
    },
    "employee": {
        "Employee Catalog": "employee_catalog",
        "Employee Sales": "employee_sales",
        "Employee Flags": "employee_flags",
        "AI Assistant": "assistant",
    },
}


def clean_text(value):
    return value.strip()


def load_dataset(name, fallback=None):
    ok, data, error = store.load(name)
    if not ok:
        st.error(f"We could not load {name} data: {error}")
        return fallback if fallback is not None else []
    return data


def persist_dataset(name):
    ok, error = store.save(name, st.session_state[name])
    if not ok:
        return False, f"We could not save {name} data: {error}"
    return True, ""


def safe_persist(name, fallback=None):
    ok, msg = persist_dataset(name)
    if ok:
        return True
    st.error(msg)
    if fallback is not None:
        st.session_state[name] = load_dataset(name, fallback=fallback)
    return False


def ensure_inventory_defaults(items):
    changed = False
    for item in items:
        if "product_id" not in item:
            item["product_id"] = str(uuid.uuid4())
            changed = True
        if "low_stock_threshold" not in item:
            item["low_stock_threshold"] = 5
            changed = True
        if "discontinued" not in item:
            item["discontinued"] = False
            changed = True
    return changed


def ensure_user_defaults(users):
    changed = False
    for user in users:
        if "role" not in user:
            user["role"] = "employee"
            changed = True
    return changed


def init_session_state():
    for name in DATASETS:
        st.session_state.setdefault(name, load_dataset(name))

    if ensure_inventory_defaults(st.session_state["inventory"]):
        safe_persist("inventory", fallback=st.session_state["inventory"])
    if ensure_user_defaults(st.session_state["users"]):
        safe_persist("users", fallback=st.session_state["users"])

    st.session_state.setdefault("messages", [{"role": "assistant", "content": DEFAULT_CHAT}])
    st.session_state.setdefault("page", "login")
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("current_user", "")
    st.session_state.setdefault("current_role", "")


def render_section_title(title, subtitle=""):
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='section-sub'>{subtitle}</div>", unsafe_allow_html=True)


def render_table_group(title, rows, empty_message):
    st.markdown("<div class='table-group'>", unsafe_allow_html=True)
    st.subheader(title)
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info(empty_message)
    st.markdown("</div>", unsafe_allow_html=True)


def active_inventory():
    return [i for i in st.session_state["inventory"] if not i.get("discontinued", False)]


def low_stock_items(strict=False):
    compare = (lambda stock, threshold: stock < threshold) if strict else (lambda stock, threshold: stock <= threshold)
    return [
        i
        for i in active_inventory()
        if compare(i.get("stock", 0), i.get("low_stock_threshold", 5))
    ]


def get_by_id(items, key, value):
    return next((item for item in items if item.get(key) == value), None)


def validate_registration(username, password, role):
    users = st.session_state["users"]
    username, password = clean_text(username), clean_text(password)
    if not username:
        return False, "Username is required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not password:
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if role not in ROLE_OPTIONS:
        return False, "Please select a valid role."
    if next((u for u in users if u.get("username", "").lower() == username.lower()), None):
        return False, "That username is already taken."
    return True, ""


def validate_product_input(name, price, stock, threshold):
    name = clean_text(name)
    items = st.session_state["inventory"]
    if not name:
        return False, "Product name is required."
    if len(name) < 2:
        return False, "Product name must be at least 2 characters."
    duplicate = next(
        (i for i in items if not i.get("discontinued", False) and i.get("name", "").lower() == name.lower()),
        None,
    )
    if duplicate:
        return False, "A product with that name already exists."
    if price <= 0:
        return False, "Price must be greater than 0."
    if price > 100000:
        return False, "Price is too large."
    if stock < 0:
        return False, "Stock cannot be negative."
    if stock > 100000:
        return False, "Stock is too large."
    if threshold < 1:
        return False, "Low stock threshold must be at least 1."
    if threshold > 100000:
        return False, "Low stock threshold is too large."
    return True, ""


def validate_sale(item, quantity):
    if item is None:
        return False, "Please select a valid item."
    if quantity < 1:
        return False, "Quantity must be at least 1."
    if quantity > item.get("stock", 0):
        return False, "Quantity cannot be greater than current stock."
    return True, ""


def validate_flag_note(note):
    return (False, "Flag note must be 250 characters or fewer.") if len(note.strip()) > 250 else (True, "")


def register_user(username, password, role):
    ok, msg = validate_registration(username, password, role)
    if not ok:
        return False, msg

    users = st.session_state["users"]
    users.append(
        {
            "user_id": len(users) + 1,
            "username": clean_text(username),
            "password": clean_text(password),
            "role": role,
        }
    )
    if not safe_persist("users"):
        users.pop()
        return False, "Registration failed because user data could not be saved."
    return True, "Registration successful. You can now log in."


def add_product(name, category, price, stock, threshold):
    ok, msg = validate_product_input(name, price, stock, threshold)
    if not ok:
        return False, msg

    inventory = st.session_state["inventory"]
    inventory.append(
        {
            "product_id": str(uuid.uuid4()),
            "name": clean_text(name),
            "category": clean_text(category) or "General",
            "price": float(price),
            "stock": int(stock),
            "low_stock_threshold": int(threshold),
            "discontinued": False,
        }
    )
    if not safe_persist("inventory"):
        inventory.pop()
        return False, "Product could not be saved."
    return True, "Product added successfully."


def update_product(product_id, price, stock, threshold):
    item = get_by_id(st.session_state["inventory"], "product_id", product_id)
    if item is None:
        return False, "Selected product was not found."
    if price <= 0:
        return False, "Price must be greater than 0."
    if stock < 0:
        return False, "Stock cannot be negative."
    if threshold < 1:
        return False, "Low stock threshold must be at least 1."

    backup = (item.get("price", 0), item.get("stock", 0), item.get("low_stock_threshold", 5))
    item["price"], item["stock"], item["low_stock_threshold"] = float(price), int(stock), int(threshold)
    if not safe_persist("inventory"):
        item["price"], item["stock"], item["low_stock_threshold"] = backup
        return False, "Product update could not be saved."
    return True, "Product updated successfully."


def discontinue_product(product_id):
    item = get_by_id(st.session_state["inventory"], "product_id", product_id)
    if item is None:
        return False, "Selected product was not found."
    previous = item.get("discontinued", False)
    item["discontinued"] = True
    if not safe_persist("inventory"):
        item["discontinued"] = previous
        return False, "Could not mark item as discontinued."
    return True, "Product marked as discontinued."


def record_sale(product_id, quantity, sold_by):
    item = get_by_id(active_inventory(), "product_id", product_id)
    ok, msg = validate_sale(item, quantity)
    if not ok:
        return False, msg

    quantity = int(quantity)
    old_stock = item["stock"]
    item["stock"] = old_stock - quantity
    sale = {
        "sale_id": str(uuid.uuid4()),
        "product_name": item["name"],
        "quantity": quantity,
        "unit_price": item["price"],
        "total": item["price"] * quantity,
        "sold_by": sold_by,
    }
    st.session_state["sales"].append(sale)

    if not safe_persist("inventory"):
        item["stock"] = old_stock
        st.session_state["sales"].pop()
        return False, "Sale failed while saving inventory."
    if not safe_persist("sales"):
        item["stock"] = old_stock
        st.session_state["sales"].pop()
        return False, "Sale failed while saving sales log."
    return True, "Sale logged and stock updated successfully."


def submit_low_stock_flag(product_name, note, flagged_by):
    ok, msg = validate_flag_note(note)
    if not ok:
        return False, msg

    flags = st.session_state["flags"]
    flags.append(
        {
            "flag_id": str(uuid.uuid4()),
            "product_name": product_name,
            "flagged_by": flagged_by,
            "note": note.strip() or "No additional note provided.",
            "status": "open",
        }
    )
    if not safe_persist("flags"):
        flags.pop()
        return False, "Flag could not be saved."
    return True, "Low-stock flag submitted."


def login_user(username, password):
    username, password = clean_text(username), clean_text(password)
    user = next(
        (
            u
            for u in st.session_state["users"]
            if u.get("username", "").lower() == username.lower() and u.get("password") == password
        ),
        None,
    )
    if not user:
        return False

    st.session_state["authenticated"] = True
    st.session_state["current_user"] = user["username"]
    st.session_state["current_role"] = user.get("role", "employee")
    st.session_state["page"] = "owner_inventory" if st.session_state["current_role"] == "owner" else "employee_catalog"
    return True


def logout_user():
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = ""
    st.session_state["current_role"] = ""
    st.session_state["page"] = "login"


def generate_ai_response(prompt_text):
    prompt = prompt_text.lower().strip()
    if any(word in prompt for word in ["hello", "hi", "hey"]):
        return "Hello! I can help with low-stock checks, sales logging guidance, and flagging inventory risks."
    if "low" in prompt and "stock" in prompt:
        items = low_stock_items(strict=True)
        if not items:
            return "Low-stock alert list:\nNo items are currently below their low-stock threshold."
        lines = [f"- {i['name']} (stock: {i['stock']}, threshold: {i.get('low_stock_threshold', 5)})" for i in items]
        return "Low-stock alert list:\n" + "\n".join(lines)
    if "log" in prompt and "sale" in prompt:
        return "To log a sale: open Employee Sales, choose product, enter quantity, and submit."
    if "flag" in prompt or "danger" in prompt:
        return "To flag low inventory: open Employee Flags, select a low-stock item, add a short note, and submit."
    return "I can answer: low stock status, how to log a sale, and how to flag low-stock items."


def render_auth_screen():
    st.title("Small Business Inventory Manager")
    st.markdown(
        "<div class='app-hero role-employee'><strong>Welcome.</strong> Sign in to continue or create an account to start managing inventory workflows.</div>",
        unsafe_allow_html=True,
    )

    logged_in = False
    _, center, _ = st.columns([1, 1.6, 1])
    with center:
        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab, st.container(border=True):
            render_section_title("Login", "Use your account credentials to continue.")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_btn", use_container_width=True, type="primary"):
                if login_user(username, password):
                    st.success("Login successful.")
                    logged_in = True
                else:
                    st.error("Invalid username or password. Please try again.")

        with register_tab, st.container(border=True):
            render_section_title("Register", "Create a new account and choose your role.")
            username = st.text_input("Username", key="reg_username")
            password = st.text_input("Password", type="password", key="reg_password")
            role = st.selectbox("Role", ROLE_OPTIONS, key="reg_role")
            if st.button("Create Account", key="register_btn", use_container_width=True):
                ok, msg = register_user(username, password, role)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
    return logged_in


def render_sidebar_navigation():
    role = st.session_state["current_role"]
    choices = NAV["owner"] if role == "owner" else NAV["employee"]
    labels = list(choices.keys())

    with st.sidebar:
        st.markdown("### Navigation")
        st.write(f"Logged in as: {st.session_state['current_user']}")
        st.write(f"Role: {role.title()}")
        st.divider()

        default_page = "owner_inventory" if role == "owner" else "employee_catalog"
        current_page = st.session_state.get("page", default_page)
        current_label = next((label for label, page in choices.items() if page == current_page), labels[0])
        nav_key = "sidebar_owner_nav" if role == "owner" else "sidebar_employee_nav"

        selected_label = st.radio("Go to", labels, index=labels.index(current_label), key=nav_key)
        st.session_state["page"] = choices[selected_label]

        st.divider()
        if st.button("Logout", use_container_width=True, key="logout_btn"):
            logout_user()
            return True
    return False


def render_ai_assistant():
    render_section_title("Simulated AI Assistant", "This assistant uses 5 hardcoded response patterns.")
    _, clear_col = st.columns([4, 1])
    with clear_col:
        if st.button("Clear chat", key="clear_chat_btn", use_container_width=True):
            st.session_state["messages"] = [{"role": "assistant", "content": DEFAULT_CHAT}]

    question = st.chat_input("Ask a question", key="assistant_chat_input")
    if question:
        st.session_state["messages"].append({"role": "user", "content": question})
        st.session_state["messages"].append({"role": "assistant", "content": generate_ai_response(question)})

    with st.container(border=True, height=360):
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.write(message["content"])


def render_owner_inventory_page():
    inventory = st.session_state["inventory"]
    active = active_inventory()
    render_section_title("Owner Inventory Management", "Control products, pricing, and stock status.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Active Products", len(active))
    c2.metric("Low Stock Items", len(low_stock_items(strict=True)))
    c3.metric("Discontinued", len(inventory) - len(active))

    create_col, update_col = st.columns(2)
    with create_col, st.container(border=True):
        st.subheader("Add Product")
        with st.form("owner_add_product_form"):
            name = st.text_input("Product Name", key="owner_new_name")
            category = st.text_input("Category", key="owner_new_category")
            price = st.number_input("Price", min_value=0.01, max_value=100000.0, step=0.25, key="owner_new_price")
            stock = st.number_input("Stock", min_value=0, max_value=100000, step=1, key="owner_new_stock")
            threshold = st.number_input("Low Stock Threshold", min_value=1, max_value=100000, step=1, value=5, key="owner_new_threshold")
            if st.form_submit_button("Add Product", use_container_width=True):
                ok, msg = add_product(name, category, price, stock, threshold)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    with update_col, st.container(border=True):
        st.subheader("Update / Discontinue")
        if not active:
            st.info("No active products yet. Add your first product from the panel on the left.")
        else:
            item_map = {item["product_id"]: item for item in active}
            selected_id = st.selectbox(
                "Select Product",
                options=list(item_map.keys()),
                format_func=lambda product_id: item_map[product_id]["name"],
                key="owner_select_update",
            )
            selected = item_map[selected_id]

            with st.form("owner_update_product_form"):
                price = st.number_input("Update Price", min_value=0.01, max_value=100000.0, step=0.25, value=float(selected["price"]), key="owner_upd_price")
                stock = st.number_input("Update Stock", min_value=0, max_value=100000, step=1, value=int(selected["stock"]), key="owner_upd_stock")
                threshold = st.number_input("Update Threshold", min_value=1, max_value=100000, step=1, value=int(selected.get("low_stock_threshold", 5)), key="owner_upd_threshold")
                if st.form_submit_button("Save Changes", use_container_width=True):
                    ok, msg = update_product(selected_id, price, stock, threshold)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

            if st.button("Mark as Discontinued", key="owner_discontinue_btn", use_container_width=True):
                ok, msg = discontinue_product(selected_id)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    rows = [
        {
            "Name": item["name"],
            "Category": item.get("category", "General"),
            "Price": f"${item['price']:.2f}",
            "Stock": item["stock"],
            "Threshold": item.get("low_stock_threshold", 5),
        }
        for item in active
    ]
    with st.container(border=True):
        render_table_group("Current Catalog", rows, "No active products in catalog.")


def render_owner_reports_page():
    sales = st.session_state["sales"]
    flags = st.session_state["flags"]
    revenue = sum(sale.get("total", 0) for sale in sales)
    open_flags = sum(1 for flag in flags if flag.get("status") == "open")

    render_section_title("Owner Reports", "Track sales performance and low-stock alerts.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sales", len(sales))
    c2.metric("Revenue", f"${revenue:.2f}")
    c3.metric("Open Flags", open_flags)

    tab_sales, tab_flags = st.tabs(["Sales Log", "Low Stock Flags"])
    with tab_sales, st.container(border=True):
        rows = [
            {
                "Product": sale.get("product_name", ""),
                "Qty": sale.get("quantity", 0),
                "Unit Price": f"${sale.get('unit_price', 0):.2f}",
                "Total": f"${sale.get('total', 0):.2f}",
                "Sold By": sale.get("sold_by", ""),
            }
            for sale in sales
        ]
        render_table_group("Sales Log", rows, "No sales recorded yet.")

    with tab_flags, st.container(border=True):
        rows = [
            {
                "Product": flag.get("product_name", ""),
                "Flagged By": flag.get("flagged_by", ""),
                "Note": flag.get("note", ""),
                "Status": flag.get("status", "open"),
            }
            for flag in flags
        ]
        render_table_group("Low Stock Flags", rows, "No low-stock flags submitted yet.")


def render_employee_catalog_page():
    items = active_inventory()
    render_section_title("Employee Catalog", "Browse current inventory and stock levels.")

    col_search, col_count = st.columns([2, 1])
    with col_search:
        search = st.text_input("Search by product name", key="employee_catalog_search").lower().strip()
    with col_count:
        st.metric("Products", len(items))

    filtered = [i for i in items if search in i["name"].lower() or search in i.get("category", "").lower()]
    st.metric("Total Items in Stock", sum(i.get("stock", 0) for i in filtered))

    rows = [
        {
            "Name": item["name"],
            "Category": item.get("category", "General"),
            "Price": f"${item['price']:.2f}",
            "Stock": item["stock"],
        }
        for item in filtered
    ]
    with st.container(border=True):
        render_table_group("Catalog", rows, "No products matched your search. Try a different name or category.")


def render_employee_sales_page():
    items = active_inventory()
    render_section_title("Employee Sales", "Record customer purchases and update stock.")

    with st.container(border=True):
        if not items:
            st.info("No inventory available to sell. Ask the owner to add products first.")
            return

        item_map = {item["product_id"]: item for item in items}
        selected_id = st.selectbox(
            "Select Item",
            options=list(item_map.keys()),
            format_func=lambda product_id: item_map[product_id]["name"],
            key="employee_sales_item",
        )
        quantity = st.number_input("Quantity Sold", min_value=1, max_value=100000, step=1, key="employee_sales_qty")
        selected = item_map[selected_id]

        c1, c2 = st.columns(2)
        c1.write(f"Current stock: {selected['stock']}")
        c2.write(f"Price: ${selected['price']:.2f}")

        if st.button("Record Sale", key="record_sale_btn", use_container_width=True, type="primary"):
            ok, msg = record_sale(selected_id, quantity, st.session_state["current_user"])
            if ok:
                st.success(msg)
            else:
                st.error(msg)


def render_employee_flags_page():
    flags = st.session_state["flags"]
    items = low_stock_items(strict=False)
    render_section_title("Employee Flags", "Notify the owner about inventory risks.")

    view_col, form_col = st.columns([2, 1])
    with view_col, st.container(border=True):
        rows = [{"Name": i["name"], "Stock": i["stock"], "Threshold": i.get("low_stock_threshold", 5)} for i in items]
        render_table_group("Items Needing Attention", rows, "Great news: no items are currently below threshold.")

    with form_col, st.container(border=True):
        st.subheader("Submit Flag")
        if not items:
            st.write("No low-stock items to flag.")
        else:
            names = [item["name"] for item in items]
            product = st.selectbox("Select item", names, key="employee_flags_item")
            note = st.text_area("Reason / note", key="employee_flags_note", max_chars=250)
            if st.button("Submit Flag", key="submit_flag_btn", use_container_width=True):
                ok, msg = submit_low_stock_flag(product, note, st.session_state["current_user"])
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    my_rows = [
        {"Product": f.get("product_name", ""), "Note": f.get("note", ""), "Status": f.get("status", "open")}
        for f in flags
        if f.get("flagged_by") == st.session_state["current_user"]
    ]
    render_table_group("Your Recent Flags", my_rows, "You have not submitted any flags yet.")


def render_main_app():
    if not st.session_state["authenticated"]:
        return

    role = st.session_state["current_role"]
    st.title("Small Business Inventory Manager")
    if role == "owner":
        st.markdown(
            "<div class='app-hero role-owner'><strong>Owner Control Panel</strong><br/>Manage inventory strategy, review reports, and monitor team activity.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='app-hero role-employee'><strong>Employee Operations Portal</strong><br/>Use catalog, sales, and low-stock workflows to keep daily operations smooth.</div>",
            unsafe_allow_html=True,
        )

    if render_sidebar_navigation():
        return

    route = {
        "assistant": render_ai_assistant,
        "owner_inventory": render_owner_inventory_page,
        "owner_reports": render_owner_reports_page,
        "employee_catalog": render_employee_catalog_page,
        "employee_sales": render_employee_sales_page,
        "employee_flags": render_employee_flags_page,
    }
    default_page = "owner_inventory" if role == "owner" else "employee_catalog"
    route.get(st.session_state.get("page", default_page), route[default_page])()


def main():
    init_session_state()
    if not st.session_state["authenticated"]:
        if render_auth_screen():
            render_main_app()
    else:
        render_main_app()


main()
