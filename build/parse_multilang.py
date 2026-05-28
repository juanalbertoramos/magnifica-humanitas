#!/usr/bin/env python3
"""Multi-language parser for Magnifica Humanitas (EN/FR/ES).

Reads the firecrawl-scraped markdown for each language and emits one JSON
per language with the canonical 245-paragraph / 224-footnote structure.

Handles:
  - relaxed paragraph regex (ES has '23.La...' without space in a few places)
  - non-bold chapter dividers / titles / sections (FR convention)
  - language-specific signature lines
  - the EN [10] artifact fix (EN only)
"""
import re, html as htmllib, json, os, sys

# ---------- per-language configuration ----------
LANGS = {
 'en': {
  'src':'/tmp/magnifica_full.md',
  'descriptor':'First Encyclical Letter of His Holiness Pope Leo XIV',
  'kind':'Encyclical Letter',
  'pope':'Pope Leo XIV',
  'title':'Magnifica Humanitas',
  'subtitle':'On Safeguarding the Human Person in the Time of Artificial Intelligence',
  'date':'15 May 2026',
  'place':"Rome, at Saint Peter's",
  'source':'https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20260515-magnifica-humanitas.html',
  'sig_marker':'Given in Rome',          # italic prefix of the dating line
  'sig_name':'LEO PP. XIV',
  'ui':{
   'contents':'Contents','search_ph':'Search the encyclical…','mystudy':'My Study',
   'reading':'Reading','begin':'Begin reading','resume':'Resume at ¶','video':'Watch the signing',
   'pdf':'Official PDF','readaloud':'Read aloud','official_text':'Read the official text',
   'paragraphs':'Paragraphs','footnotes':'Footnotes','min_read':'Min read','movements':'Movements',
   'given_at':'Given at','notes_heading':'Notes','welcome_back':'Welcome back — continue at ¶',
   'saved':'Saved','copied':'Copied to clipboard','bookmarked':'Bookmarked ¶',
   'removed_bm':'Removed bookmark ¶','add_note':'Add note','resume_btn':'Resume',
   'scroll':'scroll','progress':'Reading progress',
   'all':'All','highlights':'Highlights','notes':'Notes','bookmarks':'Bookmarks',
   'export_md':'Export Markdown','backup_json':'Backup JSON','import':'Import',
   'theme':'Theme','typeface':'Typeface','text_size':'Text size','line_spacing':'Line spacing',
   'justify':'Justify text','width':'Width: comfortable column',
   'note_ph':'Write your reflection, question, or cross-reference…',
   'note':'Note','cancel':'Cancel','save':'Save note','delete':'Delete',
   'no_anno':'No {kind} yet.','select_hint':'Select any text to highlight, click a ¶ number to bookmark, and build your study notes here.',
   'para_sym':'¶','para_full':'Paragraph',
  },
 },
 'fr': {
  'src':'/tmp/magnifica.fr.md',
  'descriptor':'Première Lettre encyclique du Saint-Père Léon XIV',
  'kind':'Lettre encyclique',
  'pope':'Pape Léon XIV',
  'title':'Magnifica Humanitas',
  'subtitle':'Sur la protection de la personne humaine au temps de l’intelligence artificielle',
  'date':'15 mai 2026',
  'place':'Rome, près de Saint-Pierre',
  'source':'https://www.vatican.va/content/leo-xiv/fr/encyclicals/documents/20260515-magnifica-humanitas.html',
  'sig_marker':'Donné à Rome',
  'sig_name':'LÉON PP. XIV',
  'ui':{
   'contents':'Sommaire','search_ph':'Rechercher dans l’encyclique…','mystudy':'Mes notes',
   'reading':'Lecture','begin':'Commencer la lecture','resume':'Reprendre au §','video':'Voir la signature',
   'pdf':'PDF officiel','readaloud':'Lire à voix haute','official_text':'Lire le texte officiel',
   'paragraphs':'Paragraphes','footnotes':'Notes','min_read':'Min de lecture','movements':'Parties',
   'given_at':'Donné à','notes_heading':'Notes','welcome_back':'Bon retour — reprenez au §',
   'saved':'Enregistré','copied':'Copié dans le presse-papiers','bookmarked':'Signet §',
   'removed_bm':'Signet retiré §','add_note':'Ajouter une note','resume_btn':'Reprendre',
   'scroll':'défiler','progress':'Progression de lecture',
   'all':'Tout','highlights':'Surlignages','notes':'Notes','bookmarks':'Signets',
   'export_md':'Exporter en Markdown','backup_json':'Sauvegarde JSON','import':'Importer',
   'theme':'Thème','typeface':'Police','text_size':'Taille du texte','line_spacing':'Interligne',
   'justify':'Texte justifié','width':'Largeur : colonne confortable',
   'note_ph':'Écrivez votre réflexion, votre question ou un renvoi…',
   'note':'Note','cancel':'Annuler','save':'Enregistrer','delete':'Supprimer',
   'no_anno':'Aucun(e) {kind} pour le moment.','select_hint':'Sélectionnez du texte pour le surligner, cliquez sur un numéro de § pour ajouter un signet, et construisez vos notes ici.',
   'para_sym':'§','para_full':'Paragraphe',
  },
 },
 'es': {
  'src':'/tmp/magnifica.es.md',
  'descriptor':'Primera Carta encíclica del Santo Padre León XIV',
  'kind':'Carta encíclica',
  'pope':'Papa León XIV',
  'title':'Magnifica Humanitas',
  'subtitle':'Sobre la salvaguardia de la persona humana en el tiempo de la inteligencia artificial',
  'date':'15 de mayo de 2026',
  'place':'Roma, junto a San Pedro',
  'source':'https://www.vatican.va/content/leo-xiv/es/encyclicals/documents/20260515-magnifica-humanitas.html',
  'sig_marker':'Dado en Roma',
  'sig_name':'LEÓN PP. XIV',
  'ui':{
   'contents':'Índice','search_ph':'Buscar en la encíclica…','mystudy':'Mis notas',
   'reading':'Lectura','begin':'Comenzar a leer','resume':'Continuar en §','video':'Ver la firma',
   'pdf':'PDF oficial','readaloud':'Leer en voz alta','official_text':'Leer el texto oficial',
   'paragraphs':'Párrafos','footnotes':'Notas','min_read':'Min de lectura','movements':'Partes',
   'given_at':'Dado en','notes_heading':'Notas','welcome_back':'Bienvenido — continúe en §',
   'saved':'Guardado','copied':'Copiado al portapapeles','bookmarked':'Marcado §',
   'removed_bm':'Marcador retirado §','add_note':'Añadir nota','resume_btn':'Continuar',
   'scroll':'desplazar','progress':'Progreso de lectura',
   'all':'Todo','highlights':'Subrayados','notes':'Notas','bookmarks':'Marcadores',
   'export_md':'Exportar Markdown','backup_json':'Copia JSON','import':'Importar',
   'theme':'Tema','typeface':'Tipografía','text_size':'Tamaño del texto','line_spacing':'Interlineado',
   'justify':'Justificar texto','width':'Ancho: columna cómoda',
   'note_ph':'Escriba su reflexión, pregunta o referencia cruzada…',
   'note':'Nota','cancel':'Cancelar','save':'Guardar','delete':'Eliminar',
   'no_anno':'Aún no hay {kind}.','select_hint':'Seleccione texto para subrayarlo, haga clic en un número de § para marcar, y construya aquí sus notas.',
   'para_sym':'§','para_full':'Párrafo',
  },
 },
}

