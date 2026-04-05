import streamlit as st
import json
from pathlib import Path
import uuid

st.set_page_config(page_title="Small Business Inventory Manager", layout="wide")

inventory_file = Path("inventory.json")
sales_file = Path("sales.json")
flags_file = Path("flags.json")
users_file = Path("users.json")

if "inventory" not in st.session_state:
    if inventory_file.exists():
        with open(inventory_file, "r") as f:
            st.session_state["inventory"] = json.load(f)
    else:
        st.session_state["inventory"] = []

if "sales" not in st.session_state:
    if sales_file.exists():
        with open(sales_file, "r") as f:
            st.session_state["sales"] = json.load(f)
    else:
        st.session_state["sales"] = []

if "flags" not in st.session_state:
    if flags_file.exists():
        with open(flags_file, "r") as f:
            st.session_state["flags"] = json.load(f)
    else:
        st.session_state["flags"] = []

if "users" not in st.session_state:
    if users_file.exists():
        with open(users_file, "r") as f:
            st.session_state["users"] = json.load(f)
    else:
        st.session_state["users"] = []

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "Hello! I am your inventory helper. Ask me about low stock, sales logging, or flagging items.",
        }
    ]

if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"

if "employee_name" not in st.session_state:
    st.session_state["employee_name"] = "Employee"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "current_user" not in st.session_state:
    st.session_state["current_user"] = ""


def save_inventory():
    with open(inventory_file, "w") as f:
        json.dump(st.session_state["inventory"], f, indent=4)


def save_sales():
    with open(sales_file, "w") as f:
        json.dump(st.session_state["sales"], f, indent=4)


def save_flags():
    with open(flags_file, "w") as f:
        json.dump(st.session_state["flags"], f, indent=4)


def save_users():
    with open(users_file, "w") as f:
        json.dump(st.session_state["users"], f, indent=4)


def register_user(username, password):
    users = st.session_state["users"]

    if username.strip() == "" or password.strip() == "":
        return False, "Username and password are required"

    exists = next((u for u in users if u["username"].lower() == username.lower()), None)
    if exists:
        return False, "Username already exists"

    users.append(
        {
            "user_id": len(users) + 1,
            "username": username.strip(),
            "password": password,
        }
    )
    save_users()
    return True, "Registration successful"


def login_user(username, password):
    user = next(
        (
            u
            for u in st.session_state["users"]
            if u["username"].lower() == username.lower() and u["password"] == password
        ),
        None,
    )

    if user:
        st.session_state["authenticated"] = True
        st.session_state["current_user"] = user["username"]
        st.session_state["employee_name"] = user["username"]
        st.session_state["page"] = "dashboard"
        return True
    return False


def logout_user():
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = ""
    st.session_state["employee_name"] = "Employee"
    st.session_state["page"] = "dashboard"


def get_low_stock_items():
    low_items = []
    for item in st.session_state["inventory"]:
        if not item.get("discontinued", False) and item.get("stock", 0) < 5:
            low_items.append(item)
    return low_items


def generate_ai_response(user_prompt):
    prompt = user_prompt.lower().strip()

    if "hello" in prompt or "hi" in prompt or "hey" in prompt:
        return "Hello! I can help with low-stock checks, sales logging guidance, and flagging inventory risks."

    if "low" in prompt and "stock" in prompt:
        low_items = get_low_stock_items()
        if not low_items:
            return "Low-stock alert list:\nNo items are currently below stock level 5."

        lines = []
        for item in low_items:
            threshold = item.get("low_stock_threshold", 5)
            lines.append(f"- {item['name']} (stock: {item['stock']}, threshold: {threshold})")
        return "Low-stock alert list:\n" + "\n".join(lines)

    if "log" in prompt and "sale" in prompt:
        return "To log a sale: open Employee Dashboard, go to Log Daily Sale, choose product, enter quantity, and submit."

    if "flag" in prompt or "danger" in prompt:
        return "To flag low inventory: open Employee Dashboard, go to Flag Low Stock, choose an item, add a note, and submit."

    return "I can answer: low stock status, how to log a sale, and how to flag low-stock items."


if not st.session_state["authenticated"]:
    st.title("Small Business Inventory Manager")
    st.caption("Login or register to continue")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.header("Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_btn"):
            if login_user(login_username, login_password):
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        st.header("Register")
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        if st.button("Create Account", key="register_btn"):
            ok, message = register_user(reg_username, reg_password)
            if ok:
                st.success(message)
            else:
                st.error(message)

