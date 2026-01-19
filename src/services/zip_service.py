"""
ZIP Bundle Service for Intelligent Coding Agent.

Generates downloadable ZIP bundles from code executions,
including source code, tests, and metadata.
"""

import io
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.services.artifact_service import ArtifactService, StoredArtifact, get_artifact_service


@dataclass
class ZipEntry:
    """Entry to include in a ZIP bundle."""
    filename: str
    content: str | bytes
    is_binary: bool = False


@dataclass
class ZipBundle:
    """Result of creating a ZIP bundle."""
    zip_bytes: bytes
    total_files: int
    total_size_bytes: int
    manifest: dict


class ZipService:
    """
    Service for creating ZIP bundles from code executions.

    Creates well-structured ZIP files with:
    - Source code files
    - Test files
    - requirements.txt / package.json (dependencies)
    - README with execution metadata
    """

    def __init__(self, artifact_service: Optional[ArtifactService] = None):
        self.artifact_service = artifact_service or get_artifact_service()

    def create_bundle(
        self,
        entries: list[ZipEntry],
        include_manifest: bool = True,
        metadata: Optional[dict] = None,
    ) -> ZipBundle:
        """
        Create a ZIP bundle from entries.

        Args:
            entries: List of ZipEntry objects to include
            include_manifest: Whether to include manifest.json
            metadata: Optional metadata to include in manifest

        Returns:
            ZipBundle with bytes and metadata
        """
        buffer = io.BytesIO()
        total_size = 0
        manifest_entries = []

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for entry in entries:
                # Get content as bytes
                if entry.is_binary or isinstance(entry.content, bytes):
                    content = entry.content if isinstance(entry.content, bytes) else entry.content.encode("utf-8")
                else:
                    content = entry.content.encode("utf-8")

                # Add to ZIP
                zf.writestr(entry.filename, content)
                total_size += len(content)

                manifest_entries.append({
                    "filename": entry.filename,
                    "size_bytes": len(content),
                    "is_binary": entry.is_binary,
                })

            # Create manifest
            manifest = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "total_files": len(entries),
                "total_size_bytes": total_size,
                "files": manifest_entries,
            }
            if metadata:
                manifest["metadata"] = metadata

            # Add manifest if requested
            if include_manifest:
                manifest_json = json.dumps(manifest, indent=2)
                zf.writestr("manifest.json", manifest_json)

        zip_bytes = buffer.getvalue()

        return ZipBundle(
            zip_bytes=zip_bytes,
            total_files=len(entries),
            total_size_bytes=total_size,
            manifest=manifest,
        )

    def create_code_bundle(
        self,
        code: str,
        tests: Optional[str],
        language: str,
        filename: str = "main",
        dependencies: Optional[list[str]] = None,
        execution_metadata: Optional[dict] = None,
    ) -> ZipBundle:
        """
        Create a ZIP bundle for a code execution result.

        Args:
            code: Generated source code
            tests: Generated test code (optional)
            language: Programming language
            filename: Base filename (without extension)
            dependencies: List of dependencies
            execution_metadata: Execution metadata for README

        Returns:
            ZipBundle ready for download
        """
        entries = []

        # Determine file extension
        ext = self._get_extension(language)

        # Add main code file
        entries.append(ZipEntry(
            filename=f"src/{filename}{ext}",
            content=code,
        ))

        # Add test file if present
        if tests:
            test_filename = self._get_test_filename(filename, language)
            entries.append(ZipEntry(
                filename=f"tests/{test_filename}",
                content=tests,
            ))

        # Add dependencies file
        deps_content = self._create_dependencies_file(language, dependencies or [])
        if deps_content:
            deps_filename = self._get_deps_filename(language)
            entries.append(ZipEntry(
                filename=deps_filename,
                content=deps_content,
            ))

        # Add README
        readme = self._create_readme(
            language=language,
            has_tests=bool(tests),
            dependencies=dependencies or [],
            metadata=execution_metadata,
        )
        entries.append(ZipEntry(
            filename="README.md",
            content=readme,
        ))

        # Add .gitignore
        gitignore = self._create_gitignore(language)
        entries.append(ZipEntry(
            filename=".gitignore",
            content=gitignore,
        ))

        return self.create_bundle(
            entries=entries,
            include_manifest=True,
            metadata=execution_metadata,
        )

    def create_multi_file_bundle(
        self,
        files: dict[str, str],
        language: str,
        tests: Optional[dict[str, str]] = None,
        dependencies: Optional[list[str]] = None,
        execution_metadata: Optional[dict] = None,
    ) -> ZipBundle:
        """
        Create a ZIP bundle for multi-file code generation.

        Args:
            files: Dict mapping filename to code content
            language: Programming language
            tests: Dict mapping test filename to test content
            dependencies: List of dependencies
            execution_metadata: Execution metadata

        Returns:
            ZipBundle ready for download
        """
        entries = []

        # Add source files
        for filename, content in files.items():
            entries.append(ZipEntry(
                filename=f"src/{filename}",
                content=content,
            ))

        # Add test files
        if tests:
            for filename, content in tests.items():
                entries.append(ZipEntry(
                    filename=f"tests/{filename}",
                    content=content,
                ))

        # Add dependencies
        deps_content = self._create_dependencies_file(language, dependencies or [])
        if deps_content:
            deps_filename = self._get_deps_filename(language)
            entries.append(ZipEntry(
                filename=deps_filename,
                content=deps_content,
            ))

        # Add README
        readme = self._create_readme(
            language=language,
            has_tests=bool(tests),
            dependencies=dependencies or [],
            metadata=execution_metadata,
            file_list=list(files.keys()),
        )
        entries.append(ZipEntry(
            filename="README.md",
            content=readme,
        ))

        # Add .gitignore
        gitignore = self._create_gitignore(language)
        entries.append(ZipEntry(
            filename=".gitignore",
            content=gitignore,
        ))

        return self.create_bundle(
            entries=entries,
            include_manifest=True,
            metadata=execution_metadata,
        )

    def save_bundle_as_artifact(
        self,
        bundle: ZipBundle,
        user_id: str,
        artifact_id: str,
        filename: str = "code_bundle.zip",
    ) -> StoredArtifact:
        """
        Save a ZIP bundle as an artifact.

        Args:
            bundle: ZipBundle to save
            user_id: User ID
            artifact_id: Artifact ID
            filename: ZIP filename

        Returns:
            StoredArtifact with storage details
        """
        return self.artifact_service.save_artifact(
            user_id=user_id,
            artifact_id=artifact_id,
            filename=filename,
            content=bundle.zip_bytes,
        )

    def _get_extension(self, language: str) -> str:
        """Get file extension for language."""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "go": ".go",
            "csharp": ".cs",
            "rust": ".rs",
            "ruby": ".rb",
            "php": ".php",
            "c": ".c",
            "cpp": ".cpp",
        }
        return extensions.get(language.lower(), ".txt")

    def _get_test_filename(self, base_filename: str, language: str) -> str:
        """Get test filename for language."""
        ext = self._get_extension(language)
        prefixes = {
            "python": "test_",
            "javascript": "",
            "typescript": "",
            "java": "",
            "go": "",
            "csharp": "",
        }
        suffixes = {
            "python": "",
            "javascript": ".test",
            "typescript": ".test",
            "java": "Test",
            "go": "_test",
            "csharp": "Tests",
        }
        prefix = prefixes.get(language.lower(), "test_")
        suffix = suffixes.get(language.lower(), "")

        if suffix and not suffix.startswith("."):
            return f"{prefix}{base_filename}{suffix}{ext}"
        elif suffix:
            return f"{prefix}{base_filename}{suffix}"
        else:
            return f"{prefix}{base_filename}{ext}"

    def _get_deps_filename(self, language: str) -> str:
        """Get dependencies filename for language."""
        filenames = {
            "python": "requirements.txt",
            "javascript": "package.json",
            "typescript": "package.json",
            "java": "pom.xml",
            "go": "go.mod",
            "csharp": "project.csproj",
            "rust": "Cargo.toml",
        }
        return filenames.get(language.lower(), "dependencies.txt")

    def _create_dependencies_file(
        self,
        language: str,
        dependencies: list[str],
    ) -> Optional[str]:
        """Create dependencies file content."""
        lang = language.lower()

        if lang == "python":
            if not dependencies:
                return "# No dependencies\n"
            return "\n".join(dependencies) + "\n"

        elif lang in ("javascript", "typescript"):
            pkg = {
                "name": "generated-code",
                "version": "1.0.0",
                "description": "Generated by Intelligent Coding Agent",
                "main": "src/main.js" if lang == "javascript" else "src/main.ts",
                "scripts": {
                    "test": "jest" if lang == "javascript" else "jest --preset ts-jest",
                    "start": "node src/main.js" if lang == "javascript" else "ts-node src/main.ts",
                },
                "dependencies": {},
                "devDependencies": {
                    "jest": "^29.0.0",
                },
            }
            if lang == "typescript":
                pkg["devDependencies"]["typescript"] = "^5.0.0"
                pkg["devDependencies"]["ts-jest"] = "^29.0.0"
                pkg["devDependencies"]["@types/jest"] = "^29.0.0"
                pkg["devDependencies"]["@types/node"] = "^20.0.0"

            for dep in dependencies:
                pkg["dependencies"][dep] = "*"

            return json.dumps(pkg, indent=2)

        elif lang == "go":
            return f"""module generated-code

go 1.21

require (
{chr(10).join(f'    {dep} v0.0.0' for dep in dependencies) if dependencies else '    // No dependencies'}
)
"""

        elif lang == "java":
            deps_xml = ""
            for dep in dependencies:
                # Simple format: groupId:artifactId
                parts = dep.split(":")
                if len(parts) >= 2:
                    deps_xml += f"""        <dependency>
            <groupId>{parts[0]}</groupId>
            <artifactId>{parts[1]}</artifactId>
            <version>LATEST</version>
        </dependency>
"""
            return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.generated</groupId>
    <artifactId>generated-code</artifactId>
    <version>1.0.0</version>
    <dependencies>
{deps_xml}    </dependencies>
</project>
"""

        return None

    def _create_readme(
        self,
        language: str,
        has_tests: bool,
        dependencies: list[str],
        metadata: Optional[dict] = None,
        file_list: Optional[list[str]] = None,
    ) -> str:
        """Create README.md content."""
        lang = language.lower()

        # Get run commands
        run_commands = {
            "python": "python src/main.py",
            "javascript": "node src/main.js",
            "typescript": "npx ts-node src/main.ts",
            "java": "mvn compile exec:java",
            "go": "go run src/main.go",
            "csharp": "dotnet run",
        }

        test_commands = {
            "python": "pytest tests/",
            "javascript": "npm test",
            "typescript": "npm test",
            "java": "mvn test",
            "go": "go test ./...",
            "csharp": "dotnet test",
        }

        install_commands = {
            "python": "pip install -r requirements.txt",
            "javascript": "npm install",
            "typescript": "npm install",
            "java": "mvn install",
            "go": "go mod download",
            "csharp": "dotnet restore",
        }

        run_cmd = run_commands.get(lang, f"# Run your {language} code")
        test_cmd = test_commands.get(lang, "# Run tests")
        install_cmd = install_commands.get(lang, "# Install dependencies")

        readme = f"""# Generated Code

