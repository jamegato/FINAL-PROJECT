"""
Service/Business Logic layer for the inventory management system.
Handles validation, user authentication, business rules, and operations.
"""

from typing import Tuple, List, Optional
from models import (
    User, Product, Sale, Flag, UserRole,
    InventoryManager, SalesManager, FlagManager, UserManager
)


class ValidationService:
    """Handles validation of user input and business rules."""

    @staticmethod
    def clean_text(value: str) -> str:
        """Clean and strip whitespace from text input."""
        return value.strip() if value else ""

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate display username format.
        
        Returns:
            Tuple of (valid, error_message)
        """
        username = ValidationService.clean_text(username)
        if not username:
            return False, "Username is required."
        if len(username) < 3:
            return False, "Username must be at least 3 characters."
        return True, ""

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format."""
        email = ValidationService.clean_text(email)
        if not email:
            return False, "Email is required."
        if "@" not in email or "." not in email.split("@")[-1]:
            return False, "Please enter a valid email address."
        return True, ""

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password format.
        
        Returns:
            Tuple of (valid, error_message)
        """
        if not password:
            return False, "Password is required."
        if len(password) < 6:
            return False, "Password must be at least 6 characters."
        return True, ""

    @staticmethod
    def validate_role(role: str) -> Tuple[bool, str]:
        """Validate user role."""
        valid_roles = [UserRole.OWNER.value, UserRole.EMPLOYEE.value]
        if role not in valid_roles:
            return False, f"Role must be one of: {', '.join(valid_roles)}"
        return True, ""

    @staticmethod
    def validate_registration(
        email: str,
        username: str,
        password: str,
        role: str,
        user_manager: UserManager
    ) -> Tuple[bool, str]:
        """
        Validate registration inputs.
        
        Returns:
            Tuple of (valid, error_message)
        """
        valid, msg = ValidationService.validate_email(email)
        if not valid:
            return False, msg

        valid, msg = ValidationService.validate_username(username)
        if not valid:
            return False, msg

        valid, msg = ValidationService.validate_password(password)
        if not valid:
            return False, msg

        valid, msg = ValidationService.validate_role(role)
        if not valid:
            return False, msg

        if user_manager.email_exists(email):
            return False, "That email is already registered."

        if user_manager.username_exists(username):
            return False, "That username is already taken."

        return True, ""

    @staticmethod
    def validate_product_input(
        name: str,
        category: str,
        price: float,
        stock: int,
        threshold: int,
        inventory_manager: InventoryManager,
        exclude_product_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate product creation/update inputs.
        
        Returns:
            Tuple of (valid, error_message)
        """
        name = ValidationService.clean_text(name)
        if not name:
            return False, "Product name is required."
        if len(name) < 2:
            return False, "Product name must be at least 2 characters."

        # Check for duplicates (excluding current product if updating)
        active_products = inventory_manager.get_active_products()
        duplicate = next(
            (p for p in active_products 
             if p.name.lower() == name.lower() and p.product_id != exclude_product_id),
            None
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

    @staticmethod
    def validate_sale(
        product: Optional[Product],
        quantity: int
    ) -> Tuple[bool, str]:
        """
        Validate sale inputs.
        
        Returns:
            Tuple of (valid, error_message)
        """
        if product is None:
            return False, "Please select a valid item."
        if quantity < 1:
            return False, "Quantity must be at least 1."
        if quantity > product.stock:
            return False, f"Quantity cannot exceed available stock ({product.stock})."
        return True, ""

    @staticmethod
    def validate_flag_note(note: str) -> Tuple[bool, str]:
        """
        Validate flag note length.
        
        Returns:
            Tuple of (valid, error_message)
        """
        if len(note.strip()) > 250:
            return False, "Flag note must be 250 characters or fewer."
        return True, ""


class AuthenticationService:
    """Handles user authentication and registration."""

    def __init__(self, user_manager: UserManager):
        """Initialize with a user manager."""
        self.user_manager = user_manager
        self.validation = ValidationService()

    def register_user(self, email: str, username: str, password: str, role: str) -> Tuple[bool, str]:
        """
        Register a new user.
        
        Returns:
            Tuple of (success, message)
        """
        valid, msg = self.validation.validate_registration(email, username, password, role, self.user_manager)
        if not valid:
            return False, msg

        email = self.validation.clean_text(email)
        username = self.validation.clean_text(username)
        password = self.validation.clean_text(password)
        
        next_id = max((u.user_id for u in self.user_manager.users), default=0) + 1
        user = User(user_id=next_id, email=email, username=username, password=password, role=role)
        
        if self.user_manager.add_user(user):
            return True, "Registration successful. You can now log in."
        return False, "Registration failed. Please try again."

    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[User]]:
        """
        Authenticate a user by email or username.
        
        Returns:
            Tuple of (success, user_object)
        """
        username = self.validation.clean_text(username)
        password = self.validation.clean_text(password)
        
        user = self.user_manager.authenticate(username, password)
        if user:
            return True, user
        return False, None


