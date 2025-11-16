{ lib
, writeShellScriptBin
, westProjects
}:

writeShellScriptBin "setup-west-workspace" ''
  set -euo pipefail

  echo "Setting up West workspace with Nix-managed dependencies..."

  # Get the workspace root (parent directory of current directory)
  # We assume we're running from zephyr-example-application
  WORKSPACE_ROOT="$(cd .. && pwd)"

  echo "Workspace root: $WORKSPACE_ROOT"

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
path = zephyr-example-application
file = west.yml
EOF

  echo "West workspace setup complete!"
''
