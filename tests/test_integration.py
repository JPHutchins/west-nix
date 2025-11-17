"""Integration test for complete west-nix workflow.

This test validates the end-to-end workflow:
1. Start with a west.yml manifest
2. Run westupdate to generate westlock.nix
3. Use library functions to create workspace
4. Verify workspace works with `west list`
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Final

import pytest

from conftest import Implementation, get_implementations


REPO_ROOT: Final = Path(__file__).parent.parent
FIXTURES_DIR: Final = Path(__file__).parent / "fixtures" / "westupdate"
INTEGRATION_FIXTURES_DIR: Final = Path(__file__).parent / "fixtures" / "integration"


@pytest.mark.parametrize("impl", get_implementations(), ids=lambda impl: impl.name)
def test_complete_workflow(
    impl: Implementation,
    build_implementations: dict[str, Path],
) -> None:
    """Test complete workflow from west.yml to working workspace."""

    westupdate_exe: Final = build_implementations[f"{impl.name}-westupdate"]

    # Use the zephyr-example-application fixture
    fixture_dir = FIXTURES_DIR / "zephyr-example-application"
    manifest_path = fixture_dir / "in" / "west.yml"

    assert manifest_path.exists(), f"Fixture not found: {manifest_path}"

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_dir = Path(tmpdir) / "workspace"
        workspace_dir.mkdir()

        print(f"\n=== Step 1: Run westupdate to generate westlock.nix ===")

        # Run westupdate to generate westlock.nix
        result = subprocess.run(
            [str(westupdate_exe), str(manifest_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=300,  # 5 minutes for cloning
        )

        assert result.returncode == 0, (
            f"westupdate failed:\n"
            f"stderr: {result.stderr}\n"
            f"stdout: {result.stdout}"
        )

        westlock_content = result.stdout
        westlock_path = workspace_dir / "westlock.nix"
        westlock_path.write_text(westlock_content)

        # Copy the west.yml to the workspace directory (simulating manifest.self scenario)
        west_yml_dest = workspace_dir / "west.yml"
        shutil.copy(manifest_path, west_yml_dest)

        print(f"✓ Generated westlock.nix with {westlock_content.count('name =')} projects")

        print(f"\n=== Step 2: Create flake that uses west-nix library ===")

        # Read flake template from fixture and substitute the west-nix path
        flake_template_path = INTEGRATION_FIXTURES_DIR / "workspace-setup" / "flake.nix"
        flake_content = flake_template_path.read_text()
        flake_content = flake_content.replace("WEST_NIX_PATH", f"path:{REPO_ROOT}")

        flake_path = workspace_dir / "flake.nix"
        flake_path.write_text(flake_content)

        print(f"✓ Created test flake.nix")

        print(f"\n=== Step 3: Run workspace setup ===")

        # Build the setup-workspace package
        result = subprocess.run(
            ["nix", "build", ".#default", "--out-link", "result-setup"],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )

        assert result.returncode == 0, (
            f"Failed to build workspace setup:\n"
            f"stderr: {result.stderr}\n"
            f"stdout: {result.stdout}"
        )

        setup_script = workspace_dir / "result-setup" / "bin" / "westinit"
        assert setup_script.exists(), "westinit script not found"

        print(f"✓ Built workspace setup script")

        # Run the setup script
        # Use workspace_dir as the manifest path (simulating a manifest.self scenario)
        west_workspace_dir = workspace_dir / "west-workspace"
        result = subprocess.run(
            [str(setup_script), str(workspace_dir), "west.yml", str(west_workspace_dir)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

        assert result.returncode == 0, (
            f"Failed to run workspace setup:\n"
            f"stderr: {result.stderr}\n"
            f"stdout: {result.stdout}"
        )

        print(f"✓ Workspace setup complete")
        print(f"  Output: {result.stdout}")

        print(f"\n=== Step 4: Verify workspace structure ===")

        # Check that workspace was created
        assert west_workspace_dir.exists(), "Workspace directory not created"
        assert (west_workspace_dir / ".west" / "config").exists(), ".west/config not created"
        assert (west_workspace_dir / ".gitignore").exists(), ".gitignore not created"

        # Check for expected symlinks
        assert (west_workspace_dir / "zephyr").is_symlink(), "zephyr symlink not created"

        print(f"✓ Workspace structure validated")

        print(f"\n=== Step 5: Verify west list works ===")

        # Run west list using nix develop to ensure west is available
        # Run from workspace_dir (which has flake.nix) and cd to the west workspace
        result = subprocess.run(
            ["nix", "develop", "--command", "bash", "-c", f"cd {west_workspace_dir} && west list"],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

        assert result.returncode == 0, (
            f"west list failed:\n"
            f"stderr: {result.stderr}\n"
            f"stdout: {result.stdout}"
        )

        west_list_output = result.stdout
        project_lines = [line for line in west_list_output.splitlines() if line.strip()]

        # Should have header + projects
        assert len(project_lines) >= 2, f"Expected multiple projects, got:\n{west_list_output}"

        # Verify zephyr is in the list
        assert any("zephyr" in line for line in project_lines), (
            f"zephyr not found in west list:\n{west_list_output}"
        )

        # Verify hal modules are in the list
        assert any("hal_nordic" in line or "nordic" in line for line in project_lines), (
            f"hal_nordic not found in west list:\n{west_list_output}"
        )

        print(f"✓ west list works! Found {len(project_lines) - 1} projects")
        print(f"\nFirst 10 lines of west list output:")
        for line in project_lines[:10]:
            print(f"  {line}")

        print(f"\n{'='*60}")
        print(f"✓ Integration test PASSED for {impl.name}")
        print(f"{'='*60}")
