#!/usr/bin/env python3
import json, re, html, os, collections

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(REPO, 'build', 'magnifica.json')))
OUT = os.path.join(REPO, 'narration')
for sub in ['plain','ssml','tts-chunks','lexicon']:
    os.makedirs(os.path.join(OUT,sub), exist_ok=True)

# ---------- pronunciation data (derived from terms actually in the text) ----------
# term -> spoken respelling (reliable, ecclesiastical/English-friendly)
RESPELL = {
 "Magnifica Humanitas":"mahg-NIFF-ee-kah hoo-MAH-nee-tahss",
 "Rerum Novarum":"RAY-room noh-VAH-room",
 "Gaudium et Spes":"GOW-dee-um et SPESS",
 "Populorum Progressio":"pop-oo-LOH-room pro-GRESS-ee-oh",
 "Laudato Si":"low-DAH-toh SEE",
 "Fratelli Tutti":"frah-TELL-ee TOO-tee",
 "Magnificat":"mahg-NIFF-ee-kaht",
 "res novae":"RAYSS NOH-veye",
 "res publica":"RAYSS POO-blee-kah",
 "rerum novarum":"RAY-room noh-VAH-room",
 "Mater et Magistra":"MAH-ter et mah-JEE-strah",
 "Pacem in Terris":"PAH-chem in TER-reess",
 "Dignitatis Humanae":"deeg-nee-TAH-tiss hoo-MAH-nigh",
 "Octogesima Adveniens":"ok-toh-JEH-zee-mah ad-VEN-ee-ens",
 "Laborem Exercens":"lah-BOH-rem EX-er-chens",
 "Sollicitudo Rei Socialis":"sol-ee-chee-TOO-doh RAY-ee soh-chee-AH-liss",
 "Centesimus Annus":"chen-TEH-zee-mooss AHN-nooss",
 "Caritas in Veritate":"KAH-ree-tahss in veh-ree-TAH-teh",
 "Evangelii Gaudium":"eh-vahn-JEH-lee-ee GOW-dee-um",
 "Dilexit Nos":"dee-LEX-it nohss",
 "Dignitas Infinita":"DEEG-nee-tahss in-fee-NEE-tah",
 "Quadragesima Anno":"kwah-drah-JEH-zee-mah AHN-noh",
 "Divini Redemptoris":"dee-VEE-nee reh-demp-TOH-riss",
 "Iustitia et Pax":"yoo-STEE-tee-ah et pahks",
 "Lumen Gentium":"LOO-men JEN-tee-um",
 "In Illo uno unum":"in EEL-loh OO-noh OO-noom",
 "Mit Brennender Sorge":"mit BREN-en-der ZOR-guh",
 "Non Abbiamo Bisogno":"non ab-YAH-moh bee-ZON-yoh",
 "Shema Yisrael":"sh' MAH yiss-rah-ELL",
 "Realpolitik":"ray-AHL-poh-lee-teek",
 "détente":"day-TAHNT",
 "Magna Carta":"MAG-nah CAR-tah",
 "corpus":"KOR-pooss",
 "de facto":"day FAK-toh",
}
# approximate IPA (best-effort) for PLS lexicon
IPA = {
 "Magnifica Humanitas":"maɲˈɲiːfika uˈmaːnitas",
 "Rerum Novarum":"ˈreːrum noˈvaːrum",
 "Gaudium et Spes":"ˈɡaudium et ˈspɛs",
 "Populorum Progressio":"popuˈloːrum proˈɡrɛssio",
 "Laudato Si":"lauˈdaːto ˈsi",
 "Fratelli Tutti":"fraˈtɛlli ˈtutti",
 "Magnificat":"maɲˈɲifikat",
 "res novae":"ˈrɛs ˈnɔvɛ",
 "Centesimus Annus":"tʃenˈtɛzimus ˈannus",
 "Lumen Gentium":"ˈluːmen ˈdʒɛntium",
 "Evangelii Gaudium":"evanˈdʒɛlii ˈɡaudium",
}
# Name + Roman numeral -> spoken ordinal
ORD = {1:"the First",2:"the Second",3:"the Third",4:"the Fourth",5:"the Fifth",6:"the Sixth",
 7:"the Seventh",8:"the Eighth",9:"the Ninth",10:"the Tenth",11:"the Eleventh",12:"the Twelfth",
 13:"the Thirteenth",14:"the Fourteenth",15:"the Fifteenth",16:"the Sixteenth",17:"the Seventeenth",
 18:"the Eighteenth",19:"the Nineteenth",20:"the Twentieth",21:"the Twenty-first",22:"the Twenty-second",
 23:"the Twenty-third",24:"the Twenty-fourth"}
POPE_NAMES = "Leo|John Paul|Paul|Pius|Benedict|John|Gregory|Innocent|Clement|Urban|Boniface|Francis|Sixtus|Alexander|Julius|Adrian|Celestine|Honorius|Nicholas|Stephen"
def roman_to_int(r):
    vals={'I':1,'V':5,'X':10,'L':50,'C':100}; t=0;p=0
    for c in reversed(r.upper()):
        v=vals.get(c,0); t+=-v if v<p else v; p=max(p,v)
    return t
