"""Measure how many non-empty, non-comment lines a challenge's solution adds over its starter.
Usage: python3 test/size.py dc03 [dc04 ...]   (run from /home/claude/prep)
Lines between `// CORE` and `// END CORE` markers (and `/* CORE */ ... /* END CORE */` in CSS) are also counted
separately as the Core size, if markers are present."""
import re, sys, difflib

def sections(exid):
    t = open(f'ex/{exid}.txt').read()
    parts = re.split(r'^@@@ (\w+) (\S+)\n', t, flags=re.M)
    return {(parts[i], parts[i + 1]): parts[i + 2] for i in range(1, len(parts), 3)}

def added_lines(starter, solution):
    return [l[1:] for l in difflib.unified_diff(starter.splitlines(), solution.splitlines(), lineterm='', n=0)
            if l.startswith('+') and not l.startswith('+++')]

def meaningful(l):
    s = l.strip()
    return s and not s.startswith('//') and not s.startswith('/*') and not s.startswith('*')

for exid in sys.argv[1:]:
    f = sections(exid)
    code = css = 0
    for (role, p), body in f.items():
        if role != 'solution':
            continue
        n = sum(1 for l in added_lines(f.get(('starter', p), ''), body) if meaningful(l))
        if p.endswith('.css'):
            css += n
        else:
            code += n
    print(f'{exid}: code +{code}  css +{css}  ≈ fluent {5 + code / 3.5 + css / 6:.0f} min · at current pace {6 + code / 2.2 + css / 4:.0f} min')
