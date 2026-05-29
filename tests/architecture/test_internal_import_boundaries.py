"""AST guard: no cross-layer imports of tokdown.*._internal."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "tokdown"
LAYERS = frozenset({"domain", "application", "infrastructure", "interface"})


def _layer_for_path(path: Path) -> str | None:
    try:
        rel = path.relative_to(SRC_ROOT)
    except ValueError:
        return None
    if not rel.parts:
        return None
    layer = rel.parts[0]
    return layer if layer in LAYERS else None


def _internal_layer_from_module(module: str) -> str | None:
    for layer in sorted(LAYERS):
        prefix = f"tokdown.{layer}._internal"
        if module == prefix or module.startswith(f"{prefix}."):
            return layer
    return None


def _package_name(path: Path) -> str:
    rel = path.relative_to(SRC_ROOT.parent)
    parts = list(rel.with_suffix("").parts)
    if parts[-1] != "__init__":
        parts.pop()
    return ".".join(parts)


def _resolve_import_from(path: Path, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module
    package = _package_name(path)
    base_parts = package.split(".")
    if node.level > len(base_parts):
        return None
    base = base_parts[: len(base_parts) - node.level + 1]
    if node.module:
        return ".".join([*base, node.module])
    return ".".join(base)


def _collect_imported_modules(path: Path, tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve_import_from(path, node)
            if resolved:
                modules.append(resolved)
    return modules


def _may_import_internal(importer: Path, imported_layer: str) -> bool:
    rel = importer.relative_to(SRC_ROOT)
    importer_layer = _layer_for_path(importer)

    if rel.parts == ("domain", "api.py") and imported_layer == "domain":
        return True

    if (
        importer_layer is not None
        and len(rel.parts) >= 2
        and rel.parts[1] == "_internal"
        and imported_layer == importer_layer
    ):
        return True

    return importer_layer == imported_layer


@pytest.mark.parametrize(
    "py_file",
    sorted(SRC_ROOT.rglob("*.py")),
    ids=lambda p: str(p.relative_to(SRC_ROOT)),
)
def test_no_cross_layer_internal_imports(py_file: Path) -> None:
    importer_layer = _layer_for_path(py_file)
    if importer_layer is None:
        return

    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(py_file))
    for module in _collect_imported_modules(py_file, tree):
        imported_layer = _internal_layer_from_module(module)
        if imported_layer is None:
            continue
        if _may_import_internal(py_file, imported_layer):
            continue
        rel = py_file.relative_to(SRC_ROOT)
        pytest.fail(
            f"{rel} ({importer_layer}) must not import "
            f"tokdown.{imported_layer}._internal ({module!r})",
        )
