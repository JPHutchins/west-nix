# West-Nix Consumer Example

This example demonstrates how to consume `west-nix` in your own flake to create reproducible West workspaces.

## Quick Start

### 1. Generate westlock.nix (First Time Only)

```bash
nix run github:JPHutchins/west-nix#westupdate west.yml > westlock.nix
git add westlock.nix
```

### 2. Initialize your West workspace

```bash
nix run .#westinit . west.yml .west-workspace
```

That's it! Your West workspace is now set up with all dependencies from the Nix store.

---

## The Three Commands

West-nix provides three commands that mirror the West workflow:

1. **`westupdate`** - Generate/update the lockfile from `west.yml` (like `west update` but outputs Nix)
2. **`westlock`** - Convert existing West lockfile to Nix format (if you already have one)
3. **`westinit`** - Initialize a West workspace from the lockfile (the main command you'll use)

## Detailed Workflow

### Step 1: Generate the lockfile (First Time Setup)

From your West project directory (containing `west.yml`):

```bash
# Generate westlock.nix from west.yml manifest
nix run github:JPHutchins/west-nix#westupdate west.yml > westlock.nix

# Add to git (required for flakes to see it)
git add westlock.nix
```

This creates `westlock.nix` containing all projects with locked revisions and Nix SHA256 hashes.

**Why?** Just like `package-lock.json` or `Cargo.lock`, you need a lockfile before you can build/install. `westupdate` creates this lockfile from your `west.yml` manifest.

### 2. Create your flake

See [flake.nix](./flake.nix) for a complete example. The key parts:

```nix
inputs.west-nix.url = "github:JPHutchins/west-nix";

outputs = { self, nixpkgs, west-nix }:
  let
    westLib = west-nix.lib.${system};
    westProjects = westLib.mkWestProjects ./westlock.nix;
    westinit = westLib.mkWestWorkspace { inherit westProjects; };
  in
  {
    packages.${system} = {
      inherit westinit;
    };

    devShells.${system}.default = pkgs.mkShell {
      buildInputs = [ westinit ];
      shellHook = ''
        # Auto-setup workspace on shell entry
        if [ ! -L ".west-workspace/zephyr" ]; then
          westinit "$PWD" west.yml .west-workspace
        fi
        source .west-workspace/env.sh
      '';
    };
  };
```

### 3. Use the workspace

**Option A: Via dev shell (recommended)**
```bash
nix develop
```

This will automatically:
- Fetch all West projects from the Nix store (cached, reproducible)
- Create a `.west-workspace/` subdirectory with symlinks to Nix store
- Set up `.west-workspace/.west/config` correctly
- Export `ZEPHYR_BASE` and git config via sourcing `env.sh`

**Option B: Manual initialization**
```bash
nix run .#westinit . west.yml .west-workspace
source .west-workspace/env.sh
```

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

Creates a `westinit` script that symlinks all projects and sets up the workspace.

**Parameters:**
- `westProjects`: List of project derivations from `mkWestProjects`

**Usage:**
```bash
# Required arguments: manifest-path, manifest-file, and workspace-path
westinit <manifest-path> <manifest-file> <workspace-path>

# Example: Your repo is the manifest
westinit . west.yml ./.west-workspace

# Example: Using an imported project's manifest
westinit zephyr west.yml ./workspace
```

**Arguments:**
- `manifest-path`: Path to directory containing the manifest file (e.g., `.` for current dir, `zephyr` for zephyr project)
- `manifest-file`: Name of the manifest file (commonly `west.yml`)
- `workspace-path`: Where to create the workspace

### `mkWestProject`

```nix
mkWestProject :: { name, url, rev, sha256, ... } -> Derivation
```

Low-level function to create a single project derivation. Usually you'll use `mkWestProjects` instead.
