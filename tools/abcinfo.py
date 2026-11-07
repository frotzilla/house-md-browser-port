"""Minimal AVM2 ABC reader: list DoABC tags and find a method body by method name.
usage: abcinfo.py file.swf <method name substring>"""
import sys, zlib, struct

def swf_body(path):
    d = open(path, 'rb').read()
    b = zlib.decompress(d[8:]) if d[:3] == b'CWS' else d[8:]
    nb = b[0] >> 3
    return b, (5 + 4 * nb + 7) // 8 + 4

def tags(b, p):
    while p < len(b):
        h = struct.unpack_from('<H', b, p)[0]; p += 2
        t, l = h >> 6, h & 0x3f
        if l == 0x3f: l = struct.unpack_from('<I', b, p)[0]; p += 4
        yield t, p, l
        p += l
        if t == 0: break

class R:
    def __init__(s, b, p): s.b, s.p = b, p
    def u8(s): v = s.b[s.p]; s.p += 1; return v
    def u16(s): v = struct.unpack_from('<H', s.b, s.p)[0]; s.p += 2; return v
    def u30(s):
        r = 0
        for i in range(5):
            c = s.b[s.p]; s.p += 1
            r |= (c & 0x7f) << (7 * i)
            if not c & 0x80: break
        return r
    def d64(s): s.p += 8
    def bytes(s, n): v = s.b[s.p:s.p + n]; s.p += n; return v

def parse_abc(b, p):
    r = R(b, p)
    r.u16(); r.u16()
    n = r.u30(); [r.u30() for _ in range(max(n - 1, 0))]          # int
    n = r.u30(); [r.u30() for _ in range(max(n - 1, 0))]          # uint
    n = r.u30(); [r.d64() for _ in range(max(n - 1, 0))]          # double
    n = r.u30(); strings = [''] + [r.bytes(r.u30()).decode('utf8', 'replace') for _ in range(max(n - 1, 0))]
    n = r.u30(); nss = [None]
    for _ in range(max(n - 1, 0)): k = r.u8(); nss.append((k, r.u30()))
    n = r.u30()
    for _ in range(max(n - 1, 0)): [r.u30() for _ in range(r.u30())]
    n = r.u30(); mns = [None]
    for _ in range(max(n - 1, 0)):
        k = r.u8()
        if k in (0x07, 0x0D): mns.append(('Q', r.u30(), r.u30()))
        elif k in (0x0F, 0x10): mns.append(('RTQ', r.u30()))
        elif k in (0x11, 0x12): mns.append(('RTQL',))
        elif k in (0x09, 0x0E): mns.append(('M', r.u30(), r.u30()))
        elif k in (0x1B, 0x1C): mns.append(('ML', r.u30()))
        elif k == 0x1D:
            nm = r.u30(); mns.append(('TN', nm, [r.u30() for _ in range(r.u30())]))
        else: raise ValueError(hex(k))
    n = r.u30(); method_names = []
    for _ in range(n):
        pc = r.u30(); r.u30(); [r.u30() for _ in range(pc)]
        name = r.u30(); flags = r.u8()
        if flags & 0x08:
            for _ in range(r.u30()): r.u30(); r.u8()
        if flags & 0x80: [r.u30() for _ in range(pc)]
        method_names.append(strings[name])
    for _ in range(r.u30()):  # metadata
        r.u30(); c = r.u30(); [r.u30() for _ in range(2 * c)]
    ic = r.u30()
    def traits():
        for _ in range(r.u30()):
            r.u30(); kind = r.u8(); t = kind & 0x0f
            if t in (0, 6):
                r.u30(); r.u30(); vi = r.u30()
                if vi: r.u8()
            elif t in (1, 2, 3, 4, 5): r.u30(); r.u30()
            if kind & 0x40: [r.u30() for _ in range(r.u30())]
    for _ in range(ic):
        r.u30(); r.u30(); fl = r.u8()
        if fl & 0x08: r.u30()
        [r.u30() for _ in range(r.u30())]
        r.u30(); traits()
    for _ in range(ic): r.u30(); traits()
    for _ in range(r.u30()): r.u30(); traits()
    bodies = []
    for bi in range(r.u30()):
        m = r.u30(); r.u30(); r.u30(); r.u30(); r.u30()
        cl = r.u30(); code_off = r.p; r.p += cl
        for _ in range(r.u30()): [r.u30() for _ in range(5)]
        traits()
        bodies.append((bi, m, code_off, cl))
    return method_names, bodies

if __name__ == '__main__':
    b, p = swf_body(sys.argv[1])
    want = sys.argv[2]
    ai = 0
    for t, tp, l in tags(b, p):
        if t in (72, 82):
            start = b.index(b'\0', tp + 4) + 1 if t == 82 else tp
            names, bodies = parse_abc(b, start)
            print(f'ABC #{ai} tag {t} at 0x{tp:x}: {len(names)} methods, {len(bodies)} bodies')
            for bi, m, off, cl in bodies:
                if want in names[m]:
                    print(f'  body {bi} method {m} {names[m]!r} code@0x{off:x} len {cl}')
            ai += 1
