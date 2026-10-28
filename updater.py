"""GitHub version checks and the restartable application updater."""

import json
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


GITHUB_REPOSITORY = "vinetailgames/FocusQuest"
GITHUB_BRANCH = "main"
CHECK_INTERVAL_SECONDS = 120
REQUEST_TIMEOUT_SECONDS = 12
UPDATE_STATE_RELATIVE_PATH = Path("data") / "update_state.json"
PRESERVED_DIRECTORY_NAMES = {".git", ".venv", "venv", "env", "data", "__pycache__"}


def _read_version_file(path):
    with open(path, "r", encoding="utf-8") as version_file:
        payload = json.load(version_file)
    version = payload.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("version.json must contain a non-empty 'version' string")
    return version.strip()


def _read_update_state(root):
    state_path = root / UPDATE_STATE_RELATIVE_PATH
    try:
        with open(state_path, "r", encoding="utf-8") as state_file:
            state = json.load(state_file)
        commit = state.get("commit")
        return commit if isinstance(commit, str) and commit else None
    except (OSError, ValueError, AttributeError):
        return None


def _write_update_state(root, version, commit):
    state_path = root / UPDATE_STATE_RELATIVE_PATH
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = state_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as state_file:
        json.dump({"version": version, "commit": commit}, state_file, indent=2)
    os.replace(temp_path, state_path)


def _git_head(root):
    if not (root / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=3
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _is_ancestor(root, ancestor, descendant):
    if not (root / ".git").exists():
        return False
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=root,
            capture_output=True,
            timeout=3
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _compare_versions(left, right):
    """Compare numeric version components, such as v.0.2 and v.0.10."""
    import re

    left_parts = [int(part) for part in re.findall(r"\d+", left)]
    right_parts = [int(part) for part in re.findall(r"\d+", right)]
    if not left_parts or not right_parts:
        return 0
    width = max(len(left_parts), len(right_parts))
    left_parts.extend([0] * (width - len(left_parts)))
    right_parts.extend([0] * (width - len(right_parts)))
    return (left_parts > right_parts) - (left_parts < right_parts)


def _request_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "FocusQuest-Updater",
            "Cache-Control": "no-cache, no-store",
            "Pragma": "no-cache"
        }
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _latest_github_version(local_version):
    commit_url = (
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}"
        f"/commits/{GITHUB_BRANCH}?nocache={time.time_ns()}"
    )
    commit_payload = _request_json(commit_url)
    commit = commit_payload.get("sha")
    if not isinstance(commit, str) or not commit:
        raise ValueError("GitHub did not return the latest commit SHA")

    version_url = (
        f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/"
        f"{commit}/version.json"
    )
    try:
        version_payload = _request_json(version_url)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        # Older GitHub revisions may predate the addition of version.json.
        return local_version, commit
    version = version_payload.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("GitHub version.json has no version")
    return version.strip(), commit


def _latest_binary_update(local_version):
    """Return a newer version and its repository commit for frozen builds."""
    version, commit = _latest_github_version(local_version)
    if _compare_versions(version, local_version) <= 0:
        return version, None
    return version, commit