LANGUAGES = [
 {'code':'en','label':'English','url':LANGS['en']['source']},
 {'code':'it','label':'Italiano','url':'https://www.vatican.va/content/leo-xiv/it/encyclicals/documents/20260515-magnifica-humanitas.html'},
 {'code':'es','label':'Español','url':LANGS['es']['source']},
 {'code':'fr','label':'Français','url':LANGS['fr']['source']},
 {'code':'de','label':'Deutsch','url':'https://www.vatican.va/content/leo-xiv/de/encyclicals/documents/20260515-magnifica-humanitas.html'},
 {'code':'pt','label':'Português','url':'https://www.vatican.va/content/leo-xiv/pt/encyclicals/documents/20260515-magnifica-humanitas.html'},
 {'code':'pl','label':'Polski','url':'https://www.vatican.va/content/leo-xiv/pl/encyclicals/documents/20260515-magnifica-humanitas.html'},
 {'code':'ar','label':'العربية','url':'https://www.vatican.va/content/leo-xiv/ar/encyclicals/documents/20260515-magnifica-humanitas.html'},
]
VIDEO='https://www.youtube.com/watch?v=7WJuHd8EtPQ'
MULTIMEDIA='https://www.vatican.va/content/leo-xiv/en/events/event.dir.html/content/vaticanevents/en/2026/5/25/enciclica-magnifica-humanitas.html'

