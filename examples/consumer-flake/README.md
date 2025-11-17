# West-Nix Consumer Example

This example demonstrates how to consume `west-nix` in your own flake to create reproducible West workspaces.

## Workflow

### 1. Generate the lockfile

From your West project directory (containing `west.yml`):

```bash
# Option A: If you already have a frozen lockfile (westlock.yaml)
westlock < westlock.yaml > westlock.nix

# Option B: Generate from west.yml manifest (recommended)
westupdate west.yml > westlock.nix
```

This creates `westlock.nix` containing all projects with locked revisions and Nix SHA256 hashes.

### 2. Create your flake

See [flake.nix](./flake.nix) for a complete example. The key parts:

```nix
inputs.west-nix.url = "github:youruser/west-nix";

outputs = { self, nixpkgs, west-nix }:
  let
    westLib = west-nix.lib.${system};
    westProjects = westLib.mkWestProjects ./westlock.nix;
    setupWorkspace = westLib.mkWestWorkspace { inherit westProjects; };
  in
  {
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = [ setupWorkspace ];
      shellHook = ''
        setup-west-workspace
      '';
    };
  };
```

### 3. Enter the dev shell

```bash
nix develop
```

This will:
- Fetch all West projects from the Nix store (cached, reproducible)
- Create a `west-workspace/` subdirectory with symlinks to Nix store
- Set up `west-workspace/.west/config` correctly
- Export `ZEPHYR_BASE` pointing to the workspace

All projects are read-only Nix store paths with minimal git repos for West compatibility.

The workspace lives in `./west-workspace/` (like `node_modules/` or `.venv/`), keeping your project directory clean.

**Note**: The workspace includes its own `.gitignore` that ignores all contents, so you don't need to manually configure git to ignore it. Just like Python's venv or Node's node_modules, the workspace can be regenerated at any time with `nix develop`.

### Project Structure

```
consumer-flake/
├── flake.nix           # Your project's Nix flake
├── west.yml            # West manifest (source of truth)
├── westlock.nix        # Generated lockfile (like package-lock.json)
└── west-workspace/     # Auto-generated (gitignored)
    ├── .west/
    │   └── config
    ├── zephyr/         # Symlink to Nix store
    └── modules/
        └── hal/
            ├── cmsis_6/    # Symlink to Nix store
            ├── nordic/     # Symlink to Nix store
            └── stm32/      # Symlink to Nix store
```

## What You Get

- **Reproducibility**: All projects pinned to exact SHAs with Nix hashes
- **Caching**: Projects shared across your system, no duplication
- **Offline builds**: All sources cached in Nix store
- **Fast workspace setup**: Just symlinks, no cloning

## Library API

### `mkWestProjects`

```nix
mkWestProjects :: Path | List -> List Derivation
```

Converts a `westlock.nix` file (or list of project attrs) into derivations.

### `mkWestWorkspace`

```nix
mkWestWorkspace :: { westProjects } -> Derivation
```

Creates a `setup-west-workspace` script that symlinks all projects.

**Parameters:**
- `westProjects`: List of project derivations from `mkWestProjects`

**Usage:**
```bash
# Required arguments: manifest-path, manifest-file, and workspace-path
setup-west-workspace <manifest-path> <manifest-file> <workspace-path>

# Example:
setup-west-workspace zephyr west.yml ./west-workspace
```

**Arguments:**
- `manifest-path`: Relative path from workspace root to the manifest project (should match a `path` in your `westlock.nix`)
- `manifest-file`: Name of the manifest file (commonly `west.yml`, but can be any filename)
- `workspace-path`: Where to create the workspace

### `mkWestProject`

```nix
mkWestProject :: { name, url, rev, sha256, ... } -> Derivation
```

Low-level function to create a single project derivation. Usually you'll use `mkWestProjects` instead.
