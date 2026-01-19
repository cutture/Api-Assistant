"""
GitHub Service.

Provides GitHub repository operations, code indexing, and context management.
"""

import re
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Any
from functools import lru_cache

from src.auth.oauth import GitHubOAuth, OAuthError

logger = logging.getLogger(__name__)


@dataclass
class GitHubConnection:
    """GitHub connection information."""
    id: str
    user_id: str
    github_user_id: str
    github_username: str
    access_token: str
    scopes: list[str]
    connected_at: datetime
    avatar_url: Optional[str] = None


@dataclass
class Repository:
    """GitHub repository information."""
    id: int
    full_name: str
    name: str
    owner: str
    description: Optional[str]
    private: bool
    default_branch: str
    language: Optional[str]
    languages: dict[str, int] = field(default_factory=dict)
    html_url: str = ""
    clone_url: str = ""
    updated_at: Optional[datetime] = None
    size: int = 0
    stargazers_count: int = 0


@dataclass
class RepositoryContext:
    """Analyzed repository context for code generation."""
    repo_full_name: str
    default_branch: str
    languages: dict[str, int]
    primary_language: Optional[str]
    framework_detected: Optional[str]
    package_manager: Optional[str]
    structure_summary: str
    key_files: list[str]
    patterns: list[str]
    indexed_files: int = 0
    last_analyzed_at: Optional[datetime] = None


@dataclass
class FileContent:
    """Repository file content."""
    path: str
    name: str
    content: str
    size: int
    language: Optional[str]
    sha: str


# Framework detection patterns
FRAMEWORK_PATTERNS = {
    # Python
    "fastapi": ["fastapi", "uvicorn"],
    "django": ["django", "DJANGO_SETTINGS_MODULE"],
    "flask": ["flask", "Flask(__name__)"],
    "pytorch": ["torch", "pytorch"],
    "tensorflow": ["tensorflow", "tf."],

    # JavaScript/TypeScript
    "react": ["react", "ReactDOM", "jsx"],
    "nextjs": ["next.config", "getStaticProps", "getServerSideProps"],
    "express": ["express()", "app.listen"],
    "nestjs": ["@nestjs", "NestFactory"],
    "vue": ["vue", "createApp"],

    # Java
    "spring": ["@SpringBootApplication", "springframework"],
    "maven": ["pom.xml"],
    "gradle": ["build.gradle"],

    # Go
    "gin": ["github.com/gin-gonic/gin"],
    "echo": ["github.com/labstack/echo"],
    "fiber": ["github.com/gofiber/fiber"],

    # C#
    "aspnet": ["Microsoft.AspNetCore", "WebApplication"],
    "blazor": ["Microsoft.AspNetCore.Components"],
}

# Package manager detection
PACKAGE_MANAGERS = {
    "requirements.txt": "pip",
    "Pipfile": "pipenv",
    "pyproject.toml": "poetry",
    "package.json": "npm",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "go.mod": "go",
    "Cargo.toml": "cargo",
    "*.csproj": "nuget",
    "Gemfile": "bundler",
    "composer.json": "composer",
}

# Important files to index
IMPORTANT_FILES = [
    "README.md",
    "README.rst",
    "CONTRIBUTING.md",
    "setup.py",
    "setup.cfg",
    "pyproject.toml",
    "package.json",
    "tsconfig.json",
    "pom.xml",
    "build.gradle",
    "go.mod",
    "Cargo.toml",
    ".env.example",
    "docker-compose.yml",
    "Dockerfile",
    "Makefile",
]

# Code file extensions to index
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs",
    ".cs", ".rb", ".php", ".kt", ".swift", ".cpp", ".c", ".h",
    ".sql", ".sh", ".bash", ".yml", ".yaml", ".json", ".toml",
}


