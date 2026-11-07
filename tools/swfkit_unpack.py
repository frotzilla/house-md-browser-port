"""Unpack the SWFKit embedded-file tree from a SWFKit projector exe.

Entry format (little endian):
  u32 type (1 = dir, 0 = file), u32 name_len (UTF-16 chars incl NUL), name
  dir:  u32 content_bytes, then child entries filling content_bytes
  file: u32 comp_size, zlib stream of comp_size bytes
"""
import sys, zlib, os, struct

def u32(d, p): return struct.unpack_from('<I', d, p)[0]

def parse(d, p, end, path, out, listing):
    while p < end:
        typ, nl = u32(d, p), u32(d, p + 4)
        if typ not in (0, 1) or not 0 < nl < 260:
            raise ValueError(f'bad entry at {hex(p)}')
        name = d[p + 8:p + 8 + nl * 2].decode('utf-16le').rstrip('\0')
        p += 8 + nl * 2
        size = u32(d, p); p += 4
        rel = os.path.join(path, name)
        if typ == 1:
            parse(d, p, p + size, rel, out, listing)
        else:
            data = zlib.decompress(d[p:p + size])
            listing.append((rel, len(data)))
            if out:
                fp = os.path.join(out, rel)
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                open(fp, 'wb').write(data)
        p += size
    return p

exe, root_name, out = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else None)
d = open(exe, 'rb').read()
needle = struct.pack('<II', 1, len(root_name) + 1) + (root_name + '\0').encode('utf-16le')
start = d.find(needle)
assert start >= 0, 'root dir not found'
listing = []
# top level: walk sibling entries until the structure stops parsing
p = start
while True:
    try:
        nl = u32(d, p + 4); hdr = 8 + nl * 2
        size = u32(d, p + hdr)
        if u32(d, p) not in (0, 1) or not 0 < nl < 260: break
        parse(d, p, p + hdr + 4 + size, '', out, listing)
        p = p + hdr + 4 + size
    except Exception:
        break
end = p
for rel, n in listing: print(n, rel)
print('entries', len(listing), 'ended at', hex(end), 'next bytes', d[end:end + 16].hex(' '), file=sys.stderr)
