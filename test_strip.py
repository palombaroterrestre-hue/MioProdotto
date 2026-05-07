import unicodedata
import re

def stripAccents(s):
    return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().strip()

queries = ['caffè', 'CAFFÈ', 'DEK', 'dek', 'caff']
for q in queries:
    uq = stripAccents(q)
    print(f'Query: {q!r} -> stripAccents: {uq!r}')