"""The gate of ADR-0007 section 4 covers every package, enumerated rather than listed.

Trace: ADR-0007 section 4. Cross-package by nature, so it lives here rather than under a package
(ADR-0007 section 6).

The tiers contract holds by construction because `exhaustive` makes an unlisted package fail the
build. Its sibling cannot: `import-linter` has no `exhaustive` option for a `protected` contract,
so the module list is the one part of the gate a new package is silently missing from, which is the
same defect class the tiers contract was corrected for. This is the N2 catalogue enumeration
pointed at the gate's own configuration.
"""

import tomllib
from pathlib import Path
from typing import Any

import mapsift

STACK_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = Path(str(mapsift.__file__)).resolve().parent


def _packages_holding_models() -> set[str]:
    return {
        package.name
        for package in PACKAGE_ROOT.iterdir()
        if (package / "models.py").exists() or (package / "models" / "__init__.py").exists()
    }


def _protected_contracts() -> list[dict[str, Any]]:
    configuration = tomllib.loads((STACK_ROOT / "pyproject.toml").read_text())
    contracts: list[dict[str, Any]] = configuration["tool"]["importlinter"]["contracts"]
    return [contract for contract in contracts if contract["type"] == "protected"]


def test_every_package_holding_models_protects_them_from_every_other_package() -> None:
    """ADR-0007 section 4. Asserted as pairs rather than as two lists, because a `protected`
    contract applies every allowed importer to every protected module: naming two packages in one
    contract reads as coverage and is the permission it exists to withhold."""
    owns_its_own_models = {
        (f"mapsift.{package}.models", f"mapsift.{package}")
        for package in _packages_holding_models()
    }
    the_gate_allows = {
        (protected, importer)
        for contract in _protected_contracts()
        for protected in contract["protected_modules"]
        for importer in contract["allowed_importers"]
    }

    assert the_gate_allows == owns_its_own_models