class UpdateService:
    """Poll GitHub off-thread and expose a small, thread-safe status snapshot."""

    def __init__(self, app_root, check_interval=CHECK_INTERVAL_SECONDS):
        self.app_root = Path(app_root).resolve()
        self.is_frozen = bool(getattr(sys, "frozen", False))
        self.local_version = _read_version_file(self.app_root / "version.json")
        self.local_commit = _read_update_state(self.app_root)
        if self.local_commit is None:
            self.local_commit = _git_head(self.app_root)

        self.check_interval = check_interval
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._snapshot = {
            "connection_available": None,
            "check_error": None,
            "local_version": self.local_version,
            "available_version": None,
            "available_commit": None,
            "available_asset_url": None
        }
        self._thread = threading.Thread(
            target=self._run,
            name="FocusQuestUpdateChecker",
            daemon=True
        )

    def start(self):
        self._thread.start()

    def request_check(self):
        self._wake.set()

    def stop(self):
        self._stop.set()
        self._wake.set()

    def snapshot(self):
        with self._lock:
            return self._snapshot.copy()

    def _run(self):
        while not self._stop.is_set():
            self._check_once()
            self._wake.wait(self.check_interval)
            self._wake.clear()

    def _check_once(self):
        try:
            if self.is_frozen:
                latest_version, latest_commit = _latest_binary_update(
                    self.local_version
                )
                with self._lock:
                    self._snapshot["connection_available"] = True
                    self._snapshot["check_error"] = None
                    self._snapshot["available_version"] = (
                        latest_version if latest_commit else None
                    )
                    self._snapshot["available_commit"] = latest_commit
                    self._snapshot["available_asset_url"] = None
                return

            latest_version, latest_commit = _latest_github_version(self.local_version)
            if self.local_commit is None and latest_version == self.local_version:
                # A source ZIP has no Git metadata. Record its first online baseline.
                self.local_commit = latest_commit
                try:
                    _write_update_state(self.app_root, self.local_version, latest_commit)
                except OSError:
                    pass

            remote_is_older = _compare_versions(
                latest_version, self.local_version
            ) < 0
            local_is_ahead = (
                self.local_commit is not None
                and _is_ancestor(
                    self.app_root, latest_commit, self.local_commit
                )
            )
            update_available = (
                not remote_is_older
                and not local_is_ahead
                and (
                    latest_version != self.local_version
                    or (
                        self.local_commit is not None
                        and latest_commit != self.local_commit
                    )
                )
            )
            with self._lock:
                self._snapshot["connection_available"] = True
                self._snapshot["check_error"] = None
                self._snapshot["available_version"] = (
                    latest_version if update_available else None
                )
                self._snapshot["available_commit"] = (
                    latest_commit if update_available else None
                )
                self._snapshot["available_asset_url"] = None
        except urllib.error.HTTPError as error:
            with self._lock:
                self._snapshot["connection_available"] = True
                self._snapshot["check_error"] = (
                    f"GitHub returned HTTP {error.code}"
                )
                self._snapshot["available_version"] = None
                self._snapshot["available_commit"] = None
                self._snapshot["available_asset_url"] = None
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            with self._lock:
                self._snapshot["connection_available"] = False
                self._snapshot["check_error"] = str(error)
        except Exception as error:
            with self._lock:
                self._snapshot["connection_available"] = True
                self._snapshot["check_error"] = str(error)
                self._snapshot["available_version"] = None
                self._snapshot["available_commit"] = None
                self._snapshot["available_asset_url"] = None


