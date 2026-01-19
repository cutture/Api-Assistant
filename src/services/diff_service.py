"""
Diff Service for Intelligent Coding Agent.

Provides code comparison functionality:
- Unified diff generation between code versions
- Side-by-side diff formatting
- Change statistics
"""

import difflib
from dataclasses import dataclass
from typing import Optional


@dataclass
class DiffStats:
    """Statistics about a diff."""
    additions: int
    deletions: int
    changes: int
    total_lines_before: int
    total_lines_after: int


@dataclass
class DiffResult:
    """Result of comparing two code versions."""
    unified_diff: str
    html_diff: str
    stats: DiffStats
    has_changes: bool


class DiffService:
    """
    Service for generating and formatting code diffs.

    Supports:
    - Unified diff format (for display and storage)
    - HTML diff format (for rich display)
    - Change statistics
    """

    def __init__(self, context_lines: int = 3):
        """
        Initialize diff service.

        Args:
            context_lines: Number of context lines around changes
        """
        self.context_lines = context_lines

    def compare(
        self,
        old_code: str,
        new_code: str,
        old_label: str = "before",
        new_label: str = "after",
    ) -> DiffResult:
        """
        Compare two code versions and generate diff.

        Args:
            old_code: Original code version
            new_code: New code version
            old_label: Label for old version
            new_label: Label for new version

        Returns:
            DiffResult with unified diff, HTML diff, and stats
        """
        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)

        # Generate unified diff
        unified_diff = self._generate_unified_diff(
            old_lines, new_lines, old_label, new_label
        )

        # Generate HTML diff
        html_diff = self._generate_html_diff(old_lines, new_lines)

        # Calculate stats
        stats = self._calculate_stats(old_lines, new_lines)

        return DiffResult(
            unified_diff=unified_diff,
            html_diff=html_diff,
            stats=stats,
            has_changes=stats.additions > 0 or stats.deletions > 0,
        )

    def _generate_unified_diff(
        self,
        old_lines: list[str],
        new_lines: list[str],
        old_label: str,
        new_label: str,
    ) -> str:
        """Generate unified diff format."""
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_label,
            tofile=new_label,
            n=self.context_lines,
        )
        return "".join(diff)

    def _generate_html_diff(
        self,
        old_lines: list[str],
        new_lines: list[str],
    ) -> str:
        """Generate HTML table diff for rich display."""
        differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
        return differ.make_table(
            old_lines,
            new_lines,
            fromdesc="Before",
            todesc="After",
            context=True,
            numlines=self.context_lines,
        )

    def _calculate_stats(
        self,
        old_lines: list[str],
        new_lines: list[str],
    ) -> DiffStats:
        """Calculate diff statistics."""
        # Use SequenceMatcher for detailed analysis
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

        additions = 0
        deletions = 0
        changes = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "insert":
                additions += j2 - j1
            elif tag == "delete":
                deletions += i2 - i1
            elif tag == "replace":
                # Count as both changes
                old_count = i2 - i1
                new_count = j2 - j1
                changes += max(old_count, new_count)

        return DiffStats(
            additions=additions,
            deletions=deletions,
            changes=changes,
            total_lines_before=len(old_lines),
            total_lines_after=len(new_lines),
        )

    def format_stats_summary(self, stats: DiffStats) -> str:
        """Format stats as human-readable summary."""
        parts = []

        if stats.additions > 0:
            parts.append(f"+{stats.additions} additions")
        if stats.deletions > 0:
            parts.append(f"-{stats.deletions} deletions")
        if stats.changes > 0:
            parts.append(f"~{stats.changes} changes")

        if not parts:
            return "No changes"

        return ", ".join(parts)

    def get_changed_lines(
        self,
        old_code: str,
        new_code: str,
    ) -> dict:
        """
        Get line numbers of changed lines.

        Returns:
            Dict with 'added', 'deleted', 'modified' line numbers
        """
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

        added = []
        deleted = []
        modified = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "insert":
                added.extend(range(j1 + 1, j2 + 1))  # 1-indexed
            elif tag == "delete":
                deleted.extend(range(i1 + 1, i2 + 1))  # 1-indexed
            elif tag == "replace":
                deleted.extend(range(i1 + 1, i2 + 1))
                added.extend(range(j1 + 1, j2 + 1))
                # Mark as modified (overlap of old and new ranges)
                modified.extend(range(j1 + 1, j2 + 1))

        return {
            "added": added,
            "deleted": deleted,
            "modified": modified,
        }

    def generate_inline_diff(
        self,
        old_code: str,
        new_code: str,
    ) -> list[dict]:
        """
        Generate inline diff with line-by-line changes.

        Returns:
            List of dicts with line info for rendering
        """
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        result = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for idx, line in enumerate(old_lines[i1:i2]):
                    result.append({
                        "type": "equal",
                        "old_line_no": i1 + idx + 1,
                        "new_line_no": j1 + idx + 1,
                        "content": line,
                    })
            elif tag == "delete":
                for idx, line in enumerate(old_lines[i1:i2]):
                    result.append({
                        "type": "delete",
                        "old_line_no": i1 + idx + 1,
                        "new_line_no": None,
                        "content": line,
                    })
            elif tag == "insert":
                for idx, line in enumerate(new_lines[j1:j2]):
                    result.append({
                        "type": "insert",
                        "old_line_no": None,
                        "new_line_no": j1 + idx + 1,
                        "content": line,
                    })
            elif tag == "replace":
                # Show deletions first, then insertions
                for idx, line in enumerate(old_lines[i1:i2]):
                    result.append({
                        "type": "delete",
                        "old_line_no": i1 + idx + 1,
                        "new_line_no": None,
                        "content": line,
                    })
                for idx, line in enumerate(new_lines[j1:j2]):
                    result.append({
                        "type": "insert",
                        "old_line_no": None,
                        "new_line_no": j1 + idx + 1,
                        "content": line,
                    })

        return result


# Singleton instance
_diff_service: Optional[DiffService] = None


def get_diff_service() -> DiffService:
    """Get the global diff service instance."""
    global _diff_service
    if _diff_service is None:
        _diff_service = DiffService()
    return _diff_service
