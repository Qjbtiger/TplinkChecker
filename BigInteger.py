import math

charset = "0123456789abcdefghijklmnopqrstuvwxyz"
BI_FP = 52

def char2int(char):
    if (char >= 'A' and char <='Z'):
        return ord(char) - ord('A') + 10
    elif (char >= 'a' and char <='z'):
        return ord(char) - ord('a') + 10
    elif (char >= '0' and char <='9'):
        return ord(char) - ord('0')
    else:
        return -1

def int2char(x):
    return charset[x]

def nbits(x):
    r = 1
    t = x >> 16
    if t != 0:
        x = t
        r += 16
    t = x >> 8
    if t != 0:
        x = t
        r += 8
    t = x >> 4
    if t != 0:
        x = t
        r += 4
    t = x >> 2
    if t != 0:
        x = t
        r += 2
    t = x >> 1
    if t != 0:
        x = t
        r += 1

    return r

def nbi():
    return BigInteger()

def nbv(num):
    res = BigInteger()
    res.initFromNumber(num)
    return(res)

class Montgomery(object):
    def __init__(self, m):
        self.m = m
        self.mp = m.invDigit()
        self.mpl = self.mp & 0x7fff
        self.mph = self.mp >> 15
        self.um = (1 << (m.dbits - 15)) - 1
        self.mt2 = 2 * m.t

    def convert(self, x):
        r = x.abs().dlShiftTo(self.m.t)
        r = r.divRemTo(self.m, None)
        if x.s < 0 and r.compareTo(nbv(0)) > 0:
            r = self.m.subTo(r)
        return r

    def reduce(self, x):
        while (x.t <= self.mt2):
            x.data.append(0)
            x.t += 1
        for i in range(0, self.m.t, 1):
            j = x.data[i] & 0x7fff
            u0 = (j * self.mpl + (((j * self.mph + (x.data[i] >> 15) * self.mpl) & self.um) << 15)) & x.dm
            j = i + self.m.t
            x.data[j] += self.m.am(0, u0, x, i, 0, self.m.t)
            while x.data[j] >= x.dv:
                x.data[j] -= x.dv
                j += 1
                x.data[j] += 1

        x.clamp()
        x = x.drShiftTo(self.m.t)
        if x.compareTo(self.m) >= 0: 
            x = x.subTo(self.m)
        return x

    def sqrTo(self, x):
        r = x.squareTo()
        r = self.reduce(r)
        return r

    def mulTo(self, x, y):
        r = x.multiplyTo(y)
        r = self.reduce(r)
        return r

    def revert(self, x):
        r = x.copy()
        r = self.reduce(r)
        return r

class Classics(object):
    def __init__(self, m):
        self.m = m

    def convert(self, x):
        if x.s < 0 or x.compareTo(self.m) >= 0:
            return x.mod(self.m)
        else:
            return x

    def reduce(self, x):
        x = x.divRemTo(self.m, None, x)
        return x

    def sqrTo(self, x):
        r = x.squareTo()
        r = self.reduce(r)
        return r

    def mulTo(self, x, y):
        r = x.multiplyTo(y)
        r = self.reduce(r)
        return r

    def revert(self, x):
        return x