class InventoryService:
    """Handles inventory operations."""

    def __init__(self, inventory_manager: InventoryManager):
        """Initialize with an inventory manager."""
        self.inventory = inventory_manager
        self.validation = ValidationService()

    def add_product(
        self,
        name: str,
        category: str,
        price: float,
        stock: int,
        threshold: int
    ) -> Tuple[bool, str]:
        """
        Add a new product to inventory.
        
        Returns:
            Tuple of (success, message)
        """
        valid, msg = self.validation.validate_product_input(
            name, category, price, stock, threshold, self.inventory
        )
        if not valid:
            return False, msg

        product = Product.create(
            name=self.validation.clean_text(name),
            category=self.validation.clean_text(category) or "General",
            price=float(price),
            stock=int(stock),
            threshold=int(threshold)
        )
        
        if self.inventory.add_product(product):
            return True, "Product added successfully."
        return False, "Product could not be added."

    def update_product(
        self,
        product_id: str,
        price: float,
        stock: int,
        threshold: int
    ) -> Tuple[bool, str]:
        """
        Update an existing product.
        
        Returns:
            Tuple of (success, message)
        """
        product = self.inventory.get_product(product_id)
        if not product:
            return False, "Product not found."

        # Validate new values
        if price <= 0:
            return False, "Price must be greater than 0."
        if stock < 0:
            return False, "Stock cannot be negative."
        if threshold < 1:
            return False, "Low stock threshold must be at least 1."

        # Store old values in case we need to rollback
        old_price, old_stock, old_threshold = product.price, product.stock, product.low_stock_threshold

        # Update product
        product.price = float(price)
        product.stock = int(stock)
        product.low_stock_threshold = int(threshold)

        return True, "Product updated successfully."

    def discontinue_product(self, product_id: str) -> Tuple[bool, str]:
        """
        Mark a product as discontinued.
        
        Returns:
            Tuple of (success, message)
        """
        product = self.inventory.get_product(product_id)
        if not product:
            return False, "Product not found."

        product.discontinue()
        return True, "Product marked as discontinued."

    def get_low_stock_report(self) -> List[Product]:
        """Get all low stock items for reporting."""
        return self.inventory.get_low_stock_items(strict=True)

    def get_inventory_value(self) -> float:
        """Get total value of active inventory."""
        return self.inventory.calculate_total_value()


class SalesService:
    """Handles sales operations."""

    def __init__(
        self,
        sales_manager: SalesManager,
        inventory_manager: InventoryManager
    ):
        """Initialize with managers."""
        self.sales = sales_manager
        self.inventory = inventory_manager
        self.validation = ValidationService()

    def record_sale(
        self,
        product_id: str,
        quantity: int,
        sold_by: str
    ) -> Tuple[bool, str]:
        """
        Record a sale and update inventory.
        
        Returns:
            Tuple of (success, message)
        """
        product = self.inventory.get_product(product_id)
        valid, msg = self.validation.validate_sale(product, quantity)
        if not valid:
            return False, msg

        # Apply the sale
        if not product.apply_sale(int(quantity)):
            return False, "Could not apply sale to inventory."

        # Record the sale
        sale = Sale.create(
            product_name=product.name,
            quantity=int(quantity),
            unit_price=product.price,
            sold_by=sold_by
        )

        if self.sales.record_sale(sale):
            return True, "Sale logged and stock updated successfully."
        
        # Rollback inventory if sale recording failed
        product.stock += int(quantity)
        return False, "Sale could not be saved."

    def get_employee_sales(self, employee: str) -> List[Sale]:
        """Get all sales recorded by an employee."""
        return self.sales.get_sales_by_employee(employee)

    def get_revenue_report(self) -> dict:
        """Get revenue report data."""
        return {
            "total_sales": self.sales.get_sales_count(),
            "total_revenue": self.sales.get_total_revenue(),
            "average_sale": self.sales.get_average_sale_value(),
        }


class FlagService:
    """Handles low-stock flag operations."""

    def __init__(
        self,
        flag_manager: FlagManager,
        inventory_manager: InventoryManager
    ):
        """Initialize with managers."""
        self.flags = flag_manager
        self.inventory = inventory_manager
        self.validation = ValidationService()

    def submit_flag(
        self,
        product_name: str,
        note: str,
        flagged_by: str
    ) -> Tuple[bool, str]:
        """
        Submit a low-stock flag.
        
        Returns:
            Tuple of (success, message)
        """
        valid, msg = self.validation.validate_flag_note(note)
        if not valid:
            return False, msg

        flag = Flag.create(
            product_name=product_name,
            flagged_by=flagged_by,
            note=note
        )

        if self.flags.submit_flag(flag):
            return True, "Low-stock flag submitted."
        return False, "Flag could not be saved."

    def get_low_stock_items(self) -> List[Product]:
        """Get items below low stock threshold."""
        return self.inventory.get_low_stock_items(strict=False)

    def get_employee_flags(self, employee: str) -> List[Flag]:
        """Get all flags submitted by an employee."""
        return self.flags.get_flags_by_employee(employee)

    def get_open_flags(self) -> List[Flag]:
        """Get all open flags."""
        return self.flags.get_open_flags()

    def get_flag_report(self) -> dict:
        """Get flag report data."""
        open_flags = self.flags.get_open_flags()
        return {
            "total_flags": len(self.flags.flags),
            "open_flags": len(open_flags),
            "resolved_flags": len(self.flags.flags) - len(open_flags),
        }
