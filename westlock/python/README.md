# west-to-nix

Converts West lockfiles (`westlock.yaml`) to Nix derivation expressions.

## Usage

```bash
# From the zephyr-example-application directory
nix run .#west-to-nix

# Or manually with uv
cd tools/west-to-nix
uv run west-to-nix
```

## What it does

1. Reads `westlock.yaml` from the workspace root
2. Validates the structure using strict dataclass schemas
3. For each project, prefetches the git repository to get SHA256 hash
4. Generates `nix/generated/west-projects.nix` with all projects as Nix expressions

## Requirements

- Python 3.11+
- `nix-prefetch-git` available in PATH
- Valid `westlock.yaml` in workspace root
