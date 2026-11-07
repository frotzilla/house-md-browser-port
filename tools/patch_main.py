"""Patch main.swf so it runs in a browser (Ruffle).

enterCustomSplash() busy-waits with `while(!bCustomSplashLoaded){}` for an
optional splash1.png that the SWFKit wrapper loaded synchronously. In a browser
the load is async, so the loop never ends and freezes the tab. The splash file
does not ship with the game anyway, so:
  - turn the loop's backward iftrue into a no-op branch (offset 0)
  - replace `getlex bCustomSplashValid` with `pushfalse; nop; nop` so the
    function takes its "no custom splash" path and goes straight to Splash1.
"""
import sys, zlib

src, dst = sys.argv[1], sys.argv[2]
d = open(src, 'rb').read()
assert d[:3] == b'CWS', 'expected a zlib-compressed SWF'
body = bytearray(zlib.decompress(d[8:]))

old = bytes.fromhex('60c65e 96 11f4ffff f0c92f 60c75e 124300 00'.replace(' ', ''))
new = bytes.fromhex('60c65e 96 11000000 f0c92f 270202 124300 00'.replace(' ', ''))
n = body.count(old)
assert n == 1, f'expected exactly one match, found {n}'
i = body.find(old)
body[i:i + len(old)] = new

out = b'CWS' + d[3:4] + (len(body) + 8).to_bytes(4, 'little') + zlib.compress(bytes(body), 9)
open(dst, 'wb').write(out)
print(f'patched at 0x{i:x}, wrote {dst}')
