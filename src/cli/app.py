"""
Main CLI Application for API Assistant.

A command-line interface for parsing API specifications, managing
vector store collections, and searching API documentation.

Author: API Assistant Team
Date: 2025-12-27
"""

import json
import sys
from pathlib import Path
from typing import Any, List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint

from src.parsers import UnifiedFormatHandler, APIFormat

# Create Typer app
app = typer.Typer(
    name="api-assistant",
    help="API Assistant CLI - Parse, analyze, and search API specifications",
    add_completion=True,
)

# Rich console for pretty output
console = Console()

# Global state (initialized on demand)
_vector_store: Optional[Any] = None
_format_handler: Optional[UnifiedFormatHandler] = None


def get_vector_store():
    """Get or create vector store instance (lazy import)."""
    global _vector_store
    if _vector_store is None:
        # Lazy import to avoid loading heavy dependencies on CLI startup
        from src.core.vector_store import VectorStore
        _vector_store = VectorStore()
    return _vector_store


def get_format_handler() -> UnifiedFormatHandler:
    """Get or create format handler instance."""
    global _format_handler
    if _format_handler is None:
        _format_handler = UnifiedFormatHandler()
    return _format_handler


# ============================================================================
# PARSE COMMANDS
# ============================================================================

parse_app = typer.Typer(help="Parse API specifications")
app.add_typer(parse_app, name="parse")


