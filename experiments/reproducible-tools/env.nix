# The tools the experiments in this repository use, pinned by content hash.
let
  nixpkgs = builtins.fetchTarball {
    url = "https://releases.nixos.org/nixos/unstable/nixos-26.11pre1078696.4975466d3247/nixexprs.tar.xz";
    sha256 = "1svxa407zymz2qgygwcg1v67zxjw402gaj925bdvqi3sqkm3770i";
  };
  pkgs = import nixpkgs { };
in
pkgs.mkShell {
  packages = [ pkgs.python3 pkgs.git pkgs.gnupg ];
}