def normalize_popes(text):
    rx=re.compile(r'\b('+POPE_NAMES+r') ((?=[IVXLC])(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))\b')
    def rep(m):
        name,rn=m.group(1),m.group(2)
        n=roman_to_int(rn)
        return f'{name} {ORD.get(n,rn)}' if n in ORD else m.group(0)
    return rx.sub(rep,text)
def normalize_abbrev(text):
    text=re.sub(r'\bCf\.','See',text); text=re.sub(r'\bcf\.','see',text)
    text=text.replace('i.e.','that is').replace('e.g.','for example')
    return text

# ---------- html -> spoken plain text ----------
def to_plain(h):
    h=re.sub(r'<sup class="fnref">.*?</sup>','',h)   # drop footnote markers
    h=re.sub(r'<[^>]+>','',h)
    h=html.unescape(h)
    h=re.sub(r'[ \t]+',' ',h).strip()
    return h
def speak_text(h):
    return normalize_abbrev(normalize_popes(to_plain(h)))

# ---------- build chapter structure ----------
chapters=[]; cur=None
for n in d['nodes']:
    if n['type']=='chapter':
        cur={'label':n['label'],'title':to_plain(n['title']),'units':[]}; chapters.append(cur)
    elif n['type']=='section' and cur is not None:
        cur['units'].append(('sec',n.get('level',1),speak_text(n['html'])))
    elif n['type']=='para' and cur is not None:
        cur['units'].append(('para',n['n'],speak_text(n['html'])))
    elif n['type']=='sig' and cur is not None:
        cur['units'].append(('sig',0,speak_text(n['html'])))

def chapter_intro(c):
    lab,ti=c['label'],c['title']
    return ti if lab.strip().lower()==ti.strip().lower() else f"{lab}. {ti}"

SLUG=['00-introduction','01-chapter-one','02-chapter-two','03-chapter-three',
      '04-chapter-four','05-chapter-five','06-conclusion']

# ---------- XML escape + SSML latin <sub> ----------
def xesc(s): return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
# build one regex for latin terms (longest first); match straight/curly apostrophe for "Laudato Si"
_terms=sorted(RESPELL.keys(), key=len, reverse=True)
def latin_pat(t):
    p=re.escape(t)
    if t=="Laudato Si": p+=r"['’]?"
    return p
LATIN_RX=re.compile('('+'|'.join(latin_pat(t) for t in _terms)+')')
def latin_sub_ssml(escaped):
    def rep(m):
        key=m.group(1).rstrip("'’")
        r=RESPELL.get(key) or RESPELL.get(key.strip("'’")) or RESPELL.get(key.title())
        if not r:
            for k in _terms:
                if k.lower()==key.lower(): r=RESPELL[k];break
        return f'<sub alias="{r}">{m.group(0)}</sub>' if r else m.group(0)
    return LATIN_RX.sub(rep,escaped)
def latin_respell_plain(text):   # for lexicon-less engines: replace inline
    return LATIN_RX.sub(lambda m:(RESPELL.get(m.group(1).rstrip("'’")) or
        next((RESPELL[k] for k in _terms if k.lower()==m.group(1).rstrip("'’").lower()),m.group(0))),text)

# ---------- writers ----------
full_plain=[]; full_ssml=['<?xml version="1.0" encoding="UTF-8"?>',
  '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">',
  '<prosody rate="92%">']
manifest=[]; chunk_idx=0; chunks=[]
CHUNK_MAX=3800

def flush_chunk(buf,chap):
    global chunk_idx
    if not buf.strip(): return
    chunk_idx+=1
    fn=f'chunk-{chunk_idx:03d}.txt'
    open(os.path.join(OUT,'tts-chunks',fn),'w').write(buf.strip()+'\n')
    manifest.append({'file':fn,'chapter':chap,'chars':len(buf.strip())})

