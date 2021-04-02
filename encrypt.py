from BigInteger import BigInteger

def nopadding(message, size):
    if (len(message) > size):
        print('Message is too long!')
        return

    ba = [0] * size
    i = 0
    j = 0
    while ((i < len(message)) and (j < size)):
        c = ord(message[i])
        if (c < 128):
            ba[j] = c
            j += 1
        elif ((c > 127) and (c < 2048)):
            ba[j] = (c & 63) | 128;
            j += 1
            ba[j] = (c >> 6) | 192;
            j += 1
        else:
            ba[j] = (c & 63) | 128
            j += 1
            ba[j] = ((c >> 6) & 63) | 128
            j += 1
            ba[j] = (c >> 12) | 224
            j += 1
        i += 1
    res = BigInteger()
    res.initFromList(ba, 256)
    return res

def encrypt(message, n, e):

    n_bigInteger = BigInteger()
    n_bigInteger.initFromString(n, 16)
    m = nopadding(message, (n_bigInteger.getBitLength() + 7) >> 3)
    c = m.modPow(e, n_bigInteger)
    h = c.toString(16)
    if (len(h) & 1) == 0:
        return h
    else:
        return "0" + h

# print(encrypt('86688668'))