class GitHubService:
    """Service for GitHub operations and repository context."""

    def __init__(self):
        """Initialize GitHub service."""
        self._oauth = GitHubOAuth()
        self._connections: dict[str, GitHubConnection] = {}
        self._repo_contexts: dict[str, RepositoryContext] = {}

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> str:
        """
        Get GitHub OAuth authorization URL.

        Args:
            redirect_uri: OAuth callback URL
            state: Optional state for CSRF protection

        Returns:
            Authorization URL
        """
        return self._oauth.get_authorization_url(redirect_uri, state)

    async def authenticate(
        self,
        code: str,
        redirect_uri: str,
        user_id: str
    ) -> GitHubConnection:
        """
        Authenticate user with GitHub OAuth code.

        Args:
            code: Authorization code from callback
            redirect_uri: OAuth callback URL
            user_id: Application user ID

        Returns:
            GitHubConnection with connection details
        """
        user_info = await self._oauth.authenticate(code, redirect_uri)

        connection = GitHubConnection(
            id=f"gh_{user_id}",
            user_id=user_id,
            github_user_id=user_info.provider_user_id,
            github_username=user_info.username or "",
            access_token=user_info.access_token or "",
            scopes=self._oauth.SCOPES,
            connected_at=datetime.now(timezone.utc),
            avatar_url=user_info.avatar_url,
        )

        # Store connection in memory (in production, store in database)
        self._connections[user_id] = connection

        return connection

    def get_connection(self, user_id: str) -> Optional[GitHubConnection]:
        """Get GitHub connection for a user."""
        return self._connections.get(user_id)

    def disconnect(self, user_id: str) -> bool:
        """
        Disconnect GitHub for a user.

        Args:
            user_id: User ID to disconnect

        Returns:
            True if disconnected, False if not connected
        """
        if user_id in self._connections:
            del self._connections[user_id]
            # Also clear any cached repo contexts
            keys_to_remove = [
                k for k in self._repo_contexts
                if k.startswith(f"{user_id}:")
            ]
            for key in keys_to_remove:
                del self._repo_contexts[key]
            return True
        return False

    async def list_repos(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 30
    ) -> list[Repository]:
        """
        List user's accessible repositories.

        Args:
            user_id: User ID
            page: Page number
            per_page: Results per page

        Returns:
            List of Repository objects
        """
        connection = self._connections.get(user_id)
        if not connection:
            raise ValueError("User not connected to GitHub")

        repos_data = await self._oauth.get_user_repos(
            connection.access_token,
            page=page,
            per_page=per_page
        )

        return [
            Repository(
                id=r["id"],
                full_name=r["full_name"],
                name=r["name"],
                owner=r["owner"]["login"],
                description=r.get("description"),
                private=r["private"],
                default_branch=r.get("default_branch", "main"),
                language=r.get("language"),
                html_url=r.get("html_url", ""),
                clone_url=r.get("clone_url", ""),
                size=r.get("size", 0),
                stargazers_count=r.get("stargazers_count", 0),
            )
            for r in repos_data
        ]

    async def analyze_repository(
        self,
        user_id: str,
        owner: str,
        repo: str
    ) -> RepositoryContext:
        """
        Analyze a repository and build context for code generation.

        Args:
            user_id: User ID
            owner: Repository owner
            repo: Repository name

        Returns:
            RepositoryContext with analysis results
        """
        connection = self._connections.get(user_id)
        if not connection:
            raise ValueError("User not connected to GitHub")

        full_name = f"{owner}/{repo}"
        cache_key = f"{user_id}:{full_name}"

        # Get repository info
        repos = await self.list_repos(user_id, per_page=100)
        repo_info = next((r for r in repos if r.full_name == full_name), None)

        if not repo_info:
            raise ValueError(f"Repository not found or no access: {full_name}")

        # Get languages
        languages = await self._oauth.get_repo_languages(
            connection.access_token,
            owner,
            repo
        )

        # Get root contents to analyze structure
        try:
            contents = await self._oauth.get_repo_contents(
                connection.access_token,
                owner,
                repo
            )
        except OAuthError:
            contents = []

        # Detect package manager
        package_manager = None
        file_names = [c.get("name", "") for c in contents if c.get("type") == "file"]
        for pattern, pm in PACKAGE_MANAGERS.items():
            if "*" in pattern:
                # Glob pattern
                regex = pattern.replace(".", r"\.").replace("*", ".*")
                if any(re.match(regex, f) for f in file_names):
                    package_manager = pm
                    break
            elif pattern in file_names:
                package_manager = pm
                break

        # Detect framework
        framework_detected = None
        try:
            # Read main config files to detect frameworks
            files_to_check = ["package.json", "requirements.txt", "go.mod", "Cargo.toml"]
            for filename in files_to_check:
                if filename in file_names:
                    try:
                        content = await self._oauth.get_file_content(
                            connection.access_token,
                            owner,
                            repo,
                            filename
                        )
                        for framework, patterns in FRAMEWORK_PATTERNS.items():
                            if any(p in content for p in patterns):
                                framework_detected = framework
                                break
                        if framework_detected:
                            break
                    except OAuthError:
                        continue
        except Exception as e:
            logger.warning(f"Framework detection error: {e}")

        # Build structure summary
        dirs = [c["name"] for c in contents if c.get("type") == "dir"]
        files = [c["name"] for c in contents if c.get("type") == "file"]

        structure_parts = []
        if dirs:
            structure_parts.append(f"Directories: {', '.join(dirs[:10])}")
        if files:
            structure_parts.append(f"Root files: {', '.join(files[:10])}")

        # Identify key files
        key_files = [f for f in file_names if f in IMPORTANT_FILES]

        # Detect patterns
        patterns = []
        if "src" in dirs:
            patterns.append("src/ source directory")
        if "tests" in dirs or "test" in dirs:
            patterns.append("Dedicated test directory")
        if "docs" in dirs:
            patterns.append("Documentation directory")
        if ".github" in dirs:
            patterns.append("GitHub Actions configured")
        if "Dockerfile" in files or "docker-compose.yml" in files:
            patterns.append("Docker containerization")

        # Determine primary language
        primary_language = repo_info.language
        if not primary_language and languages:
            primary_language = max(languages, key=languages.get)

        context = RepositoryContext(
            repo_full_name=full_name,
            default_branch=repo_info.default_branch,
            languages=languages,
            primary_language=primary_language,
            framework_detected=framework_detected,
            package_manager=package_manager,
            structure_summary="; ".join(structure_parts),
            key_files=key_files,
            patterns=patterns,
            last_analyzed_at=datetime.now(timezone.utc),
        )

        # Cache the context
        self._repo_contexts[cache_key] = context

        return context

    async def get_file_content(
        self,
        user_id: str,
        owner: str,
        repo: str,
        path: str
    ) -> FileContent:
        """
        Get file content from repository.

        Args:
            user_id: User ID
            owner: Repository owner
            repo: Repository name
            path: File path

        Returns:
            FileContent with file details
        """
        connection = self._connections.get(user_id)
        if not connection:
            raise ValueError("User not connected to GitHub")

        content = await self._oauth.get_file_content(
            connection.access_token,
            owner,
            repo,
            path
        )

        # Get metadata
        contents = await self._oauth.get_repo_contents(
            connection.access_token,
            owner,
            repo,
            path
        )

        metadata = contents[0] if contents else {}

        # Detect language from extension
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
        language = self._detect_language(ext)

        return FileContent(
            path=path,
            name=path.rsplit("/", 1)[-1],
            content=content,
            size=metadata.get("size", len(content)),
            language=language,
            sha=metadata.get("sha", ""),
        )

    def _detect_language(self, extension: str) -> Optional[str]:
        """Detect language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".kt": "kotlin",
            ".swift": "swift",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".sql": "sql",
            ".sh": "bash",
            ".bash": "bash",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".json": "json",
            ".toml": "toml",
            ".md": "markdown",
        }
        return extension_map.get(extension.lower())

    def get_cached_context(
        self,
        user_id: str,
        repo_full_name: str
    ) -> Optional[RepositoryContext]:
        """Get cached repository context."""
        cache_key = f"{user_id}:{repo_full_name}"
        return self._repo_contexts.get(cache_key)

    def clear_context_cache(self, user_id: str, repo_full_name: Optional[str] = None):
        """Clear cached repository context."""
        if repo_full_name:
            cache_key = f"{user_id}:{repo_full_name}"
            if cache_key in self._repo_contexts:
                del self._repo_contexts[cache_key]
        else:
            # Clear all contexts for user
            keys_to_remove = [
                k for k in self._repo_contexts
                if k.startswith(f"{user_id}:")
            ]
            for key in keys_to_remove:
                del self._repo_contexts[key]


# Singleton instance
_github_service: GitHubService | None = None


def get_github_service() -> GitHubService:
    """Get or create the GitHub service singleton."""
    global _github_service
    if _github_service is None:
        _github_service = GitHubService()
    return _github_service
