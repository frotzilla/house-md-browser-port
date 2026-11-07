// Browser stand-ins for what the original SWFKit Windows wrapper provided.
// The game calls these through ExternalInterface.call() and fscommand().

(function () {
  // Folder that holds bin-debug/, swf/, img/, snd/ and so on (where index.html is).
  const BASE = new URL(".", location.href).href;
  const SAVE_PREFIX = "housemd:";

  // The game builds asset paths as getAppPath() + "swf/...". Without a wrapper
  // it falls back to stripping "file://" off its own URL, which breaks over http.
  window.getAppPath = function () {
    return BASE;
  };

  // Polled every frame: "has the user clicked the window's close button?"
  window.getCloseFlag = function () {
    return false;
  };

  // Settings and the four player profiles were stored in the Windows registry
  // as ";"-separated strings. Keep them in localStorage instead.
  window.ReadFromRegistry = function (section, key) {
    try {
      const v = localStorage.getItem(SAVE_PREFIX + section + "/" + key);
      return v === null ? null : v;
    } catch (e) {
      return null;
    }
  };
  window.WriteToRegistry = function (section, key, value) {
    try {
      localStorage.setItem(SAVE_PREFIX + section + "/" + key, String(value));
    } catch (e) {}
  };

  // Quick clicks. Menu buttons swap to a "pressed" image on mouseDown and only
  // act on mouseUp over that pressed image. If press and release land in the
  // same frame (trackpad tap-to-click does this), Ruffle hit-tests the release
  // before the swap and the click is lost. Hold back a too-fast release until a
  // couple of frames have passed.
  const MIN_PRESS_MS = 80;
  let lastDown = 0;
  const inPlayer = (e) => e.composedPath().some((n) => n.localName === "ruffle-player");
  window.addEventListener("pointerdown", (e) => {
    if (inPlayer(e)) lastDown = performance.now();
  }, true);
  window.addEventListener("pointerup", (e) => {
    if (e.__houseReplay || !inPlayer(e)) return;
    const wait = MIN_PRESS_MS - (performance.now() - lastDown);
    if (wait <= 0) return;
    e.stopImmediatePropagation();
    const target = e.composedPath()[0];
    const copy = new PointerEvent("pointerup", {
      bubbles: true, cancelable: true, composed: true,
      clientX: e.clientX, clientY: e.clientY, screenX: e.screenX, screenY: e.screenY,
      button: e.button, buttons: e.buttons, pointerId: e.pointerId,
      pointerType: e.pointerType, isPrimary: e.isPrimary,
      ctrlKey: e.ctrlKey, shiftKey: e.shiftKey, altKey: e.altKey, metaKey: e.metaKey,
    });
    // Ruffle reads offsetX/Y; a synthetic event would recompute them without
    // the page's CSS scaling, so carry over the browser's original values.
    Object.defineProperty(copy, "offsetX", { value: e.offsetX });
    Object.defineProperty(copy, "offsetY", { value: e.offsetY });
    copy.__houseReplay = true;
    setTimeout(() => target.dispatchEvent(copy), wait);
  }, true);

  // fscommand("ffish_run", ...) and fscommand("Quit") from the game.
  window.houseFSCommand = function (player, cmd, args) {
    if (cmd === "ffish_run" && args === "switchtofullscreen") {
      // Fullscreen the whole page (not the player) so the page's own scaling
      // keeps fitting the 800x600 stage. Only works after a click or key press,
      // so the call the game makes at startup is ignored by the browser.
      const root = document.documentElement;
      if (!document.fullscreenElement && root.requestFullscreen) {
        root.requestFullscreen().catch(function () {});
      }
    } else if (cmd === "ffish_run" && args === "switchtowindowed") {
      if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
    } else if (cmd === "Quit") {
      if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
      document.getElementById("quit").hidden = false;
      const toolbar = document.getElementById("toolbar");
      if (toolbar) toolbar.hidden = true;
      player.remove();
    }
    // "setallowclose" and "minimizeapp" have no browser meaning.
    return true;
  };
})();
