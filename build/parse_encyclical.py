#!/usr/bin/env python3
"""Parse the Firecrawl-extracted Vatican markdown of Magnifica Humanitas into
the structured JSON the reader consumes (build/magnifica.json).

Source default: vatican-source/magnifica-humanitas.firecrawl.md (committed).
Override with: python3 build/parse_encyclical.py path/to/source.md [path/to/out.json]
"""
import json, os, re, sys, html as htmllib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'vatican-source', 'magnifica-humanitas.firecrawl.md')
OUT  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, 'build', 'magnifica.json')

md = open(SRC).read()
lines = md.split('\n')

# Locate the body by semantic markers — the first standalone '**INTRODUCTION**'
# line (the TOC link version earlier in the file has [INTRODUCTION](...) inside).
BODY_START = next(
    (i for i, ln in enumerate(lines) if ln.strip() == '**INTRODUCTION**'),
    None,
)
if BODY_START is None:
    sys.exit(f"could not find '**INTRODUCTION**' marker in {SRC}")
# The horizontal-rule '* * *' separates the body from the footnote section.
try:
    SEP = lines.index('* * *', BODY_START)
except ValueError:
    sys.exit(f"could not find '* * *' footnote separator in {SRC}")
body_lines = lines[BODY_START:SEP]
fn_lines = lines[SEP+1:]

# Repair a known defect in the upstream Vatican source: a stray "\[10\]"
# appears immediately after footnote 110's reference in ¶82. Strip any
# such "\[N\]" that directly follows a "](#_ftnM)" footnote link.
_STRAY_FN_RE = re.compile(r'(\]\([^)]*#_ftn\d+\))\\\[\d+\\\]')
body_lines = [_STRAY_FN_RE.sub(r'\1', ln) for ln in body_lines]

fnref_counter = {}

def conv_inline(text, in_footnote=False):
    """Convert a markdown inline string to HTML, handling links, footnote refs, emphasis, escapes."""
    # 1. tokenize markdown links [text](url)
    links = []
    def stash(m):
        links.append((m.group(1), m.group(2)))
        return f'\x00{len(links)-1}\x00'
    text = re.sub(r'\[((?:[^\[\]]|\\\[|\\\])*?)\]\(([^)]+)\)', stash, text)

    # 2. emphasis on remaining text
    text = emphasize(text)
    # 3. unescape backslash escapes and nbsp
    text = unescape(text)

    # 4. reinsert links
    def build_link(idx):
        ltext, url = links[idx]
        if '#_ftnref' in url:   # this is a footnote back-reference (inside footnote defs) -> drop, handled separately
            return ''
        if '#_ftn' in url:      # inline footnote reference
            m = re.search(r'(\d+)', re.sub(r'\\', '', ltext))
            n = m.group(1) if m else '?'
            cnt = fnref_counter.get(n, 0); fnref_counter[n] = cnt + 1
            rid = f'fnref-{n}-{cnt}'
            return f'<sup class="fnref"><a id="{rid}" href="#fn-{n}" data-fn="{n}">{n}</a></sup>'
        # external link
        inner = unescape(emphasize(ltext))
        safe = url.replace('"', '%22')
        return f'<a href="{safe}" target="_blank" rel="noopener noreferrer">{inner}</a>'

    text = re.sub(r'\x00(\d+)\x00', lambda m: build_link(int(m.group(1))), text)

    # Repair: the source markdown loses the space between a closing link/em
    # and an immediately following date paren (e.g., "Hominis</a>(4 March 1979)").
    text = re.sub(r'</a>\((\d)', r'</a> (\1', text)
    text = re.sub(r'</em>\((\d)', r'</em> (\1', text)
    # Repair: the anchor text for footnote 37 in the source MD was split as
    # "<em>Sollicitudo Rei S</em> ocialis" (broken italics around the link).
    text = text.replace('<em>Sollicitudo Rei S</em> ocialis', '<em>Sollicitudo Rei Socialis</em>')
    # Repair: source MD wraps the trailing period of "ibid", "Ibid", "Cf" in
    # its own <em> tag with a leading space, producing "ibid ." after tag-strip.
    text = re.sub(r'(\w) <em>\.</em>', r'\1.', text)

    return text.strip()

def emphasize(t):
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    # italics: underscores not part of a token placeholder
    t = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', t)
    return t

def unescape(t):
    t = t.replace('\xa0', ' ')
    t = re.sub(r'\\([\\`*_{}\[\]()#+\-.!>~|"\'])', r'\1', t)
    return t

def strip_heading_markers(s):
    # remove ** bold markers globally for heading rendering
    return s.replace('**', '')

WORDNUM = r'(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)'

def plain(s):
    # text with markup removed for classification
    x = strip_heading_markers(s)
    x = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', x)  # links -> text
    x = x.replace('_', '').replace('\xa0', ' ')
    return x.strip()

