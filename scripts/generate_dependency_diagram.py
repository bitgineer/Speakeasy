#!/usr/bin/env python3
"""Generate and maintain a module dependency diagram for faster-whisper-hotkey.

This script analyzes Python source files in the src/faster_whisper_hotkey directory
and generates a visual dependency diagram using Graphviz.

Usage:
    python scripts/generate_dependency_diagram.py [--output OUTPUT] [--format FORMAT]
"""

import argparse
import ast
import os
import sys
from pathlib import Path
from collections import defaultdict


def is_local_import(node, module_name: str, package_name: str = "faster_whisper_hotkey") -> bool:
    """Check if an import is from the local package."""
    if module_name.startswith(package_name):
        return True
    if module_name.startswith("."):
        return True
    return False


def get_local_module_name(import_name: str, package_name: str = "faster_whisper_hotkey") -> str:
    """Convert import name to local module name."""
    if import_name.startswith(package_name):
        # Remove package prefix and get the module name
        relative = import_name[len(package_name):].lstrip(".")
        if not relative:
            # Reference to package itself (e.g., "from . import version")
            return package_name.split(".")[-1]
        # Handle submodules
        parts = relative.split(".")
        return parts[0]
    if import_name.startswith("."):
        # Relative import - count the dots
        dots = len(import_name) - len(import_name.lstrip("."))
        # Remove dots and any submodules
        rest = import_name.lstrip(".")
        if rest.startswith("."):
            rest = rest.lstrip(".")
        parts = rest.split(".")
        return parts[0] if parts[0] else package_name.split(".")[-1]
    return import_name


def extract_imports(file_path: Path, local_modules: set, package_name: str = "faster_whisper_hotkey") -> set:
    """Extract all local imports from a Python file."""
    imports = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if is_local_import(alias.name, package_name):
                        module_name = get_local_module_name(alias.name, package_name)
                        if module_name in local_modules:
                            imports.add(module_name)
            elif isinstance(node, ast.ImportFrom):
                # node.level > 0 means relative import (e.g., level=1 for ".", level=2 for "..")
                if node.module:
                    # For relative imports (level > 0), check each part
                    if node.level > 0:
                        # This is a relative import like "from .settings import ..."
                        # node.module here is just "settings" or "path.to.module"
                        # Check if any part matches a local module
                        for part in node.module.split("."):
                            if part in local_modules:
                                imports.add(part)
                                break
                    else:
                        # Absolute import
                        if is_local_import(node.module, package_name):
                            module_name = get_local_module_name(node.module, package_name)
                            if module_name in local_modules:
                                imports.add(module_name)
                elif node.level > 0:
                    # "from . import X" case - node.module is None
                    # This imports from the package itself
                    imports.add(package_name.split(".")[-1])
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

    return imports


def analyze_directory(source_dir: Path, package_name: str = "faster_whisper_hotkey"):
    """Analyze all Python files in a directory and build dependency graph."""
    dependencies = defaultdict(set)
    modules = set()

    # First pass: collect all module names
    for py_file in source_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            module_name = package_name.split(".")[-1]
        else:
            module_name = py_file.stem
        modules.add(module_name)

    # Second pass: extract dependencies
    for py_file in source_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            module_name = package_name.split(".")[-1]
        else:
            module_name = py_file.stem

        imports = extract_imports(py_file, modules, package_name)

        # Add dependencies (no self-imports)
        for imp in imports:
            if imp != module_name:
                dependencies[module_name].add(imp)

    return modules, dependencies


def detect_circular_dependencies(dependencies: dict) -> list:
    """Detect circular dependencies using depth-first search."""
    circles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in dependencies.get(node, []):
            if neighbor not in visited:
                result = dfs(neighbor)
                if result:
                    return result
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]

        path.pop()
        rec_stack.remove(node)
        return None

    for module in dependencies:
        if module not in visited:
            cycle = dfs(module)
            if cycle:
                circles.append(cycle)

    return circles


def categorize_modules(modules: set) -> dict:
    """Categorize modules by their purpose."""
    categories = {
        "entry": {"__main__", "cli"},
        "core": {"transcriber", "models", "settings"},
        "ui": {"gui", "ui", "history_panel", "hotkey_dialog", "shortcuts_panel", "onboarding"},
        "config": {"config", "transcribe"},
        "platform": {"clipboard", "paste", "terminal"},
        "utils": {"shortcuts_manager"},
    }

    # Assign uncategorized modules to 'other'
    categorized = defaultdict(list)
    for module in modules:
        assigned = False
        for category, members in categories.items():
            if module in members:
                categorized[category].append(module)
                assigned = True
                break
        if not assigned:
            categorized["other"].append(module)

    return dict(categorized)