@parse_app.command("file")
def parse_file(
    file_path: str = typer.Argument(..., help="Path to API specification file"),
    format_hint: Optional[str] = typer.Option(
        None, "--format", "-f", help="Format hint (openapi, graphql, postman)"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save parsed data to JSON file"
    ),
    add_to_store: bool = typer.Option(
        False, "--add", "-a", help="Add documents to vector store"
    ),
    show_documents: bool = typer.Option(
        False, "--show-docs", "-d", help="Show generated documents"
    ),
):
    """Parse a single API specification file."""
    try:
        # Validate file exists
        if not Path(file_path).exists():
            console.print(f"[red]Error: File not found: {file_path}[/red]")
            raise typer.Exit(1)

        # Parse format hint if provided
        format_type = None
        if format_hint:
            try:
                format_type = APIFormat[format_hint.upper()]
            except KeyError:
                console.print(f"[red]Error: Invalid format: {format_hint}[/red]")
                console.print(
                    f"Valid formats: {', '.join(f.value for f in APIFormat if f != APIFormat.UNKNOWN)}"
                )
                raise typer.Exit(1)

        # Parse file
        console.print(f"[cyan]Parsing {file_path}...[/cyan]")
        handler = get_format_handler()
        result = handler.parse_file(file_path, format_hint=format_type)

        # Display results
        console.print(f"[green]✓ Successfully parsed as {result['format']}[/green]\n")

        # Show statistics
        stats_table = Table(title="Parsing Statistics", show_header=False)
        stats_table.add_column("Key", style="cyan")
        stats_table.add_column("Value", style="yellow")

        for key, value in result["stats"].items():
            stats_table.add_row(key, str(value))

        console.print(stats_table)
        console.print(f"\n[cyan]Documents generated: {len(result['documents'])}[/cyan]")

        # Show documents if requested
        if show_documents:
            console.print("\n[bold]Generated Documents:[/bold]")
            for i, doc in enumerate(result["documents"][:5], 1):  # Show first 5
                console.print(f"\n[cyan]Document {i}:[/cyan]")
                console.print(Panel(doc["content"][:200] + "...", title="Content"))
                console.print(f"Metadata: {json.dumps(doc['metadata'], indent=2)}")
            if len(result["documents"]) > 5:
                console.print(
                    f"\n[dim]... and {len(result['documents']) - 5} more documents[/dim]"
                )

        # Add to vector store if requested
        if add_to_store:
            console.print("\n[cyan]Adding documents to vector store...[/cyan]")
            vector_store = get_vector_store()
            doc_ids = []
            for doc in result["documents"]:
                doc_id = vector_store.add_document(
                    content=doc["content"], metadata=doc["metadata"]
                )
                doc_ids.append(doc_id)
            console.print(
                f"[green]✓ Added {len(doc_ids)} documents to vector store[/green]"
            )

        # Save to file if requested
        if output:
            output_data = {
                "source_file": file_path,
                "format": result["format"],
                "stats": result["stats"],
                "documents": result["documents"],
            }
            with open(output, "w") as f:
                json.dump(output_data, f, indent=2)
            console.print(f"[green]✓ Saved results to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@parse_app.command("batch")
def parse_batch(
    files: List[str] = typer.Argument(..., help="List of API specification files"),
    add_to_store: bool = typer.Option(
        True, "--add/--no-add", help="Add documents to vector store"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", "-o", help="Save individual results to directory"
    ),
    summary: bool = typer.Option(True, "--summary/--no-summary", help="Show summary"),
):
    """Parse multiple API specification files in batch."""
    try:
        # Validate files
        valid_files = []
        for file_path in files:
            if Path(file_path).exists():
                valid_files.append(file_path)
            else:
                console.print(f"[yellow]Warning: File not found: {file_path}[/yellow]")

        if not valid_files:
            console.print("[red]Error: No valid files to process[/red]")
            raise typer.Exit(1)

        console.print(f"[cyan]Parsing {len(valid_files)} files...[/cyan]\n")

        # Parse files
        handler = get_format_handler()
        results = handler.parse_multiple(valid_files)

        # Display results
        console.print(f"[green]✓ Parsing complete[/green]\n")

        # Create summary table
        if summary:
            table = Table(title="Batch Parsing Results")
            table.add_column("File", style="cyan")
            table.add_column("Format", style="yellow")
            table.add_column("Documents", style="green")
            table.add_column("Status", style="magenta")

            for result in results["results"]:
                # Extract filename
                source = result.get("stats", {}).get("api_title", "N/A")
                if "collection_name" in result.get("stats", {}):
                    source = result["stats"]["collection_name"]

                table.add_row(
                    Path(source).name if source != "N/A" else "N/A",
                    result["format"],
                    str(len(result["documents"])),
                    "✓ Success",
                )

            for error in results["errors"]:
                table.add_row(
                    Path(error["file_path"]).name,
                    "unknown",
                    "0",
                    f"✗ {error['error'][:30]}...",
                )

            console.print(table)

        console.print(
            f"\n[green]Successful: {len(results['results'])}[/green] | "
            f"[red]Failed: {len(results['errors'])}[/red]"
        )

        # Add to vector store if requested
        if add_to_store and results["results"]:
            console.print("\n[cyan]Adding documents to vector store...[/cyan]")
            vector_store = get_vector_store()
            total_docs = 0

            for result in results["results"]:
                for doc in result["documents"]:
                    vector_store.add_document(
                        content=doc["content"], metadata=doc["metadata"]
                    )
                    total_docs += 1

            console.print(f"[green]✓ Added {total_docs} documents to vector store[/green]")

        # Save individual results if output directory specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            for i, result in enumerate(results["results"]):
                output_file = output_path / f"result_{i}.json"
                with open(output_file, "w") as f:
                    json.dump(result, f, indent=2)

            console.print(
                f"[green]✓ Saved {len(results['results'])} results to {output_dir}[/green]"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# SEARCH COMMANDS
# ============================================================================

search_app = typer.Typer(help="Search API documentation")
app.add_typer(search_app, name="search")


@search_app.command()
def query(
    query_text: str = typer.Argument(..., help="Search query"),
    n_results: int = typer.Option(5, "--limit", "-n", help="Number of results"),
    filter_source: Optional[str] = typer.Option(
        None, "--source", "-s", help="Filter by source (openapi, graphql, postman)"
    ),
    filter_method: Optional[str] = typer.Option(
        None, "--method", "-m", help="Filter by HTTP method (GET, POST, etc.)"
    ),
    show_content: bool = typer.Option(
        True, "--content/--no-content", help="Show document content"
    ),
):
    """Search the vector store for API documentation."""
    try:
        console.print(f"[cyan]Searching for: '{query_text}'...[/cyan]\n")

        # Build filter
        filter_dict = {}
        if filter_source:
            filter_dict["source"] = filter_source
        if filter_method:
            filter_dict["method"] = filter_method.upper()

        # Search
        vector_store = get_vector_store()
        results = vector_store.search(
            query=query_text, n_results=n_results, where=filter_dict if filter_dict else None
        )

        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        # Display results
        console.print(f"[green]Found {len(results)} results[/green]\n")

        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            score = result.get("score", 0)

            # Create result panel
            title = f"Result {i} | Score: {score:.4f}"
            if "name" in metadata:
                title += f" | {metadata['name']}"
            if "method" in metadata:
                title += f" | {metadata['method']}"

            if show_content:
                content = result.get("content", "")
                # Truncate if too long
                if len(content) > 300:
                    content = content[:300] + "..."
                console.print(Panel(content, title=title, border_style="cyan"))
            else:
                console.print(Panel(str(metadata), title=title, border_style="cyan"))

            console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# COLLECTION COMMANDS
# ============================================================================

collection_app = typer.Typer(help="Manage vector store collections")
app.add_typer(collection_app, name="collection")


@collection_app.command("info")
def collection_info():
    """Show information about the current collection."""
    try:
        vector_store = get_vector_store()
        stats = vector_store.get_stats()

        # Display stats
        table = Table(title="Collection Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Collection Name", stats.get("collection_name", "N/A"))
        table.add_row("Total Documents", str(stats.get("total_documents", 0)))
        table.add_row("Embedding Model", stats.get("embedding_model", "N/A"))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@collection_app.command("clear")
def collection_clear(
    confirm: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    )
):
    """Clear all documents from the collection."""
    try:
        if not confirm:
            confirmed = typer.confirm(
                "Are you sure you want to clear all documents?", abort=True
            )

        vector_store = get_vector_store()
        # Clear collection
        vector_store.collection.delete()
        console.print("[green]✓ Collection cleared successfully[/green]")

    except typer.Abort:
        console.print("[yellow]Operation cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# INFO COMMANDS
# ============================================================================

info_app = typer.Typer(help="Get information about supported formats and features")
app.add_typer(info_app, name="info")


@info_app.command("formats")
def info_formats():
    """Show supported API specification formats."""
    try:
        handler = get_format_handler()
        format_info = handler.get_format_info()

        console.print("\n[bold]Supported API Specification Formats:[/bold]\n")

        for format_name, info in format_info.items():
            table = Table(title=info["name"], show_header=False)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="yellow")

            table.add_row("Versions", ", ".join(info["versions"]))
            table.add_row("Extensions", ", ".join(info["extensions"]))
            table.add_row("Description", info["description"])

            console.print(table)
            console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@info_app.command("version")
def info_version():
    """Show API Assistant version."""
    from src.__version__ import __version__, __release_date__, __status__

    console.print("[bold]API Assistant CLI[/bold]")
    console.print(f"Version: {__version__}")
    console.print(f"Status: {__status__}")
    console.print(f"Released: {__release_date__}")
    console.print("\nAll 4 phases complete (Days 1-30) 🎉")


# ============================================================================
# EXPORT/IMPORT COMMANDS
# ============================================================================

export_app = typer.Typer(help="Export and import data")
app.add_typer(export_app, name="export")


@export_app.command("documents")
def export_documents(
    output_file: str = typer.Argument(..., help="Output JSON file path"),
    limit: Optional[int] = typer.Option(None, "--limit", "-n", help="Limit number of documents"),
):
    """Export all documents to JSON file."""
    try:
        console.print("[cyan]Exporting documents...[/cyan]")

        vector_store = get_vector_store()
        # Get all documents
        all_docs = vector_store.collection.get(limit=limit)

        export_data = {
            "total_documents": len(all_docs["ids"]),
            "documents": [
                {
                    "id": doc_id,
                    "content": content,
                    "metadata": metadata,
                }
                for doc_id, content, metadata in zip(
                    all_docs["ids"],
                    all_docs["documents"],
                    all_docs["metadatas"],
                )
            ],
        }

        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)

        console.print(
            f"[green]✓ Exported {len(export_data['documents'])} documents to {output_file}[/green]"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# DIAGRAM COMMANDS
# ============================================================================

diagram_app = typer.Typer(help="Generate Mermaid diagrams from API specifications")
app.add_typer(diagram_app, name="diagram")


@diagram_app.command("sequence")
def diagram_sequence(
    file_path: str = typer.Argument(..., help="Path to API specification file"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path (.mmd)"
    ),
    endpoint_filter: Optional[str] = typer.Option(
        None, "--endpoint", "-e", help="Filter by endpoint path (OpenAPI)"
    ),
):
    """Generate sequence diagram for API request/response flow."""
    try:
        from src.diagrams import MermaidGenerator

        # Parse file
        handler = get_format_handler()
        result = handler.parse_file(file_path)

        diagrams_generated = 0

        if result["format"] == "openapi":
            # OpenAPI endpoints
            parsed_doc = result["data"]
            endpoints = parsed_doc.endpoints

            if endpoint_filter:
                endpoints = [e for e in endpoints if endpoint_filter in e.path]

            if not endpoints:
                console.print("[yellow]No matching endpoints found[/yellow]")
                return

            # Generate diagram for first matching endpoint
            endpoint = endpoints[0]
            diagram = MermaidGenerator.generate_sequence_diagram_from_endpoint(endpoint)

            console.print(f"\n[cyan]Sequence Diagram: {endpoint.method.upper()} {endpoint.path}[/cyan]\n")
            console.print(Panel(diagram.to_mermaid(), title="Mermaid Diagram"))

            if output:
                MermaidGenerator.save_diagram(diagram, output)
                console.print(f"\n[green]✓ Saved to {output}[/green]")

            diagrams_generated = 1

        elif result["format"] == "postman":
            # Postman requests
            collection = result["data"]
            requests = collection.requests

            if not requests:
                console.print("[yellow]No requests found[/yellow]")
                return

            # Generate diagram for first request
            request = requests[0]
            diagram = MermaidGenerator.generate_sequence_diagram_from_postman(request)

            console.print(f"\n[cyan]Sequence Diagram: {request.name}[/cyan]\n")
            console.print(Panel(diagram.to_mermaid(), title="Mermaid Diagram"))

            if output:
                MermaidGenerator.save_diagram(diagram, output)
                console.print(f"\n[green]✓ Saved to {output}[/green]")

            diagrams_generated = 1

        else:
            console.print(f"[yellow]Sequence diagrams not supported for {result['format']} format[/yellow]")

        if diagrams_generated:
            console.print(f"\n[green]Generated {diagrams_generated} sequence diagram(s)[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@diagram_app.command("er")
def diagram_er(
    file_path: str = typer.Argument(..., help="Path to GraphQL schema file"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path (.mmd)"
    ),
    types: Optional[str] = typer.Option(
        None, "--types", "-t", help="Comma-separated list of types to include"
    ),
):
    """Generate entity relationship diagram from GraphQL schema."""
    try:
        from src.diagrams import MermaidGenerator

        # Parse file
        handler = get_format_handler()
        result = handler.parse_file(file_path)

        if result["format"] != "graphql":
            console.print("[red]ER diagrams only supported for GraphQL schemas[/red]")
            raise typer.Exit(1)

        schema = result["data"]

        # Parse type filter
        include_types = None
        if types:
            include_types = set(t.strip() for t in types.split(","))

        # Generate diagram
        diagram = MermaidGenerator.generate_er_diagram_from_graphql(
            schema, include_types=include_types
        )

        console.print("\n[cyan]Entity Relationship Diagram[/cyan]\n")
        console.print(Panel(diagram.to_mermaid(), title="Mermaid Diagram"))

        if output:
            MermaidGenerator.save_diagram(diagram, output)
            console.print(f"\n[green]✓ Saved to {output}[/green]")

        console.print(f"\n[green]Generated ER diagram with {len(diagram.entities)} entities[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@diagram_app.command("auth")
def diagram_auth(
    auth_type: str = typer.Argument(..., help="Authentication type (bearer, oauth2, apikey, basic)"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path (.mmd)"
    ),
):
    """Generate authentication flow diagram."""
    try:
        from src.diagrams import MermaidGenerator

        valid_types = ["bearer", "oauth2", "apikey", "basic"]
        if auth_type.lower() not in valid_types:
            console.print(f"[red]Invalid auth type. Choose from: {', '.join(valid_types)}[/red]")
            raise typer.Exit(1)

        # Generate diagram
        diagram = MermaidGenerator.generate_auth_flow(auth_type.lower())

        console.print(f"\n[cyan]{auth_type.upper()} Authentication Flow[/cyan]\n")
        console.print(Panel(diagram.to_mermaid(), title="Mermaid Diagram"))

        if output:
            MermaidGenerator.save_diagram(diagram, output)
            console.print(f"\n[green]✓ Saved to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@diagram_app.command("overview")
def diagram_overview(
    file_path: str = typer.Argument(..., help="Path to OpenAPI specification file"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path (.mmd)"
    ),
):
    """Generate API overview flowchart."""
    try:
        from src.diagrams import MermaidGenerator

        # Parse file
        handler = get_format_handler()
        result = handler.parse_file(file_path)

        if result["format"] != "openapi":
            console.print("[red]Overview diagrams only supported for OpenAPI specs[/red]")
            raise typer.Exit(1)

        parsed_doc = result["data"]

        # Generate diagram
        diagram = MermaidGenerator.generate_api_overview_flow(parsed_doc)

        console.print(f"\n[cyan]API Overview: {parsed_doc.title}[/cyan]\n")
        console.print(Panel(diagram.to_mermaid(), title="Mermaid Diagram"))

        if output:
            MermaidGenerator.save_diagram(diagram, output)
            console.print(f"\n[green]✓ Saved to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# SESSION COMMANDS
# ============================================================================

session_app = typer.Typer(help="Manage user sessions")
app.add_typer(session_app, name="session")


@session_app.command("create")
def session_create(
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="User identifier"),
    ttl: int = typer.Option(60, "--ttl", "-t", help="Session TTL in minutes"),
    collection: Optional[str] = typer.Option(
        None, "--collection", "-c", help="Collection name for this session"
    ),
):
    """Create a new user session."""
    try:
        from src.sessions import get_session_manager

        manager = get_session_manager()
        session = manager.create_session(
            user_id=user_id, ttl_minutes=ttl, collection_name=collection
        )

        console.print("\n[green]✓ Session created successfully[/green]\n")

        # Display session info
        table = Table(title="Session Details", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Session ID", session.session_id)
        table.add_row("User ID", session.user_id or "Anonymous")
        table.add_row("Created At", session.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Expires At", session.expires_at.strftime("%Y-%m-%d %H:%M:%S") if session.expires_at else "Never")
        table.add_row("Status", session.status.value)
        table.add_row("Collection", session.collection_name or "None")

        console.print(table)
        console.print(f"\n[dim]Use this session ID: {session.session_id}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@session_app.command("list")
def session_list(
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="Filter by user ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (active, inactive, expired)"),
):
    """List all sessions with optional filters."""
    try:
        from src.sessions import get_session_manager, SessionStatus

        manager = get_session_manager()

        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = SessionStatus(status.lower())
            except ValueError:
                console.print(f"[red]Invalid status. Choose from: active, inactive, expired[/red]")
                raise typer.Exit(1)

        sessions = manager.list_sessions(user_id=user_id, status=status_filter)

        if not sessions:
            console.print("[yellow]No sessions found[/yellow]")
            return

        # Display sessions table
        table = Table(title=f"Sessions ({len(sessions)} total)")
        table.add_column("Session ID", style="cyan")
        table.add_column("User ID", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Created", style="blue")
        table.add_column("Last Accessed", style="blue")
        table.add_column("Messages", style="green")

        for session in sessions:
            table.add_row(
                session.session_id[:8] + "...",
                session.user_id or "Anonymous",
                session.status.value,
                session.created_at.strftime("%H:%M:%S"),
                session.last_accessed.strftime("%H:%M:%S"),
                str(len(session.conversation_history)),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@session_app.command("info")
def session_info(
    session_id: str = typer.Argument(..., help="Session ID"),
    show_history: bool = typer.Option(False, "--history", "-h", help="Show conversation history"),
):
    """Show detailed information about a session."""
    try:
        from src.sessions import get_session_manager

        manager = get_session_manager()
        session = manager.get_session(session_id)

        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            raise typer.Exit(1)

        # Display session details
        table = Table(title="Session Details", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Session ID", session.session_id)
        table.add_row("User ID", session.user_id or "Anonymous")
        table.add_row("Status", session.status.value)
        table.add_row("Created At", session.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Last Accessed", session.last_accessed.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Expires At", session.expires_at.strftime("%Y-%m-%d %H:%M:%S") if session.expires_at else "Never")
        table.add_row("Collection", session.collection_name or "None")
        table.add_row("Messages", str(len(session.conversation_history)))

        console.print(table)

        # Display settings
        console.print("\n[bold]Session Settings:[/bold]")
        settings_table = Table(show_header=False)
        settings_table.add_column("Setting", style="cyan")
        settings_table.add_column("Value", style="yellow")

        settings_table.add_row("Search Mode", session.settings.default_search_mode)
        settings_table.add_row("Results Limit", str(session.settings.default_n_results))
        settings_table.add_row("Use Reranking", str(session.settings.use_reranking))
        settings_table.add_row("Show Scores", str(session.settings.show_scores))
        settings_table.add_row("Max Content Length", str(session.settings.max_content_length))

        console.print(settings_table)

        # Show conversation history if requested
        if show_history and session.conversation_history:
            console.print(f"\n[bold]Conversation History ({len(session.conversation_history)} messages):[/bold]\n")
            for i, msg in enumerate(session.conversation_history[-10:], 1):  # Last 10 messages
                role_color = "green" if msg.role == "user" else "blue"
                console.print(f"[{role_color}]{msg.role}[/{role_color}] ({msg.timestamp.strftime('%H:%M:%S')}): {msg.content[:100]}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@session_app.command("delete")
def session_delete(
    session_id: str = typer.Argument(..., help="Session ID to delete"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a session."""
    try:
        from src.sessions import get_session_manager

        if not confirm:
            confirmed = typer.confirm(
                f"Are you sure you want to delete session {session_id}?", abort=True
            )

        manager = get_session_manager()
        deleted = manager.delete_session(session_id)

        if deleted:
            console.print(f"[green]✓ Session {session_id} deleted successfully[/green]")
        else:
            console.print(f"[yellow]Session not found: {session_id}[/yellow]")

    except typer.Abort:
        console.print("[yellow]Operation cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@session_app.command("extend")
def session_extend(
    session_id: str = typer.Argument(..., help="Session ID to extend"),
    minutes: int = typer.Option(60, "--minutes", "-m", help="Minutes to add to expiration"),
):
    """Extend session expiration time."""
    try:
        from src.sessions import get_session_manager

        manager = get_session_manager()
        session = manager.extend_session(session_id, minutes)

        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓ Session extended by {minutes} minutes[/green]")
        console.print(f"New expiration: {session.expires_at.strftime('%Y-%m-%d %H:%M:%S') if session.expires_at else 'Never'}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@session_app.command("cleanup")
def session_cleanup():
    """Remove all expired sessions."""
    try:
        from src.sessions import get_session_manager

        manager = get_session_manager()
        count = manager.cleanup_expired_sessions()

        if count > 0:
            console.print(f"[green]✓ Cleaned up {count} expired session(s)[/green]")
        else:
            console.print("[yellow]No expired sessions found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@session_app.command("stats")
def session_stats():
    """Show session statistics."""
    try:
        from src.sessions import get_session_manager

        manager = get_session_manager()
        stats = manager.get_stats()

        # Display stats
        table = Table(title="Session Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Total Sessions", str(stats["total_sessions"]))
        table.add_row("Active Sessions", str(stats["active_sessions"]))
        table.add_row("Inactive Sessions", str(stats["inactive_sessions"]))
        table.add_row("Expired Sessions", str(stats["expired_sessions"]))
        table.add_row("Unique Users", str(stats["unique_users"]))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# MAIN CALLBACK
# ============================================================================

@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    API Assistant CLI - Parse, analyze, and search API specifications.

    Supports GraphQL, OpenAPI, and Postman collection formats.
    """
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")


if __name__ == "__main__":
    app()
