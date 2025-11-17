{
  description = "Integration test workspace";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # WEST_NIX_PATH will be replaced by the test
    west-nix.url = "WEST_NIX_PATH";
  };

  outputs = { self, nixpkgs, west-nix }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      westLib = west-nix.lib.${system};

      westProjects = westLib.mkWestProjects ./westlock.nix;
      westinit = westLib.mkWestWorkspace {
        inherit westProjects;
      };
    in
    {
      packages.${system}.default = westinit;

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          westinit
        ];

        shellHook = ''
          # Set up workspace
          WORKSPACE_DIR="$PWD/west-workspace"
          if [ ! -L "$WORKSPACE_DIR/zephyr" ]; then
            westinit "$PWD" west.yml "$WORKSPACE_DIR"
          fi

          # Source the workspace environment
          if [ -f "$WORKSPACE_DIR/env.sh" ]; then
            source "$WORKSPACE_DIR/env.sh"
          fi
        '';
      };
    };
}