class BigInteger(object):
    def __init__(self):
        self.dbits = 28
        self.data = []
        self.t = 0
        self.s = 0
        self.dm = ((1 << self.dbits) - 1)
        self.dv = (1 << self.dbits)
        self.fv = pow(2, BI_FP)
        self.f1 = BI_FP - self.dbits
        self.f2 = 2 * self.dbits - BI_FP

    def initFromNumber(self, N):
        self.initFromString(str(N), 16)

    def initFromString(self, string, radix):
        xList = [char2int(char) for char in string]
        self.initFromList(xList, radix)

    def initFromList(self, xList, radix):
        sh = 0
        self.data = []
        self.t = 0
        self.s = 0
        k = 4
        if radix == 16:
            k = 4
        elif radix == 256:
            k = 8 # byte
        elif radix == 2:
            k = 1
        elif radix == 32:
            k = 5
        elif radix == 4:
            k = 2

        xList = xList[::-1]
        for char in xList:
            x = char & 0xff
            if sh == 0:
                self.data.append(x)
                self.t += 1
            elif (sh + k) > self.dbits:
                self.data[self.t-1] |= (x & ((1 << (self.dbits - sh)) - 1)) << sh
                self.data.append((x >> (self.dbits - sh)))
                self.t += 1
            else:
                self.data[self.t-1] |= x << sh
            sh += k
            if sh >= self.dbits:
                sh -= self.dbits
        if k == 8 and (xList[0] & 0x80) != 0:
            self.s = 0
            if sh > 0:
                self.data[self.t-1] |= ((1 << (self.dbits - sh)) - 1) << sh
        self.clamp()

    def getBitLength(self):
        if self.t <= 0:
            return 0
        return self.dbits * (self.t - 1) + nbits(self.data[self.t - 1] ^ (self.s & self.dm))

    def clamp(self):
        c = self.s & self.dm
        while (self.t > 0 and self.data[self.t - 1] == c):
            self.t -= 1

    def am(self, i, x, w, j, c, n):
        xl = x & 0x3fff
        xh = x >> 14
        n -= 1
        while n >= 0:
            l = self.data[i] & 0x3fff
            h = self.data[i] >> 14
            i += 1
            m = xh * l + h * xl
            l = xl * l + ((m & 0x3fff) << 14) + w.data[j] + c
            c = (l >> 28) + (m >> 14) + xh * h
            w.data[j] = l & 0xfffffff
            j += 1
            n -= 1
            
        return c

    def subTo(self, a):
        r = nbi()
        i = 0
        c = 0
        m = min(a.t, self.t)
        while (i < m):
            c += (self.data[i] - a.data[i])
            r.data.append(c & self.dm)
            i += 1
            c >>= self.dbits
        if (a.t < self.t):
            c -= a.s
            while (i < self.t):
                c += self.data[i]
                r.data.append(c & self.dm)
                i += 1
                c >>= self.dbits
            c += self.s
        else:
            c += self.s
            while (i < a.t):
                c -= a.data[i]
                r.data.append(c & self.dm)
                i += 1
                c >>= self.dbits
            c -= a.s

        r.s = -1 if (c < 0) else 0
        if c < -1:
            r.data.append(self.dv + c)
            i += 1
        elif c > 0:
            r.data.append(c)
            i += 1
        r.t = i
        r.clamp()
        return r

    def squareTo(self):
        r = nbi()
        x = self.abs()
        i = r.t = 2 * x.t
        r.data = [0] * r.t
        i -= 1
        while i >= 0:
            r.data[i] = 0
            i -= 1

        for i in range(0, x.t-1, 1):
            c = x.am(i, x.data[i], r, 2 * i, 0, 1)
            r.data[i + x.t] += x.am(i + 1, 2 * x.data[i], r, 2 * i + 1, c, x.t - i - 1)
            if r.data[i + x.t] >= x.dv:
                r.data[i + x.t] -= x.dv
                r.data[i + x.t + 1] = 1

        i += 1
        if r.t > 0:
            r.data[r.t - 1] += x.am(i, x.data[i], r, 2 * i, 0, 1)
        r.s = 0
        r.clamp()
        return r

    def multiplyTo(self, a):
        r = nbi()
        x = self.abs()
        y = a.abs()
        i = x.t
        r.t = i + y.t
        r.data = [0] * (i + y.t)
        i -= 1
        while i >= 0:
            r.data[i] = 0
            i -= 1
        for i in range(0, y.t, 1):    
            r.data[i + x.t] = x.am(0, y.data[i], r, i, 0, x.t)
        r.s = 0
        r.clamp()
        if self.s != a.s:
            r = nbi(0).subTo(r)
        return r

    def mod(self, a):
        r = nbi()
        r = self.abs().divRemTo(a, None)
        if self.s < 0 and r.compareTo(nbv(0)) > 0:
            r = a.subTo(r)
        return r

    def copy(self):
        r = nbi()
        for item in self.data:
            r.data.append(item)
        r.t = self.t
        r.s = self.s
        return r

    def negate(self):
        r = nbv(0).subTo(self)
        return r

    def abs(self):
        return self.negate() if self.s < 0 else self

    def isEven(self):
        return ((self.data[0] & 1) if (self.t > 0) else self.s) == 0

    def invDigit(self):
        if self.t < 1:
            return 0
        x = self.data[0]
        if (x & 1) == 0:
            return 0
        y = x & 3
        y = (y * (2 - (x & 0xf) * y)) & 0xf
        y = (y * (2 - (x & 0xff) * y)) & 0xff
        y = (y * (2 - (((x & 0xffff) * y) & 0xffff))) & 0xffff
        y = (y * (2 - x * y % self.dv)) % self.dv
        return (self.dv - y) if (y > 0) else -y

    def dlShiftTo(self, n):
        r = nbi()
        r.data = [0] * (self.t + n)
        for i in range(self.t - 1, -1, -1):
            r.data[i + n] = self.data[i]
        for i in range(n - 1, -1, -1):
            r.data[i] = 0
        r.t = self.t + n
        r.s = self.s
        return r

    def drShiftTo(self, n):
        r = nbi()
        r.data = [0] * max(self.t - n, 0)
        for i in range(n, self.t, 1):
            r.data[i - n] = self.data[i]
        r.t = max(self.t - n, 0)
        r.s = self.s
        return r

    def lShiftTo(self, n):
        r = nbi()
        bs = n % self.dbits
        cbs = self.dbits - bs
        bm = (1 << cbs) - 1
        ds = math.floor(n / self.dbits)
        r.data = [0] * (self.t + ds + 1)
        c = (self.s << bs) & self.dm
        for i in range(self.t - 1, -1, -1):
            r.data[i + ds + 1] = (self.data[i] >> cbs) | c
            c = (self.data[i] & bm) << bs
        for i in range(ds - 1, -1, -1):
            r.data[i] = 0
        r.data[ds] = c
        r.t = self.t + ds + 1
        r.s = self.s
        r.clamp()
        return r
    
    def rShiftTo(self, n):
        r = nbi()
        ds = math.floor(n / self.dbits)
        if ds >= self.t:
            r.t = 0
            return r
        r.data = [0] * (self.t - ds)
        bs = n % self.dbits
        cbs = self.dbits - bs
        bm = (1 << bs) - 1
        r.data[0] = self.data[ds] >> bs
        for i in range(ds + 1, self.t, 1):
            r.data[i - ds - 1] |= (self.data[i] & bm) << cbs
            r.data[i - ds] = self.data[i] >> bs
        if bs > 0:
            r.data[self.t - ds - 1] |= (self.s & bm) << cbs
        r.t = self.t - ds
        r.clamp()
        return r

    def compareTo(self, a):
        r = self.s - a.s
        if r != 0:
            return r
        i = self.t
        r = i - a.t
        if r != 0:
            return -r if (self.s < 0) else r
        i -= 1
        while i >= 0:
            if (self.data[i] - a.data[i]) != 0:
                r = self.data[i] - a.data[i]
                return r
            i -= 1
        return 0
    
    def divRemTo(self, m, q):
        r = nbi()
        pm = m.abs()
        if pm.t <= 0:
            return r
        pt = self.abs()
        if pt.t < pm.t:
            if q != None:
                q = nbv(0)
            if r != None:
                r = self.copy()
            return r

        if r == None:
            r = nbi()
        y = nbi()
        ts = self.s
        ms = m.s
        nsh = self.dbits - nbits(pm.data[pm.t - 1])

        if nsh > 0:
            y = pm.lShiftTo(nsh)
            r = pt.lShiftTo(nsh)
        else:
            y = pm.copy()
            r = pt.copy()

        ys = y.t
        y0 = y.data[ys - 1]
        if y0 == 0:
            return r
        yt = y0 * (1 << self.f1) + (y.data[ys - 2] >> self.f2 if (ys > 1) else 0)
        d1 = self.fv / yt
        d2 = (1 << self.f1) / yt
        e = 1 << self.f2
        i = r.t
        j = i - ys
        t = nbi() if (q == None) else q
        t = y.dlShiftTo(j)
        if r.compareTo(t) >= 0:
            r.data[r.t] = 1
            r.t += 1
            r = r.subTo(t)

        t = nbv(1).dlShiftTo(ys)
        y = t.subTo(y)
        while y.t < ys:
            y.data[y.t] = 0
            y.t += 1
        j -= 1
        while j >= 0:
            i -= 1
            qd = self.dm if (r.data[i] == y0) else math.floor(r.data[i] * d1 + (r.data[i - 1] + e) * d2)
            r.data[i] += y.am(0, qd, r, j, 0, ys)
            if r.data[i] < qd:
                r
                t = y.dlShiftTo(j)
                r = r.subTo(t)
                qd -= 1
                while r.data[i] < qd:
                    r = r.subTo(t)
                    qd -= 1
            j -= 1

        if q != None:
            q = r.drShiftTo(ys)
            if ts != ms:
                q = nbv(0).subTo(q)
        
        r.t = ys
        r.clamp()
        if nsh > 0:
            r = r.rShiftTo(nsh)
        if ts < 0:
            r = nbv(0).subTo(r)
        return r

    def exp(self, e, z):
        if e > 0xffffffff or e < 1:
            return nbv(1)
        g = z.convert(self)
        i = nbits(e) - 1
        r = g.copy()
        i -= 1
        while i >= 0:
            r2 = z.sqrTo(r)
            
            if (e & (1 << i)) > 0:
                r = z.mulTo(r2, g)
            else:
                t = r
                r = r2
                r2 = t
            i -= 1
        
        return z.revert(r)

    def modPow(self, e, n):
        if (e < 256 or n.isEven()):
            z = Classics(n)
        else:
            z = Montgomery(n)
        return self.exp(e, z)

    def toString(self, radix):
        if self.s < 0:
            return "-" + self.negate().toString(radix)
        if radix == 16:
            k = 4
        elif radix == 8:
            k = 3
        elif radix == 2:
            k = 1
        elif radix == 32:
            k = 5
        elif radix == 4:
            k = 2

        km = (1 << k) - 1
        d = m = False
        r = ""
        i = self.t
        p = self.dbits - (i * self.dbits) % k
        i -= 1
        if i > 0:
            d = self.data[i] >> p
            if p < self.dbits and d > 0:
                m = True
                r = int2char(d)
            while i >= 0:
                if p < k:
                    d = (self.data[i] & ((1 << p) - 1)) << (k - p)
                    i -= 1
                    p += self.DB - k
                    d |= self.data[i] >> p
                else:
                    p -= k
                    d = (self.data[i] >> p) & km
                    if p <= 0:
                        p += self.dbits
                        i -= 1
                if d > 0:
                    m = True
                if m:
                    r += int2char(d)

        return r if m else "0"
        