# ---------- inline markdown → html ----------
fnref_counter = {}

def conv_inline(text):
    links = []
    def stash(m):
        links.append((m.group(1), m.group(2)))
        return f'\x00{len(links)-1}\x00'
    text = re.sub(r'\[((?:[^\[\]]|\\\[|\\\])*?)\]\(([^)]+)\)', stash, text)
    text = emphasize(text)
    text = unescape(text)
    def build_link(idx):
        ltext, url = links[idx]
        if '#_ftnref' in url: return ''
        if '#_ftn' in url:
            m = re.search(r'(\d+)', re.sub(r'\\', '', ltext))
            n = m.group(1) if m else '?'
            cnt = fnref_counter.get(n, 0); fnref_counter[n] = cnt + 1
            rid = f'fnref-{n}-{cnt}'
            return f'<sup class="fnref"><a id="{rid}" href="#fn-{n}" data-fn="{n}">{n}</a></sup>'
        inner = unescape(emphasize(ltext))
        safe = url.replace('"', '%22')
        return f'<a href="{safe}" target="_blank" rel="noopener noreferrer">{inner}</a>'
    text = re.sub(r'\x00(\d+)\x00', lambda m: build_link(int(m.group(1))), text)

    # ---- defensive typography fixes (parity with build/parse_encyclical.py from f06e4b6) ----
    # missing space between closing link/em and date paren
    text = re.sub(r'</a>\((\d)', r'</a> (\1', text)
    text = re.sub(r'</em>\((\d)', r'</em> (\1', text)
    # one-off broken anchor in EN footnote 37
    text = text.replace('<em>Sollicitudo Rei S</em> ocialis', '<em>Sollicitudo Rei Socialis</em>')
    # stray space before italicised trailing period ("ibid ." / "Cf .")
    text = re.sub(r'(\w) <em>\.</em>', r'\1.', text)

    return text.strip()

def emphasize(t):
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', t)
    return t

def unescape(t):
    t = t.replace('\xa0', ' ')
    t = re.sub(r'\\([\\`*_{}\[\]()#+\-.!>~|"\'])', r'\1', t)
    return t

def strip_md(s):
    s = s.replace('**', '')
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)
    s = s.replace('\xa0', ' ').strip()
    return s

# ---------- chapter / heading detection ----------
CHAPTER_DIV = re.compile(
    r'^(?:'
    r'INTRODUCTION|INTRODUCCI[ÓO]N|'
    r'CONCLUSION|CONCLUSI[ÓO]N|'
    r'CHAPTER (?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)|'
    r'Chapitre\s+\d+|'
    r'CAP[ÍI]TULO (?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO|DÉCIMO)'
    r')$'
)
LABEL_PRETTY = {
    'INTRODUCTION':'Introduction','INTRODUCCIÓN':'Introducción','INTRODUCCION':'Introducción',
    'CONCLUSION':'Conclusion','CONCLUSIÓN':'Conclusión','CONCLUSION':'Conclusion',
}
ROMAN_TO_WORD = {1:'One',2:'Two',3:'Three',4:'Four',5:'Five',6:'Six',7:'Seven',8:'Eight',9:'Nine',10:'Ten'}
def pretty_label(plain, lang):
    # convert raw chapter divider to display label
    if plain in ('INTRODUCTION','INTRODUCCIÓN','CONCLUSION','CONCLUSIÓN'):
        return LABEL_PRETTY.get(plain, plain.title())
    m = re.match(r'^CHAPTER (\w+)$', plain)
    if m: return 'Chapter ' + m.group(1).title()
    m = re.match(r'^Chapitre\s+(\d+)$', plain)
    if m: return 'Chapitre ' + m.group(1)
    m = re.match(r'^CAP[ÍI]TULO (\w+)$', plain, re.I)
    if m: return 'Capítulo ' + m.group(1).title()
    return plain.title()

para_re = re.compile(r'^(\d+)\\?\.\s*(.*)$', re.S)

def is_chapter_div(stripped_plain):
    return bool(CHAPTER_DIV.match(stripped_plain))

def is_all_caps(plain):
    letters = [c for c in plain if c.isalpha()]
    return len(letters) > 0 and all(c.isupper() for c in letters)

def is_italic_line(raw_md_after_bold_strip):
    test = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', raw_md_after_bold_strip).strip()
    return test.startswith('_') or test.endswith('_')