nodes = []
i = 0
n = len(body_lines)
para_re = re.compile(r'^(\d+)\\?\.\s+(.*)$', re.S)

def is_heading(s):
    return s.strip().startswith('**') and not para_re.match(s.strip())

ch_counter = 0
while i < n:
    raw = body_lines[i].strip()
    if not raw:
        i += 1; continue
    pm = para_re.match(raw)
    if pm:
        num = int(pm.group(1))
        nodes.append({'type':'para','n':num,'html':conv_inline(pm.group(2))})
        i += 1; continue
    if is_heading(raw):
        p = plain(raw)
        is_chapter = (p == 'INTRODUCTION' or p == 'CONCLUSION' or re.match(rf'^CHAPTER {WORDNUM}$', p))
        if is_chapter:
            ch_counter += 1
            label = p.title() if p in ('INTRODUCTION','CONCLUSION') else p.title()
            titleparts = []
            j = i + 1
            # gather following ALL-CAPS bold heading lines as title (for CHAPTER X)
            if p.startswith('CHAPTER'):
                while j < n:
                    nx = body_lines[j].strip()
                    if not nx: j += 1; continue
                    if is_heading(nx) and plain(nx).isupper() and not re.match(rf'^CHAPTER {WORDNUM}$', plain(nx)):
                        titleparts.append(conv_inline(strip_heading_markers(nx)))
                        j += 1
                    else:
                        break
            title = ' '.join(titleparts) if titleparts else label
            cid = f'ch{ch_counter}'
            nodes.append({'type':'chapter','id':cid,'label':label,'title':title})
            i = j; continue
        else:
            stripped = strip_heading_markers(raw)
            # detect subsection vs major
            test = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', stripped).strip()
            level = 2 if (test.startswith('_') or test.endswith('_')) else 1
            nodes.append({'type':'section','level':level,'html':conv_inline(stripped)})
            i += 1; continue
    # signature lines
    if raw.startswith('_Given in Rome') or raw == 'LEO PP. XIV':
        nodes.append({'type':'sig','html':conv_inline(raw)})
        i += 1; continue
    # fallback: treat as paragraph without number
    nodes.append({'type':'para','n':None,'html':conv_inline(raw)})
    i += 1

# footnotes
footnotes = []
fn_def_re = re.compile(r'^\[\\?\[(\d+)\\?\]\]\([^)]*#_ftnref\d+\)\s*(.*)$', re.S)
for l in fn_lines:
    s = l.strip()
    if not s: continue
    if s.startswith('Copyright'): break
    m = fn_def_re.match(s)
    if m:
        num = int(m.group(1))
        footnotes.append({'n':num,'html':conv_inline(m.group(2), in_footnote=True)})

_LANGS = [('en','English'),('it','Italiano'),('es','Español'),('fr','Français'),
          ('de','Deutsch'),('pt','Português'),('pl','Polski'),('ar','العربية')]
meta = {
  'title':'Magnifica Humanitas',
  'kind':'Encyclical Letter',
  'pope':'Pope Leo XIV',
  'subtitle':'On Safeguarding the Human Person in the Time of Artificial Intelligence',
  'date':'15 May 2026',
  'place':'Rome, at Saint Peter’s',
  'source':'https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20260515-magnifica-humanitas.html',
  'multimedia':'https://www.vatican.va/content/leo-xiv/en/events/event.dir.html/content/vaticanevents/en/2026/5/25/enciclica-magnifica-humanitas.html',
  'descriptor':'First Encyclical Letter of His Holiness Pope Leo XIV',
  'video':'https://www.youtube.com/watch?v=7WJuHd8EtPQ',
  'languages':[{'code':c,'label':l,
    'url':f'https://www.vatican.va/content/leo-xiv/{c}/encyclicals/documents/20260515-magnifica-humanitas.html'}
    for c,l in _LANGS],
}

out = {'meta':meta,'nodes':nodes,'footnotes':footnotes}
json.dump(out, open(OUT,'w'), ensure_ascii=False, indent=1)
print('wrote', OUT)

paras = [x for x in nodes if x['type']=='para']
nums = [x['n'] for x in paras if x['n']]
print('nodes:', len(nodes))
print('chapters:', sum(1 for x in nodes if x['type']=='chapter'))
print('sections:', sum(1 for x in nodes if x['type']=='section'))
print('paragraphs:', len(paras), 'min', min(nums), 'max', max(nums))
missing = [k for k in range(1, max(nums)+1) if k not in nums]
print('missing para numbers:', missing)
dups = [k for k in set(nums) if nums.count(k)>1]
print('dup para numbers:', dups)
print('footnotes:', len(footnotes), 'first', footnotes[0]['n'], 'last', footnotes[-1]['n'])
fnnums=[f['n'] for f in footnotes]
print('missing footnotes:', [k for k in range(1,max(fnnums)+1) if k not in fnnums])
