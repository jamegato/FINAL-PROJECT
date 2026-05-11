from pathlib import Path
import json
import os
import time


class DataAccess:
    def __init__(self):
        self.paths = {
            "inventory": Path("inventory.json"),
            "sales": Path("sales.json"),
            "flags": Path("flags.json"),
            "users": Path("users.json"),
        }
        self.lock_timeout_seconds = 2.0
        self.lock_poll_seconds = 0.05

    def _lock_path(self, path):
        return Path(f"{path}.lock")

    def _acquire_lock(self, path):
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

    def _release_lock(self, lock_path):
        if lock_path is None:
            return
        try:
            if lock_path.exists():
                lock_path.unlink()
        except OSError:
            return

    def load(self, name):
        path = self.paths[name]
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

    def save(self, name, data):
        path = self.paths[name]
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