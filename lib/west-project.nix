{ fetchgit, git, runCommand }:

{ name
, url
, rev
, sha256
, ...
}:

let
  src = fetchgit {
    inherit url rev sha256;
    name = "${name}-src";
    leaveDotGit = false;
    deepClone = false;
  };
in
runCommand "${name}-src" {} ''
  cp -r ${src} $out
  chmod -R +w $out

  # Create a minimal git repo with manifest-rev branch for West
  # Following west2nix approach: https://github.com/adisbladis/west2nix
  cd $out
  ${git}/bin/git init --initial-branch=main
  ${git}/bin/git config user.email 'nix@example.com'
  ${git}/bin/git config user.name 'Nix Build'
  ${git}/bin/git add -A
  ${git}/bin/git commit -m 'Nix-fetched source at ${rev}'
  ${git}/bin/git branch manifest-rev
  ${git}/bin/git checkout --detach manifest-rev
''
