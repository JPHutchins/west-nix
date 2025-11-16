{
  description = "West manifest to Nix derivations converter";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          westlock-python = pkgs.python3Packages.buildPythonApplication {
            pname = "westlock";
            version = "0.1.0";
            pyproject = true;

            src = ./westlock/python;

            build-system = with pkgs.python3Packages; [
              hatchling
            ];

            dependencies = with pkgs.python3Packages; [
              pyyaml
              west
            ];

            nativeBuildInputs = [ pkgs.makeWrapper ];

            # Wrap to include nix-prefetch-git and git in PATH for westupdate
            makeWrapperArgs = [
              "--prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.nix-prefetch-git pkgs.git ]}"
            ];

            meta = with pkgs.lib; {
              description = "Convert West lockfiles to Nix derivations";
              license = licenses.mit;
              mainProgram = "westlock";
            };
          };

          default = self.packages.${system}.westlock-python;
        });

      apps = forAllSystems (system: {
        westlock = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/westlock";
        };
        default = self.apps.${system}.westlock;
      });

      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              python3
              uv
              nix-prefetch-git
              git
              python3Packages.west
            ];
          };
        });
    };
}
