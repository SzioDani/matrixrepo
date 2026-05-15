# Stub pyparsing minimo per compatibilità Kodi Android
class ParserElement:
    pass
class Word:
    def __init__(self, *a, **kw): pass
class Regex:
    def __init__(self, *a, **kw): pass
class Suppress:
    def __init__(self, *a, **kw): pass
class Optional:
    def __init__(self, *a, **kw): pass
class Group:
    def __init__(self, *a, **kw): pass
class Combine:
    def __init__(self, *a, **kw): pass
alphanums = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
alphas = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
nums = '0123456789'
printables = ''.join(chr(i) for i in range(32, 127))