else:
    st.title("Small Business Inventory Manager")
    st.caption("Employee operations portal")

    with st.sidebar:
        st.write(f"Logged in as: {st.session_state['current_user']}")
        st.divider()

        if st.button("Dashboard", use_container_width=True, type="primary"):
            st.session_state["page"] = "dashboard"
            st.rerun()

        if st.button("AI Assistant", use_container_width=True):
            st.session_state["page"] = "assistant"
            st.rerun()

        if st.button("Logout", use_container_width=True):
            logout_user()
            st.success("Logged out")
            st.rerun()

    if st.session_state["page"] == "assistant":
        st.header("Simulated AI Assistant")
        st.caption("This assistant uses 5 hardcoded response patterns.")

        if st.button("Clear chat"):
            st.session_state["messages"] = [
                {
                    "role": "assistant",
                    "content": "Hello! I am your inventory helper. Ask me about low stock, sales logging, or flagging items.",
                }
            ]
            st.rerun()

        with st.container(border=True, height=350):
            for message in st.session_state["messages"]:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        user_prompt = st.chat_input("Ask a question")
        if user_prompt:
            st.session_state["messages"].append({"role": "user", "content": user_prompt})
            ai_response = generate_ai_response(user_prompt)
            st.session_state["messages"].append({"role": "assistant", "content": ai_response})
            st.rerun()

    else:
        inventory = st.session_state["inventory"]
        sales = st.session_state["sales"]
        flags = st.session_state["flags"]

        tab1, tab2, tab3 = st.tabs(["Catalog", "Log Daily Sale", "Flag Low Stock"])

        with tab1:
            st.header("Catalog")
            search = st.text_input("Search by product name", key="search_inventory")

            filtered = []
            for item in inventory:
                if not item.get("discontinued", False):
                    if search.lower() in item["name"].lower() or search.lower() in item.get("category", "").lower():
                        filtered.append(item)

            total_stock = 0
            for item in filtered:
                total_stock += item.get("stock", 0)

            st.metric("Total Items in Stock", total_stock)

            if filtered:
                st.dataframe(filtered, use_container_width=True)
            else:
                st.write("No products matched your search")

        with tab2:
            st.header("Log Daily Sale")

            available_items = []
            for item in inventory:
                if not item.get("discontinued", False):
                    available_items.append(item)

            if available_items:
                item_names = [item["name"] for item in available_items]
                selected_item_name = st.selectbox("Select Item", item_names, key="sale_item")
                quantity = st.number_input("Quantity Sold", min_value=1, step=1, key="sale_qty")

                selected_item = next((i for i in available_items if i["name"] == selected_item_name), None)

                if selected_item:
                    st.write(f"Current stock: {selected_item['stock']}")
                    st.write(f"Price: ${selected_item['price']:.2f}")

                if st.button("Record Sale", key="record_sale_btn"):
                    if selected_item and selected_item["stock"] >= quantity:
                        selected_item["stock"] -= quantity
                        total = selected_item["price"] * quantity

                        sale = {
                            "sale_id": str(uuid.uuid4()),
                            "product_name": selected_item_name,
                            "quantity": quantity,
                            "unit_price": selected_item["price"],
                            "total": total,
                            "sold_by": st.session_state["current_user"],
                        }

                        sales.append(sale)
                        save_inventory()
                        save_sales()
                        st.success("Sale logged and stock updated")
                        st.rerun()
                    else:
                        st.error("Cannot sell more than current stock")
            else:
                st.write("No inventory available to sell")

        with tab3:
            st.header("Flag Low Stock")

            low_items = []
            for item in inventory:
                threshold = item.get("low_stock_threshold", 5)
                if not item.get("discontinued", False) and item.get("stock", 0) <= threshold:
                    low_items.append(item)

            if low_items:
                st.dataframe(low_items, use_container_width=True)

                low_item_names = [item["name"] for item in low_items]
                selected_flag_item = st.selectbox("Select item to flag", low_item_names, key="flag_item")
                flag_note = st.text_area("Reason / note", key="flag_note")

                if st.button("Submit low-stock flag", key="submit_flag_btn"):
                    flag = {
                        "flag_id": str(uuid.uuid4()),
                        "product_name": selected_flag_item,
                        "flagged_by": st.session_state["current_user"],
                        "note": flag_note.strip() if flag_note.strip() else "No additional note provided.",
                        "status": "open",
                    }
                    flags.append(flag)
                    save_flags()
                    st.success("Low-stock flag submitted")
                    st.rerun()
            else:
                st.write("No items currently need low-stock flagging")

            st.subheader("Your Recent Flags")
            my_flags = [flag for flag in flags if flag.get("flagged_by") == st.session_state["current_user"]]
            if my_flags:
                st.dataframe(my_flags, use_container_width=True)
            else:
                st.write("You have not submitted any flags yet")
