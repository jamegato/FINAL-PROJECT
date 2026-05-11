"""
Data access layer for loading and saving application data.
Handles JSON file I/O with file locking and error recovery.
"""

from pathlib import Path
import json
import os
import time
from typing import Tuple, List, Any, Optional
from models import User, Product, Sale, Flag


class DataLayer:
    """Manages all data persistence operations."""

    def __init__(self, data_dir: str = "."):
        """
        Initialize the data layer.
        
        Args:
            data_dir: Directory where JSON files are stored
        """
        self.data_dir = Path(data_dir)
        self.paths = {
            "inventory": self.data_dir / "inventory.json",
            "sales": self.data_dir / "sales.json",
            "flags": self.data_dir / "flags.json",
            "users": self.data_dir / "users.json",
        }
        self.lock_timeout_seconds = 2.0
        self.lock_poll_seconds = 0.05

    def _lock_path(self, path: Path) -> Path:
        """Get the lock file path for a data file."""
        return Path(f"{path}.lock")

    def _acquire_lock(self, path: Path) -> Tuple[bool, Optional[Path]]:
        """
        Acquire a file lock to prevent concurrent writes.
        
        Returns:
            Tuple of (success, lock_path)
        """
        lock_path = self._lock_path(path)
        started = time.time()

        while True:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return True, lock_path
            except FileExistsError:
                if time.time() - started >= self.lock_timeout_seconds:
                    return False, None
                time.sleep(self.lock_poll_seconds)
            except OSError:
                return False, None

    def _release_lock(self, lock_path: Optional[Path]) -> None:
        """Release a file lock."""
        if lock_path is None:
            return
        try:
            if lock_path.exists():
                lock_path.unlink()
        except OSError:
            return

    def load(self, name: str) -> Tuple[bool, List[Any], str]:
        """
        Load a JSON data file.
        
        Args:
            name: Name of the dataset (inventory, sales, flags, users)
            
        Returns:
            Tuple of (success, data, error_message)
        """
        path = self.paths.get(name)
        if path is None:
            return False, [], f"Unknown dataset: {name}"

        if not path.exists():
            return True, [], ""

        lock_ok, lock_path = self._acquire_lock(path)
        if not lock_ok:
            return False, [], "Storage is currently busy. Please retry in a moment."

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return True, data, ""
                return False, [], "Data format is invalid."
        except json.JSONDecodeError:
            return False, [], "File content is not valid JSON."
        except OSError as exc:
            return False, [], f"File could not be read ({exc})."
        finally:
            self._release_lock(lock_path)

    def save(self, name: str, data: List[Any]) -> Tuple[bool, str]:
        """
        Save data to a JSON file.
        
        Args:
            name: Name of the dataset (inventory, sales, flags, users)
            data: List of objects to save
            
        Returns:
            Tuple of (success, error_message)
        """
        path = self.paths.get(name)
        if path is None:
            return False, f"Unknown dataset: {name}"

        lock_ok, lock_path = self._acquire_lock(path)
        if not lock_ok:
            return False, "Storage is currently busy. Please retry in a moment."

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True, ""
        except OSError as exc:
            return False, f"File could not be saved ({exc})."
        finally:
            self._release_lock(lock_path)

    def load_users(self) -> Tuple[bool, List[User], str]:
        """Load users from file and convert to User objects."""
        ok, data, error = self.load("users")
        if not ok:
            return False, [], error
        
        try:
            users = [
                User(
                    user_id=item.get("user_id", 0),
                    username=item.get("username", ""),
                    password=item.get("password", ""),
                    role=item.get("role", "employee"),
                    created_at=item.get("created_at", ""),
                )
                for item in data
            ]
            return True, users, ""
        except Exception as e:
            return False, [], f"Error parsing users: {str(e)}"

    def save_users(self, users: List[User]) -> Tuple[bool, str]:
        """Save users to file."""
        data = [u.to_dict() for u in users]
        return self.save("users", data)

    def load_products(self) -> Tuple[bool, List[Product], str]:
        """Load products from file and convert to Product objects."""
        ok, data, error = self.load("inventory")
        if not ok:
            return False, [], error
        
        try:
            products = [
                Product(
                    product_id=item.get("product_id", ""),
                    name=item.get("name", ""),
                    category=item.get("category", ""),
                    price=float(item.get("price", 0.0)),
                    stock=int(item.get("stock", 0)),
                    low_stock_threshold=int(item.get("low_stock_threshold", 5)),
                    discontinued=item.get("discontinued", False),
                    created_at=item.get("created_at", ""),
                )
                for item in data
            ]
            return True, products, ""
        except Exception as e:
            return False, [], f"Error parsing products: {str(e)}"

    def save_products(self, products: List[Product]) -> Tuple[bool, str]:
        """Save products to file."""
        data = [p.to_dict() for p in products]
        return self.save("inventory", data)

    def load_sales(self) -> Tuple[bool, List[Sale], str]:
        """Load sales from file and convert to Sale objects."""
        ok, data, error = self.load("sales")
        if not ok:
            return False, [], error
        
        try:
            sales = [
                Sale(
                    sale_id=item.get("sale_id", ""),
                    product_name=item.get("product_name", ""),
                    quantity=int(item.get("quantity", 0)),
                    unit_price=float(item.get("unit_price", 0.0)),
                    total=float(item.get("total", 0.0)),
                    sold_by=item.get("sold_by", ""),
                    status=item.get("status", "completed"),
                    created_at=item.get("created_at", ""),
                )
                for item in data
            ]
            return True, sales, ""
        except Exception as e:
            return False, [], f"Error parsing sales: {str(e)}"

    def save_sales(self, sales: List[Sale]) -> Tuple[bool, str]:
        """Save sales to file."""
        data = [s.to_dict() for s in sales]
        return self.save("sales", data)

    def load_flags(self) -> Tuple[bool, List[Flag], str]:
        """Load flags from file and convert to Flag objects."""
        ok, data, error = self.load("flags")
        if not ok:
            return False, [], error
        
        try:
            flags = [
                Flag(
                    flag_id=item.get("flag_id", ""),
                    product_name=item.get("product_name", ""),
                    flagged_by=item.get("flagged_by", ""),
                    note=item.get("note", ""),
                    status=item.get("status", "open"),
                    created_at=item.get("created_at", ""),
                )
                for item in data
            ]
            return True, flags, ""
        except Exception as e:
            return False, [], f"Error parsing flags: {str(e)}"

    def save_flags(self, flags: List[Flag]) -> Tuple[bool, str]:
        """Save flags to file."""
        data = [f.to_dict() for f in flags]
        return self.save("flags", data)