This code was generated by the Intelligent Coding Agent.

## Language

{language.capitalize()}

"""

        if file_list:
            readme += "## Files\n\n"
            for f in file_list:
                readme += f"- `src/{f}`\n"
            readme += "\n"

        readme += f"""## Installation

```bash
{install_cmd}
```

## Usage

```bash
{run_cmd}
```

"""

        if has_tests:
            readme += f"""## Testing

```bash
{test_cmd}
```

"""

        if dependencies:
            readme += "## Dependencies\n\n"
            for dep in dependencies:
                readme += f"- {dep}\n"
            readme += "\n"

        if metadata:
            readme += "## Metadata\n\n"
            if "execution_id" in metadata:
                readme += f"- Execution ID: `{metadata['execution_id']}`\n"
            if "quality_score" in metadata:
                readme += f"- Quality Score: {metadata['quality_score']}/10\n"
            if "created_at" in metadata:
                readme += f"- Generated: {metadata['created_at']}\n"
            readme += "\n"

        readme += """---

*Generated by Intelligent Coding Agent*
"""

        return readme

    def _create_gitignore(self, language: str) -> str:
        """Create .gitignore content."""
        common = """# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

"""

        language_specific = {
            "python": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
.env
.venv/
.pytest_cache/
.coverage
htmlcov/
""",
            "javascript": """# Node
node_modules/
npm-debug.log
yarn-error.log
.npm
coverage/
""",
            "typescript": """# Node
node_modules/
npm-debug.log
yarn-error.log
.npm
coverage/

# TypeScript
dist/
*.js
*.d.ts
*.js.map
""",
            "java": """# Java
target/
*.class
*.jar
*.war
*.ear
*.log
""",
            "go": """# Go
bin/
pkg/
*.exe
*.test
*.out
vendor/
""",
            "csharp": """# C#
bin/
obj/
*.suo
*.user
*.csproj.user
packages/
""",
        }

        return common + language_specific.get(language.lower(), "")


# Singleton instance
_zip_service: Optional[ZipService] = None


def get_zip_service() -> ZipService:
    """Get the global ZIP service instance."""
    global _zip_service
    if _zip_service is None:
        _zip_service = ZipService()
    return _zip_service
