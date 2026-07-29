import re, json, collections

p = r"C:\dev\ai-ee3\boards\lumina-carrier\work\review.net"
s = open(p, encoding="utf-8").read()

TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')

def sexp(text):
    stack = [[]]
    for t in TOK.findall(text):
        if t == '(':
            stack.append([])
        elif t == ')':
            v = stack.pop()
            stack[-1].append(v)
        else:
            if t.startswith('"'):
                t = t[1:-1]
                t = t.replace('\\"', '"').replace('\\\\', '\\')
            stack[-1].append(t)
    return stack[0][0]

root = sexp(s)

def kids(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

def get1(node, key):
    k = kids(node, key)
    return k[0] if k else None

comps = {}
for c in kids(get1(root, 'components'), 'comp'):
    ref = get1(c, 'ref')[1]
    vnode = get1(c, 'value')
    val = vnode[1] if vnode and len(vnode) > 1 else ''
    fnode = get1(c, 'footprint')
    fp = fnode[1] if fnode and len(fnode) > 1 else ''
    props = {}
    for pr in kids(c, 'property'):
        nm = None; v = None
        for f in pr:
            if isinstance(f, list) and f[0] == 'name':
                nm = f[1]
            if isinstance(f, list) and f[0] == 'value':
                v = f[1] if len(f) > 1 else ''
        if nm is not None:
            props[nm] = v
    sh = get1(c, 'sheetpath')
    shn = get1(sh, 'names')[1] if sh and get1(sh, 'names') else ''
    comps[ref] = {'value': val, 'fp': fp, 'props': props, 'sheet': shn, 'pins': {}}

nets = collections.OrderedDict()
for n in kids(get1(root, 'nets'), 'net'):
    nn = get1(n, 'name')
    name = nn[1] if len(nn) > 1 else ''
    members = []
    for nd in kids(n, 'node'):
        ref = get1(nd, 'ref')[1]; pin = get1(nd, 'pin')[1]
        pf = get1(nd, 'pinfunction'); pt = get1(nd, 'pintype')
        pfn = pf[1] if pf and len(pf) > 1 else ''
        ptn = pt[1] if pt and len(pt) > 1 else ''
        members.append([ref, pin, pfn, ptn])
        if ref in comps:
            comps[ref]['pins'][pin] = [name, pfn, ptn]
    nets[name] = members

json.dump({'comps': comps, 'nets': nets},
          open(r"C:\dev\ai-ee3\boards\lumina-carrier\work\rv_map.json", "w"), indent=1)
print("comps:", len(comps), "nets:", len(nets))
