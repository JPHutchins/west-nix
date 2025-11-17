{ pkgs }:

rec {
  # Import a single West project as a derivation
  # Takes: { name, path, url, rev, sha256, ... }
  # Returns: derivation with git repo at manifest-rev
  mkWestProject = pkgs.callPackage ./west-project.nix {};

  # Import a list of West projects from westlock.nix output
  # Takes: path to westlock.nix file or list of project attrs
  # Returns: list of derivations
  mkWestProjects = westProjectsData:
    let
      projects = if builtins.isPath westProjectsData || builtins.isString westProjectsData
                 then import westProjectsData
                 else westProjectsData;
    in
    map (proj: proj // { src = mkWestProject proj; }) projects;

  # Create a workspace setup script that symlinks all projects
  # Takes: { westProjects }
  # Returns: script derivation that requires manifest-path and workspace-path arguments
  mkWestWorkspace = { westProjects }:
    pkgs.callPackage ./westinit.nix {
      inherit westProjects;
    };
}
