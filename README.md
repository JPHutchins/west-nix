# west-nix

Convert [West](https://docs.zephyrproject.org/latest/develop/west/index.html) manifests to reproducible Nix derivations.

## Overview

West is a meta-tool used by projects like Zephyr RTOS to manage multi-repository dependencies. This tool converts West manifests into Nix derivations, enabling:

- **Reproducible builds**: All dependencies pinned with SHA256 hashes
- **Offline builds**: Sources cached in Nix store
- **Efficient storage**: Shared derivations across projects, no duplication
- **Fast workspace setup**: Symlinks instead of cloning

## Tools

### `westlock`

Converts West frozen lockfiles to Nix format.

```bash
westlock < westlock.yaml > westlock.nix
```

**Input**: Frozen West manifest (YAML) from stdin
**Output**: Nix list of project derivations to stdout

### `westupdate`

Generates Nix lockfile from West manifest by running the full West workflow.

```bash
westupdate west.yml > westlock.nix
```

**What it does**:
1. Creates temporary workspace
2. Runs `west init` and `west update`
3. Generates frozen manifest with `west manifest --freeze`
4. Converts to Nix format via `westlock`

**Recommended**: Use `westupdate` for most workflows, as it handles manifest imports automatically.

## Library Functions

Use `west-nix` as a flake input to access library functions for setting up West workspaces:

```nix
{
  inputs.west-nix.url = "github:youruser/west-nix";

  outputs = { self, nixpkgs, west-nix }: {
    devShells.x86_64-linux.default =
      let
        westLib = west-nix.lib.x86_64-linux;
        westProjects = westLib.mkWestProjects ./westlock.nix;
        setupWorkspace = westLib.mkWestWorkspace { inherit westProjects; };
      in
      pkgs.mkShell {
        buildInputs = [ setupWorkspace ];
        shellHook = "setup-west-workspace";
      };
  };
}
```

See [examples/consumer-flake](./examples/consumer-flake) for a complete example.

### API

- **`mkWestProjects`**: Convert westlock.nix to derivations
- **`mkWestWorkspace`**: Create workspace setup script
- **`mkWestProject`**: Low-level single project builder

See [examples/consumer-flake/README.md](./examples/consumer-flake/README.md) for detailed API documentation.

## Quick Start

### 1. Install

```bash
# Run directly with nix
nix run github:youruser/west-nix

# Or enter dev shell
nix develop github:youruser/west-nix
```

### 2. Generate lockfile

From your West project:

```bash
westupdate west.yml > westlock.nix
```

### 3. Create flake

Add `west-nix` to your flake inputs and use the library functions to set up your workspace. See [examples/consumer-flake](./examples/consumer-flake).

## Development

```bash
# Enter dev shell
nix develop

# Run tests
cd tests
uv run pytest -v
```

## How It Works

1. **Fetching**: Each project is fetched using `fetchgit` with Nix SHA256 hashes
2. **Git repo creation**: Minimal git repos created with `manifest-rev` branch for West compatibility
3. **Workspace setup**: Projects symlinked to Nix store paths following West directory structure
4. **Read-only**: All sources are immutable Nix store paths

This approach is inspired by [west2nix](https://github.com/adisbladis/west2nix).

## License

MIT