def launch_installer(app_root, version, commit=None, asset_url=None):
    """Start a detached helper that waits for this app to exit before updating."""
    if getattr(sys, "frozen", False):
        return _launch_binary_installer(app_root, version, commit)

    helper_fd, helper_path = tempfile.mkstemp(
        prefix="focusquest_updater_", suffix=".py"
    )
    os.close(helper_fd)
    try:
        shutil.copy2(Path(__file__).resolve(), helper_path)
        command = [
            sys.executable,
            helper_path,
            "--install",
            str(Path(app_root).resolve()),
            version,
            commit,
            str(os.getpid())
        ]
        popen_options = {
            "cwd": str(Path(app_root).resolve()),
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True
        }
        if os.name == "nt":
            popen_options["creationflags"] = (
                getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
        else:
            popen_options["start_new_session"] = True
        subprocess.Popen(command, **popen_options)
        return True
    except Exception:
        try:
            os.remove(helper_path)
        except OSError:
            pass
        raise


def _launch_binary_installer(app_root, version, commit):
    if not commit:
        raise ValueError("GitHub did not provide a commit for this update")

    app_root = Path(app_root).resolve()
    helper_source = app_root / "FocusQuestUpdater.exe"
    if not helper_source.is_file():
        raise FileNotFoundError("FocusQuestUpdater.exe is missing from the app folder")

    app_key = hashlib.sha256(str(app_root).casefold().encode("utf-8")).hexdigest()[:12]
    helper_directory = app_root / ".focusquest-updater"
    helper_directory.mkdir(parents=True, exist_ok=True)
    helper_path = helper_directory / f"FocusQuestUpdater-{app_key}.exe"
    temporary_copy = helper_directory / f".FocusQuestUpdater-{os.getpid()}.tmp"
    try:
        shutil.copy2(helper_source, temporary_copy)
        try:
            os.replace(temporary_copy, helper_path)
        except OSError:
            # A previous helper can briefly remain locked while it relaunches
            # the game. In that case, use the already-staged helper copy.
            if not helper_path.is_file():
                raise
    except Exception:
        try:
            temporary_copy.unlink()
        except OSError:
            pass
        raise

    command = [
        str(helper_path),
        "--install-binary",
        str(app_root),
        version,
        commit,
        str(os.getpid())
    ]
    if os.name == "nt":
        import ctypes

        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        shell_execute = shell32.ShellExecuteW
        shell_execute.argtypes = (
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_int
        )
        shell_execute.restype = ctypes.c_void_p
        result = shell_execute(
            None,
            "open",
            str(helper_path),
            subprocess.list2cmdline(command[1:]),
            str(app_root),
            0
        )
        if result is None or int(result) <= 32:
            shell_errors = {
                2: "The updater executable could not be found.",
                3: "The updater path could not be found.",
                5: "Windows denied permission to start the updater.",
                8: "Windows ran out of memory while starting the updater.",
                26: "Windows could not start the updater because of a sharing violation.",
                27: "The updater file association is incomplete.",
                28: "Windows timed out while starting the updater.",
                29: "Windows could not complete the updater launch.",
                30: "The updater launch was blocked by another process.",
                31: "Windows could not find an application to open the updater.",
                32: "A required updater library could not be found."
            }
            error_code = int(result or 0)
            shell_error = OSError(
                f"{shell_errors.get(error_code, 'Windows could not start the updater.')} "
                f"(ShellExecuteW code {error_code})"
            )
            try:
                subprocess.Popen(
                    command,
                    cwd=str(app_root),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                    creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
                )
            except OSError as process_error:
                raise OSError(
                    f"{shell_error} Direct process launch also failed: "
                    f"{process_error}"
                ) from process_error
            return True
        return True

    popen_options = {
        "cwd": str(app_root),
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
        "start_new_session": True
    }
    subprocess.Popen(command, **popen_options)
    return True


def _wait_for_parent_exit(parent_pid):
    deadline = time.monotonic() + 60
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = (
            wintypes.DWORD, wintypes.BOOL, wintypes.DWORD
        )
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        synchronize = 0x00100000
        process_handle = kernel32.OpenProcess(synchronize, False, parent_pid)
        if not process_handle:
            error_code = ctypes.get_last_error()
            if error_code == 87:  # The process has already exited.
                return
            raise OSError(error_code, ctypes.FormatError(error_code))
        try:
            while time.monotonic() < deadline:
                wait_result = kernel32.WaitForSingleObject(process_handle, 200)
                if wait_result == 0:
                    return
        finally:
            kernel32.CloseHandle(process_handle)
        raise TimeoutError("Focus Quest did not close in time for the update")

    while time.monotonic() < deadline:
        try:
            os.kill(parent_pid, 0)
        except ProcessLookupError:
            return
        except PermissionError:
            pass
        except OSError:
            return
        time.sleep(0.2)
    raise TimeoutError("Focus Quest did not close in time for the update")


def _safe_archive_path(member_name, archive_root):
    path = PurePosixPath(member_name.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or not path.parts:
        return None
    if path.parts[0] != archive_root or len(path.parts) == 1:
        return None
    relative = Path(*path.parts[1:])
    if any(part in PRESERVED_DIRECTORY_NAMES for part in relative.parts):
        return None
    if any(part.startswith(".focusquest_update_") for part in relative.parts):
        return None
    if relative.is_absolute() or relative.drive:
        return None
    return relative


def _download_archive(commit, destination):
    if (
        not isinstance(commit, str)
        or len(commit) not in (40, 64)
        or any(character not in "0123456789abcdefABCDEF" for character in commit)
    ):
        raise ValueError("GitHub returned an invalid commit SHA")
    archive_url = (
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/zipball/{commit}"
    )
    request = urllib.request.Request(
        archive_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "FocusQuest-Updater"
        }
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        with open(destination, "wb") as archive_file:
            shutil.copyfileobj(response, archive_file)


def _extract_dist_bundle(archive_path, extracted_root, expected_version):
    """Extract only dist/FocusQuest from a GitHub commit ZIP archive."""
    extracted_root.mkdir(parents=True)
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        root_names = {
            PurePosixPath(member.filename.replace("\\", "/")).parts[0]
            for member in members
            if PurePosixPath(member.filename.replace("\\", "/")).parts
        }
        if len(root_names) != 1:
            raise ValueError("The GitHub archive has an unexpected layout")
        archive_root = next(iter(root_names))

        for member in members:
            member_path = PurePosixPath(member.filename.replace("\\", "/"))
            if not member_path.parts:
                continue
            if (
                member_path.is_absolute()
                or ".." in member_path.parts
                or any(":" in part for part in member_path.parts)
            ):
                raise ValueError("The update archive contains an unsafe path")
            if member_path.parts[0] != archive_root:
                raise ValueError("The GitHub archive has an unexpected layout")
            if member_path.parts[1:3] != ("dist", "FocusQuest"):
                continue
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError("The update archive contains a symbolic link")

        copied_bundle_entries = 0
        for member in members:
            member_path = PurePosixPath(member.filename.replace("\\", "/"))
            if member_path.parts[1:3] != ("dist", "FocusQuest"):
                continue
            relative_parts = member_path.parts[3:]
            if not relative_parts:
                continue
            if relative_parts[0] == "data":
                continue
            if any(part.startswith(".focusquest_update_") for part in relative_parts):
                raise ValueError("The update archive contains an unsafe path")
            relative = Path(*relative_parts)
            if relative.is_absolute() or relative.drive:
                raise ValueError("The update archive contains an unsafe path")
            destination = extracted_root / relative
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, open(destination, "wb") as output:
                shutil.copyfileobj(source, output)
            copied_bundle_entries += 1

        if copied_bundle_entries == 0:
            raise ValueError("GitHub does not contain a dist/FocusQuest build")

    version_path = extracted_root / "version.json"
    if not version_path.is_file() or _read_version_file(version_path) != expected_version:
        raise ValueError("The downloaded release does not match its version tag")
    if not (extracted_root / "FocusQuest.exe").is_file():
        raise ValueError("The downloaded release is missing FocusQuest.exe")
    if not (extracted_root / "FocusQuestUpdater.exe").is_file():
        raise ValueError("The downloaded release is missing FocusQuestUpdater.exe")
    if not (extracted_root / "_internal").is_dir():
        raise ValueError("The downloaded release is missing its game files")


def _apply_binary_release(app_root, extracted_root, staging_root):
    paths_to_replace = (
        Path("_internal"),
        Path("FocusQuest.exe"),
        Path("FocusQuestUpdater.exe"),
        Path("version.json")
    )
    backup_root = staging_root / "backup"
    changes = []
    try:
        for relative in paths_to_replace:
            source = extracted_root / relative
            target = app_root / relative
            backup = backup_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            had_target = target.exists()
            if had_target:
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, backup)
            changes.append((target, backup if had_target else None))
            os.replace(source, target)
    except Exception:
        for target, backup in reversed(changes):
            if backup is not None and backup.exists():
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                os.replace(backup, target)
            elif target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
        raise


def _apply_archive(app_root, archive_path, expected_version, expected_commit, staging_root):
    extracted_root = staging_root / "extracted"
    extracted_root.mkdir()
    changes = []

    with zipfile.ZipFile(archive_path) as archive:
        root_names = {
            PurePosixPath(member.filename.replace("\\", "/")).parts[0]
            for member in archive.infolist()
            if PurePosixPath(member.filename.replace("\\", "/")).parts
        }
        if len(root_names) != 1:
            raise ValueError("The GitHub archive has an unexpected layout")
        archive_root = next(iter(root_names))

        for member in archive.infolist():
            relative = _safe_archive_path(member.filename, archive_root)
            if relative is None:
                continue
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError("The GitHub archive contains a symbolic link")
            destination = extracted_root / relative
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, open(destination, "wb") as output:
                shutil.copyfileobj(source, output)

    archived_version_path = extracted_root / "version.json"
    archived_version = (
        _read_version_file(archived_version_path)
        if archived_version_path.exists()
        else expected_version
    )
    if archived_version != expected_version:
        raise ValueError("The GitHub version changed before installation")

    try:
        for staged_file in extracted_root.rglob("*"):
            if not staged_file.is_file():
                continue
            relative = staged_file.relative_to(extracted_root)
            target = app_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)

            backup = staging_root / "backup" / relative
            existed = target.exists()
            if existed:
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)

            replacement = target.with_name(
                f".focusquest_update_{staging_root.name}_{target.name}"
            )
            try:
                shutil.copy2(staged_file, replacement)
                os.replace(replacement, target)
            except Exception:
                try:
                    replacement.unlink()
                except OSError:
                    pass
                raise
            changes.append((target, backup if existed else None))
    except Exception:
        for target, backup in reversed(changes):
            if backup is not None and backup.exists():
                os.replace(backup, target)
            else:
                try:
                    target.unlink()
                except OSError:
                    pass
        raise

    _write_update_state(app_root, expected_version, expected_commit)


