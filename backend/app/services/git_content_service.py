"""
Git-backed content storage service

Manages all content files in a Git repository for version control.
All commits are made by the system user with web user info in commit messages.
"""

import os
import subprocess
from pathlib import Path
from typing import Any


class GitContentService:
    """Service for managing content in Git repository"""

    def __init__(self, repo_path: str | None = None):
        """
        Initialize Git content service

        Args:
            repo_path: Path to Git repository (defaults to CONTENT_REPO_PATH env var)
        """
        self.repo_path = Path(repo_path or os.getenv("CONTENT_REPO_PATH", "/app/content"))
        self._ensure_repo_initialized()

    def _ensure_repo_initialized(self) -> None:
        """Ensure Git repository is initialized"""
        if not self.repo_path.exists():
            self.repo_path.mkdir(parents=True, exist_ok=True)

        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            # Initialize repository
            self._run_git("init")
            self._run_git("config", "user.name", "Curriculum Curator")
            self._run_git("config", "user.email", "system@curriculum-curator.local")

            # Create initial commit
            readme_path = self.repo_path / "README.md"
            readme_path.write_text("# Curriculum Curator Content Repository\n\nThis repository stores all course content.\n")
            self._run_git("add", "README.md")
            self._run_git("commit", "-m", "Initial repository setup")

    def _run_git(self, *args) -> str:
        """
        Run a git command in the repository

        Args:
            *args: Git command arguments

        Returns:
            Command output
        """
        cmd = ["git", "-C", str(self.repo_path), *list(args)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def _generate_content_path(self, course_id: str, material_type: str, material_id: str) -> str:
        """
        Generate a consistent path for content storage

        Args:
            course_id: Course identifier
            material_type: Type of material (lecture, quiz, etc.)
            material_id: Material identifier

        Returns:
            Relative path for content file
        """
        # Use first 8 chars of IDs for cleaner paths
        course_short = course_id[:8] if len(course_id) > 8 else course_id
        material_short = material_id[:8] if len(material_id) > 8 else material_id

        return f"courses/{course_short}/{material_type}/{material_short}.md"

    def save_content(
        self,
        path: str,
        content: str,
        user_email: str,
        message: str | None = None
    ) -> str:
        """
        Save content to Git repository

        Args:
            path: Relative path for the file
            content: Content to save
            user_email: Email of user making the change
            message: Optional commit message

        Returns:
            Commit hash
        """
        # Ensure parent directories exist
        file_path = self.repo_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        file_path.write_text(content)

        # Stage and commit
        self._run_git("add", path)

        # Generate commit message
        if not message:
            action = "Created" if not self._file_exists_in_git(path) else "Updated"
            message = f"{action} {Path(path).stem}"

        commit_message = f"{message}\n\nUpdated by: {user_email}"

        try:
            self._run_git("commit", "-m", commit_message)
            # Extract commit hash from output
            return self._run_git("rev-parse", "HEAD")
        except subprocess.CalledProcessError:
            # No changes to commit
            return self.get_current_commit(path)

    def get_content(self, path: str, commit: str | None = None) -> str:
        """
        Get content from repository

        Args:
            path: Relative path to file
            commit: Optional commit hash to retrieve specific version

        Returns:
            File content
        """
        if commit:
            # Get content at specific commit
            return self._run_git("show", f"{commit}:{path}")
        # Get current content
        file_path = self.repo_path / path
        if file_path.exists():
            return file_path.read_text()
        raise FileNotFoundError(f"Content not found: {path}")

    def get_history(self, path: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get commit history for a file

        Args:
            path: Relative path to file
            limit: Maximum number of commits to return

        Returns:
            List of commit information
        """
        try:
            # Get commit history with formatted output
            log_format = "%H|%ai|%an|%ae|%s"
            log_output = self._run_git(
                "log",
                f"--max-count={limit}",
                f"--format={log_format}",
                "--",
                path
            )

            if not log_output:
                return []

            commits = []
            for line in log_output.split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 5:
                        commits.append({
                            "commit": parts[0],
                            "date": parts[1],
                            "author_name": parts[2],
                            "author_email": parts[3],
                            "message": parts[4]
                        })

            return commits
        except subprocess.CalledProcessError:
            return []

    def diff(self, path: str, old_commit: str, new_commit: str = "HEAD") -> str:
        """
        Get diff between two versions

        Args:
            path: Relative path to file
            old_commit: Old commit hash
            new_commit: New commit hash (defaults to HEAD)

        Returns:
            Diff output
        """
        try:
            return self._run_git("diff", old_commit, new_commit, "--", path)
        except subprocess.CalledProcessError:
            return ""

    def get_current_commit(self, path: str | None = None) -> str:
        """
        Get current commit hash for a file or repository

        Args:
            path: Optional file path

        Returns:
            Commit hash
        """
        if path:
            # Get last commit for specific file
            try:
                return self._run_git("log", "-1", "--format=%H", "--", path)
            except subprocess.CalledProcessError:
                return ""
        else:
            # Get current HEAD
            return self._run_git("rev-parse", "HEAD")

    def revert_to_commit(self, path: str, commit: str, user_email: str) -> str:
        """
        Revert a file to a previous version

        Args:
            path: File path to revert
            commit: Commit to revert to
            user_email: User performing the revert

        Returns:
            New commit hash
        """
        # Get content from old commit
        old_content = self.get_content(path, commit)

        # Save as new version
        return self.save_content(
            path,
            old_content,
            user_email,
            f"Reverted to version {commit[:8]}"
        )

    def delete_content(self, path: str, user_email: str) -> str:
        """
        Delete content from repository

        Args:
            path: File path to delete
            user_email: User performing the deletion

        Returns:
            Commit hash
        """
        file_path = self.repo_path / path
        if not file_path.exists():
            raise FileNotFoundError(f"Content not found: {path}")

        self._run_git("rm", path)
        commit_message = f"Deleted {Path(path).stem}\n\nDeleted by: {user_email}"
        self._run_git("commit", "-m", commit_message)

        return self.get_current_commit()

    def _file_exists_in_git(self, path: str) -> bool:
        """Check if file exists in Git repository"""
        try:
            self._run_git("ls-files", "--error-unmatch", path)
            return True
        except subprocess.CalledProcessError:
            return False

    def search_content(self, query: str, file_pattern: str | None = "*.md") -> list[dict[str, Any]]:
        """
        Search content in repository

        Args:
            query: Search query
            file_pattern: File pattern to search (default: *.md)

        Returns:
            List of matching files with context
        """
        try:
            # Use git grep for efficient searching
            grep_output = self._run_git(
                "grep",
                "-i",  # Case insensitive
                "-n",  # Show line numbers
                "--",
                query,
                file_pattern
            )

            results = []
            for line in grep_output.split('\n'):
                if ':' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        results.append({
                            "file": parts[0],
                            "line": parts[1],
                            "content": parts[2].strip()
                        })

            return results
        except subprocess.CalledProcessError:
            return []

    def get_repository_stats(self) -> dict[str, Any]:
        """
        Get repository statistics

        Returns:
            Repository statistics
        """
        try:
            # Count files
            file_count = len(self._run_git("ls-files").split('\n'))

            # Count commits
            commit_count = len(self._run_git("log", "--oneline").split('\n'))

            # Get repository size
            repo_size = sum(f.stat().st_size for f in self.repo_path.rglob('*') if f.is_file())

            return {
                "file_count": file_count,
                "commit_count": commit_count,
                "repository_size_bytes": repo_size,
                "repository_path": str(self.repo_path)
            }
        except subprocess.CalledProcessError:
            return {
                "file_count": 0,
                "commit_count": 0,
                "repository_size_bytes": 0,
                "repository_path": str(self.repo_path)
            }


# Singleton instance
_git_service: GitContentService | None = None


def get_git_service() -> GitContentService:
    """Get or create Git service singleton"""
    global _git_service  # noqa: PLW0603
    if _git_service is None:
        _git_service = GitContentService()
    return _git_service
