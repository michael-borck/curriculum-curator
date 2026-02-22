"""
Git-backed content storage service with per-unit repositories

Each unit gets its own Git repository for:
- Clean isolation between units
- Independent version history
- Easy handover/archive of individual units
- Future collaboration support

All commits are made by the system user with app user info in commit messages.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


class GitContentService:
    """Service for managing content in per-unit Git repositories"""

    def __init__(self, repos_base: str | None = None):
        """
        Initialize Git content service

        Args:
            repos_base: Base path for all unit repositories
                       (defaults to CONTENT_REPOS_PATH env var or ./content_repos)
        """
        default_path = Path.cwd() / "content_repos"
        self.repos_base = Path(
            repos_base or os.getenv("CONTENT_REPOS_PATH", str(default_path))
        )
        self.repos_base.mkdir(parents=True, exist_ok=True)

    def _get_unit_repo_path(self, unit_id: str) -> Path:
        """Get the path to a unit's repository"""
        return self.repos_base / unit_id

    def _ensure_unit_repo(self, unit_id: str) -> Path:
        """
        Ensure Git repository exists for a unit, create if needed.

        Args:
            unit_id: Unit identifier

        Returns:
            Path to unit repository
        """
        repo_path = self._get_unit_repo_path(unit_id)

        if not repo_path.exists():
            repo_path.mkdir(parents=True, exist_ok=True)

        git_dir = repo_path / ".git"
        if not git_dir.exists():
            # Initialize repository
            self._run_git(repo_path, "init")
            self._run_git(repo_path, "config", "user.name", "Curriculum Curator")
            self._run_git(
                repo_path, "config", "user.email", "system@curriculum-curator.local"
            )

            # Create initial structure
            self._create_unit_structure(repo_path)

            # Initial commit
            self._run_git(repo_path, "add", "-A")
            self._run_git(repo_path, "commit", "-m", "Initial unit repository setup")

        return repo_path

    def _create_unit_structure(self, repo_path: Path) -> None:
        """Create the standard folder structure for a unit repository"""
        # Create directories
        (repo_path / "weeks").mkdir(exist_ok=True)
        (repo_path / "assessments").mkdir(exist_ok=True)
        (repo_path / "resources").mkdir(exist_ok=True)

        # Create README
        readme = repo_path / "README.md"
        readme.write_text(
            "# Unit Content Repository\n\n"
            "This repository stores all content for this unit.\n\n"
            "## Structure\n\n"
            "- `weeks/` - Weekly content (lectures, workshops, etc.)\n"
            "- `assessments/` - Assessment materials\n"
            "- `resources/` - Additional resources\n"
        )

        # Create .gitkeep files to preserve empty directories
        for subdir in ["weeks", "assessments", "resources"]:
            gitkeep = repo_path / subdir / ".gitkeep"
            gitkeep.touch()

    def _run_git(self, repo_path: Path, *args: str) -> str:
        """
        Run a git command in the specified repository

        Args:
            repo_path: Path to repository
            *args: Git command arguments

        Returns:
            Command output
        """
        cmd = ["git", "-C", str(repo_path), *list(args)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def _generate_content_path(
        self, content_type: str, content_id: str, week_number: int | None = None
    ) -> str:
        """
        Generate path within unit repository for content storage.

        Args:
            content_type: Type of content (lecture, workshop, assessment, etc.)
            content_id: Content identifier
            week_number: Optional week number for weekly content

        Returns:
            Relative path within unit repo
        """
        if week_number is not None:
            return f"weeks/week-{week_number:02d}/{content_type}-{content_id}.md"
        if content_type in ("assessment", "exam", "quiz", "assignment"):
            return f"assessments/{content_type}-{content_id}.md"
        return f"resources/{content_type}-{content_id}.md"

    def generate_content_path(
        self,
        content_id: str,
        content_type: str = "content",
        week_number: int | None = None,
    ) -> str:
        """
        Generate path for content storage (public method).

        Args:
            content_id: Content identifier
            content_type: Type of content
            week_number: Optional week number

        Returns:
            Relative path within unit repo
        """
        return self._generate_content_path(content_type, content_id, week_number)

    def save_content(
        self,
        unit_id: str,
        path: str,
        content: str,
        user_email: str,
        message: str | None = None,
    ) -> str:
        """
        Save content to unit's Git repository

        Args:
            unit_id: Unit identifier
            path: Relative path for the file within unit repo
            content: Content to save
            user_email: Email of user making the change
            message: Optional commit message

        Returns:
            Commit hash
        """
        repo_path = self._ensure_unit_repo(unit_id)

        # Ensure parent directories exist
        file_path = repo_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        file_path.write_text(content)

        # Stage and commit
        self._run_git(repo_path, "add", path)

        # Generate commit message
        if not message:
            action = (
                "Created" if not self._file_exists_in_git(unit_id, path) else "Updated"
            )
            message = f"{action} {Path(path).stem}"

        commit_message = f"{message}\n\nUpdated by: {user_email}"

        try:
            self._run_git(repo_path, "commit", "-m", commit_message)
            return self._run_git(repo_path, "rev-parse", "HEAD")
        except subprocess.CalledProcessError:
            # No changes to commit
            return self.get_current_commit(unit_id, path)

    def get_content(self, unit_id: str, path: str, commit: str | None = None) -> str:
        """
        Get content from unit's repository

        Args:
            unit_id: Unit identifier
            path: Relative path to file
            commit: Optional commit hash to retrieve specific version

        Returns:
            File content
        """
        repo_path = self._get_unit_repo_path(unit_id)

        if not repo_path.exists():
            raise FileNotFoundError(f"Unit repository not found: {unit_id}")

        if commit:
            # Get content at specific commit
            return self._run_git(repo_path, "show", f"{commit}:{path}")

        # Get current content
        file_path = repo_path / path
        if file_path.exists():
            return file_path.read_text()
        raise FileNotFoundError(f"Content not found: {path} in unit {unit_id}")

    def get_history(
        self, unit_id: str, path: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get commit history for a file

        Args:
            unit_id: Unit identifier
            path: Relative path to file
            limit: Maximum number of commits to return

        Returns:
            List of commit information
        """
        repo_path = self._get_unit_repo_path(unit_id)

        if not repo_path.exists():
            return []

        try:
            log_format = "%H|%ai|%an|%ae|%s"
            log_output = self._run_git(
                repo_path,
                "log",
                f"--max-count={limit}",
                f"--format={log_format}",
                "--",
                path,
            )

            if not log_output:
                return []

            commits = []
            for line in log_output.split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) >= 5:
                        commits.append(
                            {
                                "commit": parts[0],
                                "date": parts[1],
                                "author_name": parts[2],
                                "author_email": parts[3],
                                "message": parts[4],
                            }
                        )

            return commits
        except subprocess.CalledProcessError:
            return []

    def diff(
        self, unit_id: str, path: str, old_commit: str, new_commit: str = "HEAD"
    ) -> str:
        """
        Get diff between two versions

        Args:
            unit_id: Unit identifier
            path: Relative path to file
            old_commit: Old commit hash
            new_commit: New commit hash (defaults to HEAD)

        Returns:
            Diff output
        """
        repo_path = self._get_unit_repo_path(unit_id)

        try:
            return self._run_git(repo_path, "diff", old_commit, new_commit, "--", path)
        except subprocess.CalledProcessError:
            return ""

    def get_current_commit(self, unit_id: str, path: str | None = None) -> str:
        """
        Get current commit hash for a file or repository

        Args:
            unit_id: Unit identifier
            path: Optional file path

        Returns:
            Commit hash
        """
        repo_path = self._get_unit_repo_path(unit_id)

        if not repo_path.exists():
            return ""

        if path:
            try:
                return self._run_git(repo_path, "log", "-1", "--format=%H", "--", path)
            except subprocess.CalledProcessError:
                return ""
        else:
            try:
                return self._run_git(repo_path, "rev-parse", "HEAD")
            except subprocess.CalledProcessError:
                return ""

    def revert_to_commit(
        self, unit_id: str, path: str, commit: str, user_email: str
    ) -> str:
        """
        Revert a file to a previous version

        Args:
            unit_id: Unit identifier
            path: File path to revert
            commit: Commit to revert to
            user_email: User performing the revert

        Returns:
            New commit hash
        """
        old_content = self.get_content(unit_id, path, commit)
        return self.save_content(
            unit_id, path, old_content, user_email, f"Reverted to version {commit[:8]}"
        )

    def delete_content(self, unit_id: str, path: str, user_email: str) -> str:
        """
        Delete content from repository

        Args:
            unit_id: Unit identifier
            path: File path to delete
            user_email: User performing the deletion

        Returns:
            Commit hash
        """
        repo_path = self._get_unit_repo_path(unit_id)
        file_path = repo_path / path

        if not file_path.exists():
            raise FileNotFoundError(f"Content not found: {path}")

        self._run_git(repo_path, "rm", path)
        commit_message = f"Deleted {Path(path).stem}\n\nDeleted by: {user_email}"
        self._run_git(repo_path, "commit", "-m", commit_message)

        return self.get_current_commit(unit_id)

    def save_binary(
        self,
        unit_id: str,
        path: str,
        data: bytes,
        user_email: str,
        message: str | None = None,
    ) -> str:
        """
        Save binary data (e.g. an image) to unit's Git repository.

        Args:
            unit_id: Unit identifier
            path: Relative path for the file within unit repo
            data: Binary data to save
            user_email: Email of user making the change
            message: Optional commit message

        Returns:
            Commit hash
        """
        repo_path = self._ensure_unit_repo(unit_id)

        file_path = repo_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_bytes(data)

        self._run_git(repo_path, "add", path)

        if not message:
            message = f"Added {Path(path).name}"

        commit_message = f"{message}\n\nUpdated by: {user_email}"

        try:
            self._run_git(repo_path, "commit", "-m", commit_message)
            return self._run_git(repo_path, "rev-parse", "HEAD")
        except subprocess.CalledProcessError:
            return self.get_current_commit(unit_id, path)

    def delete_file(
        self, unit_id: str, path: str, user_email: str, message: str | None = None
    ) -> str:
        """
        Delete a file from repository (works for both text and binary).

        Args:
            unit_id: Unit identifier
            path: File path to delete
            user_email: User performing the deletion
            message: Optional commit message

        Returns:
            Commit hash
        """
        repo_path = self._get_unit_repo_path(unit_id)
        file_path = repo_path / path

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        self._run_git(repo_path, "rm", path)
        commit_message = (
            f"{message or f'Deleted {Path(path).name}'}\n\nDeleted by: {user_email}"
        )
        self._run_git(repo_path, "commit", "-m", commit_message)

        return self.get_current_commit(unit_id)

    def list_directory(self, unit_id: str, dir_path: str) -> list[str]:
        """
        List files in a subdirectory of the unit repository.

        Args:
            unit_id: Unit identifier
            dir_path: Relative directory path within unit repo

        Returns:
            List of filenames in the directory
        """
        repo_path = self._get_unit_repo_path(unit_id)
        full_path = repo_path / dir_path

        if not full_path.exists() or not full_path.is_dir():
            return []

        return [f.name for f in full_path.iterdir() if f.is_file()]

    def read_binary(self, unit_id: str, path: str) -> bytes:
        """
        Read binary file from unit's repository.

        Args:
            unit_id: Unit identifier
            path: Relative path to file

        Returns:
            File bytes
        """
        repo_path = self._get_unit_repo_path(unit_id)

        if not repo_path.exists():
            raise FileNotFoundError(f"Unit repository not found: {unit_id}")

        file_path = repo_path / path
        if file_path.exists():
            return file_path.read_bytes()
        raise FileNotFoundError(f"File not found: {path} in unit {unit_id}")

    def _file_exists_in_git(self, unit_id: str, path: str) -> bool:
        """Check if file exists in Git repository"""
        repo_path = self._get_unit_repo_path(unit_id)

        if not repo_path.exists():
            return False

        try:
            self._run_git(repo_path, "ls-files", "--error-unmatch", path)
            return True
        except subprocess.CalledProcessError:
            return False

    def delete_unit_repo(self, unit_id: str) -> bool:
        """
        Delete an entire unit repository.

        Args:
            unit_id: Unit identifier

        Returns:
            True if deleted, False if not found
        """
        repo_path = self._get_unit_repo_path(unit_id)

        if repo_path.exists():
            shutil.rmtree(repo_path)
            return True
        return False

    def get_unit_history(self, unit_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get commit history for entire unit repository.

        Args:
            unit_id: Unit identifier
            limit: Maximum number of commits

        Returns:
            List of commit information
        """
        repo_path = self._get_unit_repo_path(unit_id)

        if not repo_path.exists():
            return []

        try:
            log_format = "%H|%ai|%an|%ae|%s"
            log_output = self._run_git(
                repo_path, "log", f"--max-count={limit}", f"--format={log_format}"
            )

            if not log_output:
                return []

            commits = []
            for line in log_output.split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) >= 5:
                        commits.append(
                            {
                                "commit": parts[0],
                                "date": parts[1],
                                "author_name": parts[2],
                                "author_email": parts[3],
                                "message": parts[4],
                            }
                        )

            return commits
        except subprocess.CalledProcessError:
            return []

    def search_content(
        self, unit_id: str, query: str, file_pattern: str = "*.md"
    ) -> list[dict[str, Any]]:
        """
        Search content in unit repository

        Args:
            unit_id: Unit identifier
            query: Search query
            file_pattern: File pattern to search (default: *.md)

        Returns:
            List of matching files with context
        """
        repo_path = self._get_unit_repo_path(unit_id)

        if not repo_path.exists():
            return []

        try:
            grep_output = self._run_git(
                repo_path,
                "grep",
                "-i",
                "-n",
                "--",
                query,
                file_pattern,
            )

            results = []
            for line in grep_output.split("\n"):
                if ":" in line:
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        results.append(
                            {
                                "file": parts[0],
                                "line": parts[1],
                                "content": parts[2].strip(),
                            }
                        )

            return results
        except subprocess.CalledProcessError:
            return []

    def get_unit_stats(self, unit_id: str) -> dict[str, Any]:
        """
        Get statistics for a unit repository

        Args:
            unit_id: Unit identifier

        Returns:
            Repository statistics
        """
        repo_path = self._get_unit_repo_path(unit_id)

        if not repo_path.exists():
            return {
                "exists": False,
                "file_count": 0,
                "commit_count": 0,
                "repository_size_bytes": 0,
            }

        try:
            files_output = self._run_git(repo_path, "ls-files")
            file_count = len(files_output.split("\n")) if files_output else 0

            log_output = self._run_git(repo_path, "log", "--oneline")
            commit_count = len(log_output.split("\n")) if log_output else 0

            repo_size = sum(
                f.stat().st_size for f in repo_path.rglob("*") if f.is_file()
            )

            return {
                "exists": True,
                "file_count": file_count,
                "commit_count": commit_count,
                "repository_size_bytes": repo_size,
                "repository_path": str(repo_path),
            }
        except subprocess.CalledProcessError:
            return {
                "exists": True,
                "file_count": 0,
                "commit_count": 0,
                "repository_size_bytes": 0,
                "repository_path": str(repo_path),
            }

    def list_unit_repos(self) -> list[str]:
        """
        List all unit repository IDs.

        Returns:
            List of unit IDs that have repositories
        """
        if not self.repos_base.exists():
            return []

        return [
            d.name
            for d in self.repos_base.iterdir()
            if d.is_dir() and (d / ".git").exists()
        ]


# Singleton instance
_git_service: GitContentService | None = None


def get_git_service() -> GitContentService:
    """Get or create Git service singleton"""
    global _git_service  # noqa: PLW0603
    if _git_service is None:
        _git_service = GitContentService()
    return _git_service