def _launch_application(app_root):
    if getattr(sys, "frozen", False):
        command = [str(app_root / "FocusQuest.exe")]
    else:
        command = [sys.executable, str(app_root / "main.py")]
    popen_options = {
        "cwd": str(app_root),
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True
    }
    if os.name == "nt":
        popen_options["creationflags"] = (
            getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )
    else:
        popen_options["start_new_session"] = True
    subprocess.Popen(command, **popen_options)


def _show_install_error(message):
    try:
        import tkinter
        from tkinter import messagebox

        window = tkinter.Tk()
        window.withdraw()
        messagebox.showerror("Focus Quest update failed", message, parent=window)
        window.destroy()
    except Exception:
        pass


def _run_installer(app_root, version, commit, parent_pid):
    app_root = Path(app_root).resolve()
    staging_root = None
    try:
        _wait_for_parent_exit(parent_pid)
        staging_root = Path(tempfile.mkdtemp(
            prefix=".focusquest_update_", dir=app_root
        ))
        archive_path = staging_root / "github.zip"
        _download_archive(commit, archive_path)
        _apply_archive(
            app_root, archive_path, version, commit, staging_root
        )
    except Exception as error:
        _show_install_error(str(error))
    finally:
        if staging_root is not None:
            shutil.rmtree(staging_root, ignore_errors=True)
        try:
            _launch_application(app_root)
        except Exception as error:
            _show_install_error(f"Could not relaunch Focus Quest: {error}")
        try:
            os.remove(__file__)
        except OSError:
            pass


def _run_binary_installer(app_root, version, commit, parent_pid):
    app_root = Path(app_root).resolve()
    staging_root = None
    try:
        _wait_for_parent_exit(parent_pid)
        staging_root = Path(tempfile.mkdtemp(
            prefix=".focusquest_update_", dir=app_root
        ))
        archive_path = staging_root / "github.zip"
        extracted_root = staging_root / "extracted"
        _download_archive(commit, archive_path)
        _extract_dist_bundle(archive_path, extracted_root, version)
        _apply_binary_release(app_root, extracted_root, staging_root)
        _write_update_state(app_root, version, commit)
    except Exception as error:
        _show_install_error(str(error))
    finally:
        if staging_root is not None:
            shutil.rmtree(staging_root, ignore_errors=True)
        try:
            _launch_application(app_root)
        except Exception as error:
            _show_install_error(f"Could not relaunch Focus Quest: {error}")


if __name__ == "__main__" and len(sys.argv) == 6 and sys.argv[1] == "--install":
    _run_installer(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]))
elif (
    __name__ == "__main__"
    and len(sys.argv) == 6
    and sys.argv[1] == "--install-binary"
):
    _run_binary_installer(
        sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
    )
