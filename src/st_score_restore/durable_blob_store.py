"""Verified content-addressed local blob storage for immutable artifacts."""

from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path
import tempfile

from .durable_store_support import DurableStoreError


class ContentAddressedBlobStore:
    """Store immutable bytes under lowercase SHA-256 paths with private modes."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.prepare_directory(self.root)

    def write(self, digest: str, data: bytes) -> bool:
        path = self.path_for(digest)
        self.prepare_directory(path.parent)
        self._reject_symlink(path, digest)
        if path.exists():
            self.verify_file(path, digest, len(data))
            return False
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{digest}.",
            dir=path.parent,
        )
        temporary = Path(temporary_name)
        try:
            os.chmod(temporary, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            self.set_private_file_mode(path)
            fsync_directory(path.parent)
            self.verify_file(path, digest, len(data))
            return True
        except Exception:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def read(self, digest: str, expected_size: int) -> bytes:
        path = self.path_for(digest)
        self._reject_symlink(path, digest)
        try:
            data = path.read_bytes()
        except FileNotFoundError as error:
            raise DurableStoreError(
                "artifact_blob_missing",
                "Artifact metadata references a missing blob.",
                details={"digest": digest},
            ) from error
        except OSError as error:
            raise DurableStoreError(
                "artifact_blob_unreadable",
                "Artifact blob could not be read.",
                details={"digest": digest, "osError": str(error)},
            ) from error
        self.verify_bytes(data, digest, expected_size)
        return data

    def delete(self, digest: str) -> None:
        path = self.path_for(digest)
        self._reject_symlink(path, digest)
        try:
            path.unlink(missing_ok=True)
            fsync_directory(path.parent)
        except OSError as error:
            raise DurableStoreError(
                "blob_deletion_failed",
                "An unreferenced artifact blob could not be deleted.",
                details={"digest": digest, "osError": str(error)},
            ) from error

    def sweep_orphans(self, live_digests: set[str]) -> list[str]:
        """Delete unreferenced hash blobs and interrupted private temp files."""

        removed: list[str] = []
        for directory in sorted(self.root.iterdir()):
            if directory.is_symlink():
                raise DurableStoreError(
                    "symlink_storage_path_forbidden",
                    "Blob shard directories must not be symbolic links.",
                    details={"pathName": directory.name},
                )
            valid_shard = (
                directory.is_dir()
                and len(directory.name) == 2
                and all(character in "0123456789abcdef" for character in directory.name)
            )
            if not valid_shard:
                raise DurableStoreError(
                    "unexpected_blob_store_entry",
                    "The blob store contains an unexpected entry.",
                    details={"pathName": directory.name},
                )
            for path in sorted(directory.iterdir()):
                if path.is_symlink():
                    raise DurableStoreError(
                        "symlink_blob_path_forbidden",
                        "Artifact blob paths must not be symbolic links.",
                        details={"pathName": path.name},
                    )
                name = path.name
                valid_digest = (
                    len(name) == 64
                    and all(character in "0123456789abcdef" for character in name)
                    and name.startswith(directory.name)
                )
                interrupted_temp = name.startswith(".")
                if path.is_file() and (
                    interrupted_temp or (valid_digest and name not in live_digests)
                ):
                    path.unlink()
                    fsync_directory(directory)
                    removed.append(name)
                elif not path.is_file() or not valid_digest:
                    raise DurableStoreError(
                        "unexpected_blob_store_entry",
                        "The blob store contains an unexpected entry.",
                        details={"pathName": name},
                    )
            try:
                directory.rmdir()
            except OSError:
                pass
        return removed

    def verify_file(self, path: Path, digest: str, expected_size: int) -> None:
        self._reject_symlink(path, digest)
        try:
            data = path.read_bytes()
        except OSError as error:
            raise DurableStoreError(
                "artifact_blob_unreadable",
                "Artifact blob could not be read.",
                details={"digest": digest, "osError": str(error)},
            ) from error
        self.verify_bytes(data, digest, expected_size)

    @staticmethod
    def verify_bytes(data: bytes, digest: str, expected_size: int) -> None:
        actual = hashlib.sha256(data).hexdigest()
        if len(data) != expected_size or not hmac.compare_digest(actual, digest):
            raise DurableStoreError(
                "artifact_blob_corrupt",
                "Artifact blob size or SHA-256 digest is invalid.",
                details={"digest": digest},
            )

    def path_for(self, digest: str) -> Path:
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise DurableStoreError(
                "invalid_blob_digest",
                "Blob paths require a lowercase SHA-256 digest.",
            )
        return self.root / digest[:2] / digest

    @staticmethod
    def prepare_directory(path: Path) -> None:
        if path.exists() and path.is_symlink():
            raise DurableStoreError(
                "symlink_storage_path_forbidden",
                "Durable storage directories must not be symbolic links.",
                details={"pathName": path.name},
            )
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not path.is_dir():
            raise DurableStoreError(
                "invalid_storage_directory",
                "Durable storage path must be a directory.",
                details={"pathName": path.name},
            )
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass

    @staticmethod
    def set_private_file_mode(path: Path) -> None:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

    @staticmethod
    def _reject_symlink(path: Path, digest: str) -> None:
        if path.is_symlink():
            raise DurableStoreError(
                "symlink_blob_path_forbidden",
                "Artifact blob paths must not be symbolic links.",
                details={"digest": digest},
            )


def fsync_directory(path: Path) -> None:
    if not hasattr(os, "O_DIRECTORY"):
        return
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
