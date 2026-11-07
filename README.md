# House M.D. browser port

Play the 2010 **House M.D.** PC game (Legacy Interactive / Glyphic
Entertainment) in a modern browser, using [Ruffle](https://ruffle.rs) to run
the original Flash content.

**This repo does not contain the game.** It holds the scripts and small
compatibility patches that turn your own copy of the Windows installer into a
static website.

## What you get

- The full game: all five cases, the minigames, cutscenes, music and voice.
- Saves (four profiles plus settings) kept in the browser's localStorage.
- A landing page with credits and legal info, and a toolbar with fullscreen.

## Build it

You need:

- `HouseMD-Setup.exe` from the original game (the 2010 English release;
  the build checks its SHA-256 and warns if it is a different version)
- [7-Zip](https://www.7-zip.org) as `7zz`, `python3`, `npm`, `curl`
- Java 11 or newer (only used to apply one bytecode patch)

Then:

    tools/build.sh path/to/HouseMD-Setup.exe

This fills `web/` with the game files, patches them, and downloads Ruffle 0.7.1
and the [JPEXS decompiler](https://github.com/jindrapetrik/jpexs-decompiler)
(into `tools/ffdec/`). If `java` is not on your PATH, set `JAVA=/path/to/java`.

Optional: put the box art as `cover.jpg` in the repo root before building and
the landing page will show it.

## Play it

    python3 tools/serve.py 8642 web

and open http://localhost:8642/. Any static web server works, but opening
`web/index.html` straight from disk (file://) does not. The built site is
about 350 MB, mostly images.

The intro logos run for about a minute and cannot be skipped; that is how the
original behaves.

## How the port works

The original game is a Flex 3 app (`main.swf`) wrapped in a SWFKit Windows
executable. The wrapper hid most of the game's files inside `house.exe` and
supplied a few services the browser does not have.

- `tools/swfkit_unpack.py` pulls the embedded files (main.swf, scene scripts,
  dialogue) out of `house.exe`.
- `web/shim.js` provides the wrapper calls the game makes: `getAppPath`,
  `getCloseFlag`, `ReadFromRegistry` / `WriteToRegistry` (saves, now in
  localStorage), and the fullscreen and quit commands. It also holds back
  very fast mouse releases, because the menus need press and release on
  different frames.
- `main.swf` gets two patches:
  1. `enterCustomSplash` busy-waits for an optional `splash1.png`. On Windows
     that file loaded synchronously; in a browser the loop never ends and the
     tab freezes. `tools/patch_main.py` removes the loop.
  2. The game hides text-box backgrounds by setting their alpha to 0 and relies
     on Flash Player ignoring alpha for system-font text. Ruffle applies the
     alpha, so all dialogue was invisible. The Flex `UIComponent` alpha setter
     is replaced (`tools/patches/UIComponent_alpha_set.pcode`) so alpha 0 on a
     TextInput or TextArea removes the background and border instead.
- `web/index.html` scales the fixed 800x600 stage to the window and draws the
  game's Tahoma/Verdana text with the browser's own fonts.

## Legal

House M.D. is a trademark and copyright of Universal Studios, licensed by
Universal Studios Licensing LLLP. The game was developed by Glyphic
Entertainment and published by Legacy Interactive. This project is unofficial
and non-commercial, is not affiliated with or endorsed by any of them, and
ships none of the game's files.

Rights holders and anyone else with questions: please
[open an issue](https://github.com/frotzilla/house-md-browser-port/issues).

The code in this repo is MIT licensed (see `LICENSE`). Ruffle is MIT /
Apache-2.0 and is downloaded at build time with its license files.
