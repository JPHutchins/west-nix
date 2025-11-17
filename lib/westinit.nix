{ lib
, writeShellScriptBin
, westProjects
}:

writeShellScriptBin "westinit" ''
  set -euo pipefail

  if [ $# -ne 3 ]; then
    echo "Usage: westinit <manifest-path> <manifest-file> <workspace-path>"
    echo ""
    echo "Arguments:"
    echo "  manifest-path     Path to directory containing the manifest file"
    echo "                    Can be absolute or relative (e.g., '.', '/path/to/app', 'zephyr')"
    echo "  manifest-file     Name of the manifest file (e.g., 'west.yml', 'manifest.yaml')"
    echo "  workspace-path    Path where the West workspace will be created"
    echo ""
    echo "Examples:"
    echo "  # Your repo is the manifest (has manifest.self in west.yml)"
    echo "  westinit . west.yml ./.west-workspace"
    echo ""
    echo "  # Using an imported project's manifest"
    echo "  westinit zephyr west.yml ./workspace"
    exit 1
  fi

  MANIFEST_PATH="$1"
  MANIFEST_FILE="$2"
  WORKSPACE_ROOT="$3"

  echo "Setting up West workspace with Nix-managed dependencies..."

  # Disable git dubious ownership check for Nix store paths
  # This allows git operations on read-only Nix store repositories
  # Users will also need this in their shell environment when running west commands
  export GIT_CONFIG_COUNT=1
  export GIT_CONFIG_KEY_0="safe.directory"
  export GIT_CONFIG_VALUE_0="*"

  # Create workspace root if it doesn't exist
  mkdir -p "$WORKSPACE_ROOT"
  WORKSPACE_ROOT="$(cd "$WORKSPACE_ROOT" && pwd)"

  # Convert manifest path to absolute if it isn't already
  if [[ "$MANIFEST_PATH" != /* ]]; then
    # Relative path - make it absolute from current directory
    MANIFEST_PATH="$(cd "$MANIFEST_PATH" && pwd)"
  fi

  # Compute relative path from workspace to manifest directory
  MANIFEST_REL_PATH="$(realpath --relative-to="$WORKSPACE_ROOT" "$MANIFEST_PATH")"

  echo "Workspace root: $WORKSPACE_ROOT"
  echo "Manifest directory: $MANIFEST_PATH"
  echo "Manifest relative path: $MANIFEST_REL_PATH"

  # Create directory structure and symlink each project
  ${lib.concatMapStringsSep "\n" (proj: ''
    mkdir -p "$WORKSPACE_ROOT/$(dirname "${proj.path}")"
    ln -sfn "${proj.src}" "$WORKSPACE_ROOT/${proj.path}"
  '') westProjects}

  # Ensure .west directory exists with correct config
  mkdir -p "$WORKSPACE_ROOT/.west"

  # Set up .west/config
  cat > "$WORKSPACE_ROOT/.west/config" <<EOF
[manifest]
path = $MANIFEST_REL_PATH
file = $MANIFEST_FILE
EOF

  # Create .gitignore in workspace (like venv, node_modules, etc.)
  cat > "$WORKSPACE_ROOT/.gitignore" <<'EOF'
# This workspace is managed by Nix and should not be committed
# It can be regenerated with: nix develop
*
EOF

  # Create env.sh for users to source when using the workspace manually
  cat > "$WORKSPACE_ROOT/env.sh" <<'ENVEOF'
# Source this file to set up your environment for this West workspace
# Usage: source .west-workspace/env.sh

# Disable git dubious ownership check for Nix store paths
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="safe.directory"
export GIT_CONFIG_VALUE_0="*"
ENVEOF

  # Add ZEPHYR_BASE if zephyr project exists
  if [ -d "$WORKSPACE_ROOT/zephyr" ]; then
    cat >> "$WORKSPACE_ROOT/env.sh" <<ENVEOF

# Set ZEPHYR_BASE for Zephyr-based projects
export ZEPHYR_BASE=$WORKSPACE_ROOT/zephyr
ENVEOF
  fi

  echo ""
  echo "West workspace setup complete!"
  echo ""
  echo "To use this workspace, either:"
  echo "  1. Run 'nix develop' (recommended - sets up environment automatically)"
  echo "  2. Source the environment file: source $WORKSPACE_ROOT/env.sh"
''
