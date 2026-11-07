#!/bin/zsh
# Build the playable site in web/ from your own copy of the game's installer.
# Leaves web/index.html and web/shim.js (hand-written) alone.
#
# usage: tools/build.sh [path/to/HouseMD-Setup.exe]
#
# Needs: 7zz (7-Zip), python3, npm, curl, and a Java 11+ runtime for the JPEXS
# decompiler (set JAVA=/path/to/bin/java if java is not on PATH).
set -euo pipefail
cd "${0:A:h}/.."

INSTALLER="${1:-HouseMD-Setup.exe}"
INSTALLER_SHA256=dcaa7694c31c342823509810b9657c545a8ecad241bde4d24b5b6d87a6a908d2
JAVA="${JAVA:-java}"
RUFFLE_VERSION=0.7.1
FFDEC_VERSION=26.4.0
FFDEC=tools/ffdec/ffdec-cli.jar

if [[ ! -f "$INSTALLER" ]]; then
  echo "Installer not found: $INSTALLER" >&2
  echo "Put HouseMD-Setup.exe (from the game disc) in the repo root or pass its path." >&2
  exit 1
fi
if [[ "$(shasum -a 256 "$INSTALLER" | cut -d' ' -f1)" != "$INSTALLER_SHA256" ]]; then
  echo "Warning: $INSTALLER is not the known 2010 English release; the patches may not apply." >&2
fi

# JPEXS Free Flash Decompiler, used only to apply one bytecode patch.
if [[ ! -f "$FFDEC" ]]; then
  echo "Downloading JPEXS decompiler $FFDEC_VERSION..."
  mkdir -p tools/ffdec
  curl -fsSL -o tools/ffdec/ffdec.zip \
    "https://github.com/jindrapetrik/jpexs-decompiler/releases/download/version$FFDEC_VERSION/ffdec_$FFDEC_VERSION.zip"
  (cd tools/ffdec && unzip -q ffdec.zip && rm ffdec.zip)
fi

rm -rf build-tmp && mkdir build-tmp
7zz x -y -obuild-tmp/unpacked "$INSTALLER" -x'!$PLUGINSDIR' >/dev/null

# Files SWFKit embedded inside house.exe (main.swf, scripts, text).
python3 -I tools/swfkit_unpack.py build-tmp/unpacked/house.exe bin-debug web >/dev/null
# Files the installer puts next to the exe.
cp -R build-tmp/unpacked/{swf,img,snd,music,help} web/
rm -f web/bin-debug/{main.html,AC_OETags.js,playerProductInstall.swf}
find web -name Thumbs.db -delete

# Browser fixes to main.swf (see tools/patch_main.py and tools/patches/).
cp web/bin-debug/main.swf build-tmp/main.orig.swf
python3 -I tools/patch_main.py build-tmp/main.orig.swf build-tmp/main.step1.swf
"$JAVA" -Djava.awt.headless=true -jar "$FFDEC" -replace build-tmp/main.step1.swf web/bin-debug/main.swf \
  mx.core.UIComponent tools/patches/UIComponent_alpha_set.pcode 49 >/dev/null

# Self-hosted Ruffle.
(cd build-tmp && npm pack "@ruffle-rs/ruffle@$RUFFLE_VERSION" --silent >/dev/null && tar xzf ruffle-rs-ruffle-*.tgz)
mkdir -p web/ruffle && cp build-tmp/package/*.{js,wasm} build-tmp/package/LICENSE_* web/ruffle/

# Landing page art: the game's icon, and box art if you have a cover.jpg.
mkdir -p web/assets
cp build-tmp/unpacked/house.ico web/favicon.ico
if [[ -f cover.jpg ]]; then
  cp cover.jpg web/assets/cover.jpg
else
  echo "No cover.jpg in the repo root; the landing page will show no box art." >&2
fi

rm -rf build-tmp
echo "Built web/. Serve it with: python3 tools/serve.py 8642 web"