for ci,c in enumerate(chapters):
    intro=chapter_intro(c)
    # ----- plain per-chapter -----
    P=[intro,'']
    # ----- ssml per-chapter -----
    S=['<?xml version="1.0" encoding="UTF-8"?>',
       '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">',
       '<prosody rate="92%">',
       f'<emphasis level="moderate">{xesc(intro)}</emphasis><break time="1200ms"/>']
    full_ssml.append(f'<emphasis level="moderate">{xesc(intro)}</emphasis><break time="1200ms"/>')
    full_plain.append('\n\n'+intro+'\n')
    # chunk buffer
    cbuf=intro+'\n\n'
    for kind,meta,text in c['units']:
        if kind=='sec':
            P.append(text); P.append('')
            S.append(f'<break time="800ms"/><emphasis level="reduced">{latin_sub_ssml(xesc(text))}</emphasis><break time="600ms"/>')
            full_ssml.append(f'<break time="800ms"/><emphasis level="reduced">{latin_sub_ssml(xesc(text))}</emphasis><break time="600ms"/>')
            full_plain.append('\n'+text+'\n')
            unit_plain='\n'+text+'\n\n'
        elif kind in ('para','sig'):
            P.append(text); P.append('')
            S.append(latin_sub_ssml(xesc(text))+'<break time="650ms"/>')
            full_ssml.append(latin_sub_ssml(xesc(text))+'<break time="650ms"/>')
            full_plain.append(text)
            unit_plain=text+'\n\n'
        # ---- chunking (respelled, for lexicon-less engines) ----
        unit_re=latin_respell_plain(unit_plain if kind=='sec' else (text+'\n\n'))
        if len(cbuf)+len(unit_re)>CHUNK_MAX:
            flush_chunk(cbuf,c['label']); cbuf=''
        if len(unit_re)>CHUNK_MAX:   # giant paragraph: split on sentences
            for sent in re.split(r'(?<=[.!?]) ',unit_re):
                if len(cbuf)+len(sent)>CHUNK_MAX: flush_chunk(cbuf,c['label']); cbuf=''
                cbuf+=sent+' '
        else:
            cbuf+=unit_re
    flush_chunk(cbuf,c['label'])
    S+=['</prosody>','</speak>']
    open(os.path.join(OUT,'plain',SLUG[ci]+'.txt'),'w').write('\n'.join(P).strip()+'\n')
    open(os.path.join(OUT,'ssml',SLUG[ci]+'.ssml'),'w').write('\n'.join(S))

full_ssml+=['</prosody>','</speak>']
open(os.path.join(OUT,'plain','magnifica-full.txt'),'w').write('\n'.join(full_plain).strip()+'\n')
open(os.path.join(OUT,'ssml','magnifica-full.ssml'),'w').write('\n'.join(full_ssml))
json.dump(manifest, open(os.path.join(OUT,'tts-chunks','manifest.json'),'w'), indent=1)

# ---------- lexicon files ----------
json.dump({"description":"Whole-word pronunciation substitutions for Magnifica Humanitas (use for engines without a lexicon, e.g. OpenAI/local).",
           "respellings":RESPELL,
           "spoken_ordinals_example":{"Leo XIV":"Leo the Fourteenth","John Paul II":"John Paul the Second"}},
          open(os.path.join(OUT,'lexicon','aliases.json'),'w'), ensure_ascii=False, indent=1)

pls=['<?xml version="1.0" encoding="UTF-8"?>',
 '<lexicon version="1.0" xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"',
 '  alphabet="ipa" xml:lang="en-US">',
 '  <!-- Approximate IPA for the Latin/foreign terms in the encyclical. Verify in your engine. -->']
for term,ph in IPA.items():
    pls.append(f'  <lexeme><grapheme>{xesc(term)}</grapheme><phoneme>{ph}</phoneme></lexeme>')
pls.append('</lexicon>')
open(os.path.join(OUT,'lexicon','lexicon.pls'),'w').write('\n'.join(pls))

guide=['# Pronunciation guide — Magnifica Humanitas','',
 'Spoken respellings for the Latin / foreign terms and papal names that appear in the text.',
 'Caps = stressed syllable. IPA is approximate — trust the respelling first.','',
 '## Latin & foreign terms','','| Term | Say it like | IPA (approx.) |','|---|---|---|']
for t in _terms:
    guide.append(f'| {t} | {RESPELL[t]} | {IPA.get(t,"—")} |')
guide+=['', '## Papal names (Roman numerals → spoken)','',
 'These are already expanded to words in the `plain/` and `tts-chunks/` files:','',
 '| Written | Spoken |','|---|---|',
 '| Leo XIV | Leo the Fourteenth |','| Leo XIII | Leo the Thirteenth |',
 '| John Paul II | John Paul the Second |','| Paul VI | Paul the Sixth |',
 '| Pius XI / Pius XII | Pius the Eleventh / Twelfth |','| Benedict XVI | Benedict the Sixteenth |',
 '| John XXIII | John the Twenty-third |','',
 '## Other notes','',
 '- **AI** is read letter-by-letter ("A.I.") in the `tts-chunks/` files.',
 '- **cf.** → "see", **i.e.** → "that is" (applied in plain + chunk files).',
 '- Footnote reference numbers are removed from all narration text.','']
open(os.path.join(OUT,'lexicon','pronunciation-guide.md'),'w').write('\n'.join(guide))

# also apply AI -> A.I. in chunk files (lexicon-less engines)
for f in os.listdir(os.path.join(OUT,'tts-chunks')):
    if f.endswith('.txt'):
        p=os.path.join(OUT,'tts-chunks',f); s=open(p).read()
        s=re.sub(r'\bAI\b','A.I.',s); open(p,'w').write(s)

# ---------- stats ----------
tot_chunks=len(manifest); tot_chars=sum(m['chars'] for m in manifest)
print('chapters:',len(chapters))
print('plain files:',len(SLUG)+1,' ssml files:',len(SLUG)+1)
print('tts chunks:',tot_chunks,' total chunk chars:',tot_chars)
print('lexicon terms:',len(RESPELL))
for ci,c in enumerate(chapters):
    print('  ',SLUG[ci], c['label'])