# ---------- parse one language ----------
def parse_lang(code):
    cfg = LANGS[code]
    md = open(cfg['src']).read()
    lines = md.split('\n')
    # find body
    sep_idx = None
    for i, l in enumerate(lines):
        if l.strip() == '* * *':
            sep_idx = i; break
    intro_idxs = []
    for i, l in enumerate(lines):
        if strip_md(l) in ('INTRODUCTION','INTRODUCCIÓN'):
            intro_idxs.append(i)
    body_start = intro_idxs[-1]; body_end = sep_idx
    body = lines[body_start:body_end]
    fn_lines = lines[body_end+1:]

    nodes = []
    i = 0; ch_count = 0; prev_was_chapter = False
    while i < len(body):
        raw = body[i].strip()
        if not raw:
            i += 1; continue
        pm = para_re.match(raw)
        if pm:
            num = int(pm.group(1)); content = pm.group(2)
            nodes.append({'type':'para','n':num,'html':conv_inline(content)})
            prev_was_chapter = False
            i += 1; continue
        plain = strip_md(raw)
        # signature lines
        if raw.startswith('_') and cfg['sig_marker'] in raw:
            nodes.append({'type':'sig','html':conv_inline(raw)})
            i += 1; continue
        if plain == cfg['sig_name']:
            nodes.append({'type':'sig','html':conv_inline(raw)})
            i += 1; continue
        # chapter divider
        if is_chapter_div(plain):
            ch_count += 1
            label = pretty_label(plain, code)
            # consume following title lines:
            #  - EN/ES (bold-wrapped, ALL CAPS): only ALL CAPS following lines
            #  - FR (plain-text, mixed case): any non-numbered non-italic non-divider line
            allow_mixed = (code == 'fr')
            titleparts = []
            j = i + 1
            while j < len(body):
                nx = body[j].strip()
                if not nx: j += 1; continue
                if para_re.match(nx): break
                np = strip_md(nx)
                if is_chapter_div(np): break
                is_italic = nx.startswith('_') or nx.endswith('_')
                if is_italic: break
                if allow_mixed or is_all_caps(np):
                    titleparts.append(conv_inline(nx.replace('**','')))
                    j += 1; continue
                break
            title = ' '.join(titleparts) if titleparts else label
            nodes.append({'type':'chapter','id':f'ch{ch_count}','label':label,'title':title})
            i = j; continue
        # heading (section)
        stripped = raw.replace('**','')
        level = 2 if is_italic_line(stripped) else 1
        nodes.append({'type':'section','level':level,'html':conv_inline(stripped)})
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
            footnotes.append({'n':int(m.group(1)),'html':conv_inline(m.group(2))})

    # EN-only fix: stray "[10]" after footnote 110's sup in para 82
    if code == 'en':
        for n in nodes:
            if n.get('type') == 'para' and n.get('n') == 82:
                n['html'] = n['html'].replace('</sup>[10] In the decades', '</sup> In the decades')

    meta = {k:cfg[k] for k in ('descriptor','kind','pope','title','subtitle','date','place','source')}
    meta['lang'] = code
    meta['video'] = VIDEO
    meta['multimedia'] = MULTIMEDIA
    meta['languages'] = LANGUAGES
    meta['ui'] = cfg['ui']
    return {'meta':meta, 'nodes':nodes, 'footnotes':footnotes}

# ---------- run ----------
out_all = {}
for code in ('en','fr','es'):
    fnref_counter.clear()
    data = parse_lang(code)
    paras = [n for n in data['nodes'] if n['type']=='para']
    nums = [p['n'] for p in paras]
    missing = [k for k in range(1, max(nums)+1) if k not in nums] if nums else [1]
    assert not missing, f'{code} missing paragraphs: {missing}'
    assert len(paras) == 245, f'{code} paragraph count {len(paras)} != 245'
    assert len(data['footnotes']) == 224, f'{code} footnote count {len(data["footnotes"])} != 224'
    print(f'{code.upper()}: paras {len(paras)} ({nums[0]}-{nums[-1]}) · footnotes {len(data["footnotes"])} · chapters {sum(1 for n in data["nodes"] if n["type"]=="chapter")} · sections {sum(1 for n in data["nodes"] if n["type"]=="section")}')
    json.dump(data, open(f'/tmp/magnifica.{code}.json','w'), ensure_ascii=False, indent=1)
    out_all[code] = data
print('\nAll languages OK. JSON files written to /tmp/magnifica.{en,fr,es}.json.')
