"""
Data models and business entities for the inventory management system.
Defines User, Product, Sale, Flag, and manager classes using OOP principles.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
from enum import Enum
import uuid
from datetime import datetime


class UserRole(Enum):
    """Enumeration of user roles in the system."""
    OWNER = "owner"
    EMPLOYEE = "employee"


class SaleStatus(Enum):
    """Status of a sale record."""
    COMPLETED = "completed"
    PENDING = "pending"


class FlagStatus(Enum):
    """Status of a low-stock flag."""
    OPEN = "open"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class User:
    """Represents a user account in the system."""
    user_id: int
    email: str
    password: str
    role: str
    username: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        self.email = self.email.strip()
        self.username = self.username.strip()
        if not self.username:
            self.username = self.email.split("@")[0] if "@" in self.email else self.email

    def to_dict(self) -> dict:
        """Convert user to dictionary for JSON serialization."""
        return asdict(self)

    @property
    def login_name(self) -> str:
        """Get the login email used for authentication."""
        return self.email

    def can_access_page(self, page: str) -> bool:
        """Determine if user has access to a specific page."""
        owner_pages = ["owner_inventory", "owner_reports"]
        employee_pages = ["employee_catalog", "employee_sales", "employee_flags"]
        assistant_pages = ["assistant"]

        if self.role == UserRole.OWNER.value:
            return page in owner_pages + assistant_pages
        else:
            return page in employee_pages + assistant_pages

    def is_owner(self) -> bool:
        """Check if user is an owner."""
        return self.role == UserRole.OWNER.value

    def is_employee(self) -> bool:
        """Check if user is an employee."""
        return self.role == UserRole.EMPLOYEE.value


@dataclass
class Product:
    """Represents an inventory product."""
    product_id: str
    name: str
    category: str
    price: float
    stock: int
    low_stock_threshold: int
    discontinued: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def create(cls, name: str, category: str, price: float, stock: int, threshold: int) -> "Product":
        """Factory method to create a new product."""
        return cls(
            product_id=f"p-{uuid.uuid4().hex[:8]}",
            name=name,
            category=category,
            price=price,
            stock=stock,
            low_stock_threshold=threshold,
        )

    def to_dict(self) -> dict:
        """Convert product to dictionary for JSON serialization."""
        return asdict(self)

    def is_low_stock(self) -> bool:
        """Check if product is below low stock threshold."""
        return self.stock <= self.low_stock_threshold

    def is_active(self) -> bool:
        """Check if product is not discontinued."""
        return not self.discontinued

    def apply_sale(self, quantity: int) -> bool:
        """Reduce stock by quantity sold. Returns True if successful."""
        if quantity > self.stock or quantity < 1:
            return False
        self.stock -= quantity
        return True

    def update_stock(self, new_stock: int) -> bool:
        """Update stock level."""
        if new_stock < 0:
            return False
        self.stock = new_stock
        return True

    def discontinue(self) -> None:
        """Mark product as discontinued."""
        self.discontinued = True


@dataclass
class Sale:
    """Represents a sale transaction."""
    sale_id: str
    product_name: str
    quantity: int
    unit_price: float
    total: float
    sold_by: str
    status: str = SaleStatus.COMPLETED.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def create(cls, product_name: str, quantity: int, unit_price: float, sold_by: str) -> "Sale":
        """Factory method to create a new sale."""
        return cls(
            sale_id=f"s-{uuid.uuid4().hex[:8]}",
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            total=unit_price * quantity,
            sold_by=sold_by,
        )

    def to_dict(self) -> dict:
        """Convert sale to dictionary for JSON serialization."""
        return asdict(self)

    def get_revenue(self) -> float:
        """Get revenue from this sale."""
        return self.total


@dataclass
class Flag:
    """Represents a low-stock flag or inventory alert."""
    flag_id: str
    product_name: str
    flagged_by: str
    note: str
    status: str = FlagStatus.OPEN.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def create(cls, product_name: str, flagged_by: str, note: str) -> "Flag":
        """Factory method to create a new flag."""
        return cls(
            flag_id=f"f-{uuid.uuid4().hex[:8]}",
            product_name=product_name,
            flagged_by=flagged_by,
            note=note or "No additional note provided.",
        )

    def to_dict(self) -> dict:
        """Convert flag to dictionary for JSON serialization."""
        return asdict(self)

    def resolve(self) -> None:
        """Mark flag as resolved."""
        self.status = FlagStatus.RESOLVED.value

    def acknowledge(self) -> None:
        """Mark flag as acknowledged."""
        self.status = FlagStatus.ACKNOWLEDGED.value

    def is_open(self) -> bool:
        """Check if flag is still open."""
        return self.status == FlagStatus.OPEN.value


class InventoryManager:
    """Manages inventory operations."""

    def __init__(self, products: List[Product]):
        """Initialize with a list of products."""
        self.products = products

    def add_product(self, product: Product) -> bool:
        """Add a new product to inventory."""
        if self.product_exists(product.name):
            return False
        self.products.append(product)
        return True

    def get_product(self, product_id: str) -> Optional[Product]:
        """Retrieve a product by ID."""
        return next((p for p in self.products if p.product_id == product_id), None)

    def get_product_by_name(self, name: str) -> Optional[Product]:
        """Retrieve a product by name (case-insensitive)."""
        return next((p for p in self.products if p.name.lower() == name.lower()), None)

    def product_exists(self, name: str) -> bool:
        """Check if a product with given name exists (active only)."""
        return any(p.name.lower() == name.lower() and p.is_active() for p in self.products)

    def get_active_products(self) -> List[Product]:
        """Get all active (non-discontinued) products."""
        return [p for p in self.products if p.is_active()]

    def get_low_stock_items(self, strict: bool = False) -> List[Product]:
        """Get products below or at low stock threshold."""
        active = self.get_active_products()
        if strict:
            return [p for p in active if p.stock < p.low_stock_threshold]
        return [p for p in active if p.is_low_stock()]

    def get_discontinued_products(self) -> List[Product]:
        """Get all discontinued products."""
        return [p for p in self.products if p.discontinued]

    def get_catalog_for_employee(self, search_term: str = "") -> List[Product]:
        """Get filtered active products for employee view."""
        active = self.get_active_products()
        if not search_term:
            return active
        search_lower = search_term.lower()
        return [p for p in active if search_lower in p.name.lower() or search_lower in p.category.lower()]

    def calculate_total_value(self) -> float:
        """Calculate total inventory value."""
        return sum(p.price * p.stock for p in self.get_active_products())


class SalesManager:
    """Manages sales operations."""

    def __init__(self, sales: List[Sale]):
        """Initialize with a list of sales."""
        self.sales = sales

    def record_sale(self, sale: Sale) -> bool:
        """Record a new sale."""
        self.sales.append(sale)
        return True

    def get_sales_by_employee(self, employee: str) -> List[Sale]:
        """Get all sales recorded by a specific employee."""
        return [s for s in self.sales if s.sold_by == employee]

    def get_total_revenue(self) -> float:
        """Calculate total revenue from all sales."""
        return sum(s.total for s in self.sales)

    def get_sales_count(self) -> int:
        """Get total number of sales."""
        return len(self.sales)

    def get_average_sale_value(self) -> float:
        """Get average sale value."""
        if not self.sales:
            return 0.0
        return self.get_total_revenue() / len(self.sales)


class FlagManager:
    """Manages low-stock flags."""

    def __init__(self, flags: List[Flag]):
        """Initialize with a list of flags."""
        self.flags = flags

    def submit_flag(self, flag: Flag) -> bool:
        """Submit a new low-stock flag."""
        self.flags.append(flag)
        return True

    def get_flags_by_employee(self, employee: str) -> List[Flag]:
        """Get all flags submitted by a specific employee."""
        return [f for f in self.flags if f.flagged_by == employee]

    def get_open_flags(self) -> List[Flag]:
        """Get all open (unresolved) flags."""
        return [f for f in self.flags if f.is_open()]

    def get_flags_for_product(self, product_name: str) -> List[Flag]:
        """Get all flags for a specific product."""
        return [f for f in self.flags if f.product_name == product_name]

    def resolve_flag(self, flag_id: str) -> bool:
        """Mark a flag as resolved."""
        flag = next((f for f in self.flags if f.flag_id == flag_id), None)
        if flag:
            flag.resolve()
            return True
        return False

    def get_open_flag_count(self) -> int:
        """Get count of open flags."""
        return len(self.get_open_flags())


class UserManager:
    """Manages user accounts."""

    def __init__(self, users: List[User]):
        """Initialize with a list of users."""
        self.users = users

    def add_user(self, user: User) -> bool:
        """Add a new user to the system."""
        if self.email_exists(user.email) or self.username_exists(user.username):
            return False
        self.users.append(user)
        return True

    def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID."""
        return next((u for u in self.users if u.user_id == user_id), None)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by username (case-insensitive)."""
        return next((u for u in self.users if u.username.lower() == username.lower()), None)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email (case-insensitive)."""
        return next((u for u in self.users if u.email.lower() == email.lower()), None)

    def get_user_by_identifier(self, identifier: str) -> Optional[User]:
        """Retrieve a user by either email or username."""
        identifier = identifier.strip()
        user = self.get_user_by_email(identifier)
        if user:
            return user
        return self.get_user_by_username(identifier)

    def user_exists(self, username: str) -> bool:
        """Check if a user with given identifier exists."""
        return self.get_user_by_identifier(username) is not None

    def email_exists(self, email: str) -> bool:
        """Check if a user with given email exists."""
        return self.get_user_by_email(email) is not None

    def username_exists(self, username: str) -> bool:
        """Check if a user with given display username exists."""
        return self.get_user_by_username(username) is not None

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user and return the user object if valid."""
        user = self.get_user_by_identifier(username)
        if user and user.password == password:
            return user
        return None

    def get_owners(self) -> List[User]:
        """Get all owner-role users."""
        return [u for u in self.users if u.is_owner()]

    def get_employees(self) -> List[User]:
        """Get all employee-role users."""
        return [u for u in self.users if u.is_employee()]

    def get_user_count(self) -> int:
        """Get total number of users."""
        return len(self.users)