def generate_dot_graph(
    modules: set,
    dependencies: dict,
    categorized: dict,
    show_circles: bool = True
) -> str:
    """Generate Graphviz DOT format graph."""

    # Detect circular dependencies
    circles = detect_circular_dependencies(dependencies) if show_circles else []

    dot = [
        'digraph faster_whisper_hotkey_deps {',
        '    // Graph settings',
        '    rankdir=TB;',
        '    splines=spline;',
        '    node [fontname="Arial", fontsize=10];',
        '    edge [fontname="Arial", fontsize=9, color="#555555"];',
        '',
        '    // Subgraphs for module categories',
        '',
    ]

    # Define colors for categories
    colors = {
        "entry": "#E8F5E9",  # Light green
        "core": "#E3F2FD",   # Light blue
        "ui": "#F3E5F5",     # Light purple
        "config": "#FFF3E0", # Light orange
        "platform": "#E0F2F1", # Light teal
        "utils": "#F1F8E9",  # Light lime
        "other": "#F5F5F5",  # Gray
    }

    # Create subgraphs for each category
    for category, category_modules in categorized.items():
        if not category_modules:
            continue

        dot.append(f'    subgraph cluster_{category} {{')
        dot.append(f'        label = "{category.upper()}";')
        dot.append(f'        style = filled;')
        dot.append(f'        color = "{colors.get(category, "#F5F5F5")}";')

        for module in sorted(category_modules):
            dot.append(f'        "{module}";')

        dot.append('    }')
        dot.append('')

    # Add dependency edges
    dot.append('    // Dependencies')
    for module, deps in sorted(dependencies.items()):
        for dep in sorted(deps):
            # Check if this edge is part of a circular dependency
            edge_style = ""
            for circle in circles:
                if len(circle) >= 2:
                    for i in range(len(circle) - 1):
                        if circle[i] == module and circle[i + 1] == dep:
                            edge_style = ' [color="#D32F2F", penwidth=2.5, label="cycle"]'
                            break

            dot.append(f'    "{module}" -> "{dep}"{edge_style};')

    # Add legend for circular dependencies if any
    if circles:
        dot.append('')
        dot.append('    // Legend')
        dot.append('    node [shape=plaintext];')
        dot.append('    legend [label=')
        dot.append('        <<table border="0" cellborder="1" cellspacing="0">')
        dot.append('        <tr><td colspan="2"><b>Legend</b></td></tr>')
        dot.append('        <tr><td bgcolor="#D32F2F">Red Edge</td><td>Circular Dependency</td></tr>')
        dot.append('        </table>>')
        dot.append('    ];')

    dot.append('}')
    return '\n'.join(dot)


def print_summary(modules: set, dependencies: dict, categorized: dict, circles: list):
    """Print a summary of the dependency analysis."""
    print("\n" + "=" * 60)
    print("MODULE DEPENDENCY ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"\nTotal modules: {len(modules)}")
    print(f"Total dependencies: {sum(len(deps) for deps in dependencies.values())}")

    print("\nModules by category:")
    for category, category_modules in sorted(categorized.items()):
        if category_modules:
            print(f"  {category.upper()}: {', '.join(sorted(category_modules))}")

    if circles:
        print(f"\n⚠️  CIRCULAR DEPENDENCIES DETECTED ({len(circles)}):")
        for i, circle in enumerate(circles, 1):
            print(f"  {i}. {' -> '.join(circle)}")
    else:
        print("\n✓ No circular dependencies detected!")

    print("\nDependency details:")
    for module in sorted(modules):
        deps = dependencies.get(module, set())
        if deps:
            print(f"  {module} -> {', '.join(sorted(deps))}")
        elif module not in dependencies:
            print(f"  {module} -> (no dependencies)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate module dependency diagram for faster-whisper-hotkey"
    )
    parser.add_argument(
        "--output", "-o",
        default="docs/dependencies.dot",
        help="Output file path (default: docs/dependencies.dot)"
    )
    parser.add_argument(
        "--format", "-f",
        default="dot",
        choices=["dot", "png", "svg", "pdf"],
        help="Output format (default: dot)"
    )
    parser.add_argument(
        "--source-dir", "-s",
        default="src/faster_whisper_hotkey",
        help="Source directory to analyze (default: src/faster_whisper_hotkey)"
    )
    parser.add_argument(
        "--package", "-p",
        default="faster_whisper_hotkey",
        help="Package name (default: faster_whisper_hotkey)"
    )
    parser.add_argument(
        "--no-circles", "-n",
        action="store_true",
        help="Don't highlight circular dependencies"
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only print summary, don't generate diagram"
    )

    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' not found.", file=sys.stderr)
        return 1

    # Analyze the codebase
    print(f"Analyzing {source_dir}...")
    modules, dependencies = analyze_directory(source_dir, args.package)
    categorized = categorize_modules(modules)
    circles = detect_circular_dependencies(dependencies)

    # Print summary
    print_summary(modules, dependencies, categorized, circles)

    if args.summary_only:
        return 0

    # Generate DOT graph
    dot_content = generate_dot_graph(modules, dependencies, categorized, not args.no_circles)

    # Determine output path
    output_path = Path(args.output)

    # Write output
    if args.format == "dot":
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dot_content, encoding="utf-8")
        print(f"\n✓ DOT file written to: {output_path}")
    else:
        # Need to generate using graphviz
        try:
            import graphviz

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Change extension based on format
            if output_path.suffix == ".dot":
                output_path = output_path.with_suffix(f".{args.format}")

            graph = graphviz.Source(dot_content)
            output_filename = str(output_path.with_suffix(""))
            graph.render(output_filename, format=args.format, cleanup=True)

            print(f"\n✓ {args.format.upper()} diagram written to: {output_path}")
        except ImportError:
            print(
                f"\nNote: To generate {args.format.upper()} output, install graphviz:",
                file=sys.stderr
            )
            print("  pip install graphviz", file=sys.stderr)
            print(
                "\nFalling back to DOT format. Use a Graphviz viewer or online tool:",
                file=sys.stderr
            )
            print("  https://dreampuf.github.io/GraphvizOnline/", file=sys.stderr)

            dot_path = output_path.with_suffix(".dot")
            dot_path.parent.mkdir(parents=True, exist_ok=True)
            dot_path.write_text(dot_content, encoding="utf-8")
            print(f"\n✓ DOT file written to: {dot_path}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
