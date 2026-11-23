"""Generate the field guide's static grade cards from its published records."""
import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from html import escape, unescape
import json
from pathlib import Path
import re
from urllib.parse import urlencode, quote

parser = argparse.ArgumentParser(description=__doc__)
here = Path(__file__).resolve().parent
default_site = here.parent / 'public/interp' if here.name == 'scripts' else here
parser.add_argument('site', type=Path, nargs='?', default=default_site,
                    help='Field guide directory containing the public records')
SITE = parser.parse_args().site.resolve()
MATCHED = SITE / 'instruments/matched'
OUT = SITE / 'tiers'
OUT.mkdir(exist_ok=True)
WEIGHTS = dict(S=10, A=5, B=3, C=1, D=0)
RUN = 'Qwen3.5-4B-handoff'
RULE = ('Each letter measures how many of the baseline’s misses the technique recovers: '
        '(hits − baseline hits) / (trials − baseline hits). S starts at 90%, A at 65%, '
        'B at 35%, C above zero. Matching or trailing the baseline earns D. '
        'If the baseline is perfect, the trial has no grade.')
CLASSES = {
    'leg-day': ('spider', 'bee'), 'rabbit': ('-ay', '-art'),
    'pass-the-brass': ('brass', 'silver'), 'the-e6-incident': ('white', 'black'),
    'knock-on-sky': ('upper', 'lower'), 'a-minor-adjustment': ('major', 'minor'),
    'who-let-the-mouse-peek': ('red', 'blue'), 'nobody-drew-a-triangle': ('outward', 'inward'),
    'cue-the-understudy': ('Alice gives', 'Bob gives'), 'made-you-blink': ('red', 'blue'),
    'new-york': ('Manhattan', 'Newark'), 'opposite-day-en-espanol': ('opposite', 'Spanish'),
    'oracle-blind-spot': ('pear', 'plum'), 'spin-the-week': ('Monday', 'Saturday'),
    'sum-thing': ('12', '13'), 'when-in-rome': ('Paris', 'Rome'),
    'which-great': ('Alexander', 'Catherine'), 'who-said-that': ('B', 'D'),
    'whose-job': ('hospital', 'university'),
}

def load(path):
    return json.loads(path.read_text())

def h(value):
    return escape(str(value), quote=True)

def link(url, label):
    return f'<a href="{h(url)}">{h(label)}</a>'

def record_path(file):
    return f'instruments/matched/data/{file}.json'

def bench(file, case, method, axis=None):
    fragment = '/'.join(quote(str(x), safe='') for x in (case, method, axis) if x is not None)
    return f'instruments/matched/{file}.html#{fragment}'

def run_link(case, mode, method):
    return 'range.html#' + urlencode(dict(run=RUN, event=mode, method=method, story=case))

@dataclass
class Grade:
    tool: str
    mode: str
    question: str
    hit: int
    total: int
    base: int
    baseline: str
    site: str
    rule: str
    sources: list
    headers: tuple
    rows: list

    @property
    def grade(self):
        if self.base == self.total:
            return '—'
        gain = Fraction(self.hit - self.base, self.total - self.base)
        for letter, cutoff in [('S', 90), ('A', 65), ('B', 35)]:
            if gain * 100 >= cutoff:
                return letter
        return 'C' if gain > 0 else 'D'

    @property
    def anchor(self):
        return f'{self.tool}-{self.mode.lower()}'

def site_label(d):
    site = d['layer'] if isinstance(d['layer'], str) else f"block {d['layer']}"
    return f"{d['model']} · replay at {site} · revision {str(d['revision'])[:10]}"

def scored_states(slug, d, pilot):
    """The expected concept comes from the prompt or rules, never from the tool."""
    cases = d['cases']
    if pilot:
        truth = {r['id']: r['query'] for r in pilot['cases']}
        return [(c, i, q[label]) for c in cases for q in [truth[c['id']]]
                if q['source'] != q['donor'] for i, label in enumerate(('source', 'donor'))]
    if slug == 'knock-on-sky':
        return [(c, 0, {'upper-cell': 0, 'lower-cell': 1}[c['id']]) for c in cases]
    if slug == 'the-e6-incident':
        return [(c, i, int(c[k]['board'][37] == 1)) for c in cases for i, k in enumerate(('clean','edited'))]
    case = cases[0]  # One pair for the named contrast. Repeated downstream questions share these states.
    return [(case, 0, 0), (case, 1, 1)]

def read_grades(slug, file, d, states, lenses_only=False):
    labels = CLASSES[file.removesuffix('-4b')]
    total = len(states)
    baseline = max(Counter(truth for _, _, truth in states).values())
    first = states[0][0]['id']
    src = record_path(file)
    sample = {
        'leg-day':'The spider clue and its bee transplant form one pair.',
        'rabbit':'The gray/heart pair supplies the two named rhyme families. The dead/red replay falls outside that contrast.',
        'pass-the-brass':'The owner, relay and map questions share a brass/silver prefix. Count that state pair once.',
        'the-e6-incident':'The game board and the counterfactual rules board supply the two E6 colors.',
        'knock-on-sky':'Read the upper and lower cells of the original image at seed 104.',
    }.get(slug, 'Count the original and the donor-state transplant for each question whose target changes.' if len(states)>2 else 'Count the original and edited state of this prompt pair once each.')
    def result(tool, question, rule, detail, headers, axis=None):
        return Grade(tool, 'Read', question, sum(x[-1]=='Hit' for x in detail), total, baseline,
                     'Always name one class (majority baseline)', site_label(d), rule+' '+sample,
                     [(bench(file,first,tool,axis),'Inspect this readout'), (src,'Source JSON')], headers, detail)
    if not lenses_only:
        for tool, card in d['components'].items():
            j = card['selected']
            groups = [[r[j] for ref,r in zip(d['reference'],card['reference'],strict=True)
                       if ref['label']==i] for i in (0,1)]
            centers = [sum(g)/len(g) for g in groups]
            rows = []
            for c,i,y in states:
                value = c['components'][tool][i][j]
                a,b = [abs(value-center) for center in centers]
                guess = 0 if a<b else 1 if b<a else None
                rows.append([c['id'], ('Original','Edited')[i], f'{value:.5f}',labels[y],
                             labels[guess] if guess is not None else 'Tie', 'Hit' if guess==y else 'Miss'])
            rule = (f"Use the bench’s selected coordinate ({card['ids'][j]}, {card['unit']}). Call the nearer reference mean: "
                    f"{labels[0]} = {centers[0]:.6g} ({len(groups[0])} references), "
                    f"{labels[1]} = {centers[1]:.6g} ({len(groups[1])}). A tie misses. "
                    "Only the replay states below earn points.")
            yield result(tool,f'Can it tell {labels[0]} from {labels[1]}?',rule,rows,
                         ('Saved pair','State','Coordinate','Expected','Read','Result'),j)
    if not d.get('target_tokens'):
        return
    words = [s.strip() for s in d['target_tokens']]
    if slug == 'leg-day':
        words = ['spider','bee']
    for tool in states[0][0].get('lenses',{}):
        if tool not in d['tool_labels']:
            continue
        rows = []
        for c,i,y in states:
            reading = c['lenses'][tool][i]
            ranks = reading.get('ranks',{})
            if all(w in ranks for w in words):
                a,b = (ranks[w] for w in words)
                display = (a,b)
            else:
                # Only score a visible exact token. A truncated list establishes a lower bound.
                top = reading['top']
                visible = {}
                for rank,token in enumerate(top,1):
                    visible.setdefault(token['token'].strip(),rank)
                absent = len(top)+1
                a,b = (visible.get(w,absent) for w in words)
                display = tuple(f'>{len(top)}' if v==absent else v for v in (a,b))
            guess = 0 if a<b else 1 if b<a else None
            rows.append([c['id'],('Original','Edited')[i],*display,words[y],'Hit' if guess==y else 'Miss'])
        yield result(tool,f'Which ranks higher, “{words[0]}” or “{words[1]}”?',
                     'Read the saved candidate ranks when available. For a saved top-token list, match the exact word after trimming outer whitespace. If neither word appears, the reader abstains and the trial misses. Rank 1 is best.',
                     rows,('Saved pair','State',words[0]+' rank',words[1]+' rank','Expected','Result'))

def brass_grades(d):
    text=(SITE/'range.html').read_text()
    start=re.search(r'const data\s*=\s*',text).end()
    stories=json.JSONDecoder().raw_decode(text[start:])[0][RUN]
    pairs=[]
    for r in stories:
        j=next(j for j,q in enumerate(r['case']['qs']) if q['k']=='direct')
        pairs.append((r['case'],r['case']['qs'][j],r['answers'][j]))
    for tool in [k.removeprefix('forecast_') for k in pairs[0][2] if k.startswith('forecast_')]+['patch']:
        for mode in (['edit'] if tool=='patch' else ['forecast','edit']):
            key='patch' if tool=='patch' else mode+'_'+tool
            rows=[]; base=0
            for c,q,a in pairs:
                expected=int(a['patch']>0) if mode=='forecast' else q['y'][1-c['side']]
                pred=int(a[key]>0)
                base+=int((a['base']>0)==expected)
                rows.append([c['id'],q['opts'][int(a['base']>0)],q['opts'][expected],q['opts'][pred],
                             f"{a[key]:+.5f}",'Hit' if pred==expected else 'Miss'])
            question=('Can it forecast the patched owner?' if mode=='forecast' else 'Can it produce the requested owner?')
            rule=('Target: the full donor patch’s answer.' if mode=='forecast' else 'Target: the owner specified by the word-swapped story.')
            m='means' if tool=='patch' else tool
            yield Grade('gradient_ranked_ica' if tool=='gradica' else tool, mode.title(), question,
                        sum(r[-1]=='Hit' for r in rows),len(rows),base,'Keep the original model answer',site_label(d),
                        rule+' All 200 direct owner questions count. A positive margin selects the second answer. '
                        'In the Range, read the direct row; the full patch appears in the Patched model column.',
                        [(run_link(rows[0][0],mode,m),'Open the first story in the Range')],('Story','Original','Target','Answer','Margin','Result'),rows)

def pilot_grades(pilot,slug,d):
    for tool in pilot['cases'][0]['edits']:
        if tool in ('self','random_ica_norm'):
            continue
        rows=[];base=0
        for c in pilot['cases']:
            q=c['query']; target=q['answers'][q['donor']].strip()
            actual=(c['edits'][tool]['preferred'] or 'Tie').strip()
            clean=(c['original']['preferred'] or 'Tie').strip()
            base+=clean==target
            rows.append([c['id'],clean,target,actual,'Hit' if actual==target else 'Miss'])
        yield Grade('patch' if tool=='full' else tool,'Edit','Does the edit give the requested answer?',
                    sum(r[-1]=='Hit' for r in rows),len(rows),base,'Keep the original two-choice answer',
                    site_label(d),'Use the recorded preferred answer for each edit. A tied margin misses. All eight queries count, including the four whose answer should stay fixed.',
                    [(slug+'.html','Play the exhibit'),('records/three-more/'+slug+'.json','Edit trials and controls')],
                    ('Case','Original','Target','Edited','Result'),rows)

def special_grades(slug,d):
    if slug=='awkward-pause':
        data=load(SITE/'records/pause.json')
        rows=[];base=0
        for c in data['cards']:
            a=c['conditions']; random=a['random-remove-0']['vowel_mass']; six=a['remove-all']['vowel_mass']
            base+=random<.5
            rows.append([c['prompt'],f"{a['clean']['vowel_mass']:.4f}",f'{random:.4f}',f'{six:.4f}','Hit' if six<.5 else 'Miss'])
        yield Grade('group','Edit','Can removing six neurons push vowel mass below half?',sum(r[-1]=='Hit' for r in rows),
                    len(rows),base,'Remove the recorded random six',d['model']+' · six MLP down-projection inputs · final article',
                    'On each “an” stem, score a hit when the saved vowel-word probability mass after removal is below 0.5.',
                    [(bench('awkward-pause-llama','05-an-remove','group'),'Inspect the attic removal'),('records/pause.json','All removal and control rows')],
                    ('Stem','Clean','Random six','Remove six','Result'),rows)
        picks=data['discovery']['picks']
        target=data['members']
        found=picks['mean_gap.all_layers']
        rows=[[l,n,found.get(l,'—'),picks['mean_gap.known_layers'].get(l,'—'),'Hit' if found.get(l)==n else 'Miss'] for l,n in target.items()]
        yield Grade('means','Read','Can the a/an mean gap rediscover all six neurons?',sum(r[-1]=='Hit' for r in rows),
                    len(rows),0,'Select no neurons',d['model']+' · all-layer discovery',
                    'Score exact published layer and unit matches in the six all-layer picks. The layer-hinted picks appear alongside for comparison.',
                    [('instruments/awkward-pause.html#means','Inspect discovery'),('records/pause.json','Discovery picks and member IDs')],
                    ('Layer','Published unit','All-layer pick','Hinted pick','Result'),rows)
    if slug=='leg-day':
        data=load(SITE/'records/legs-4b.json')
        rows=[]
        for t in data['trials']:
            if t['patch']=='clue end, name question':
                v=t['top_by_layer'][12]; rows.append([t['source'],t['donor'],t['source_answer'],t['donor_answer'],v,'Hit' if v==t['donor_answer'] else 'Miss'])
        yield Grade('patch','Edit','Does block 12 give the donor’s leg count?',sum(r[-1]=='Hit' for r in rows),
                    len(rows),sum(r[2]==r[3] for r in rows),'Keep the original count',site_label(d),
                    'Score all eligible name-question donors at the end of the clue, including pairs with equal leg counts.',
                    [('leg-day.html','Play the leg swap'),('records/legs-4b.json','Layer sweep and clean answers')],
                    ('Receiver','Donor','Original','Target','Edited','Result'),rows)
    if slug=='rabbit':
        data=load(SITE/'records/rabbit-4b.json'); row=data['summary']['by_layer'][18]
        yield Grade('patch','Edit','Does the line end in the donor’s rhyme family?',row['donor'],sum(row.values()),0,
                    'Keep the eligible recipient’s own rhyme',site_label(d),
                    'At the featured block 18, count the recorded donor-labelled line endings across the eligible couplets. The candidate rhyme lists can miss valid rhymes.',
                    [('rabbit.html','Read the couplets'),('records/rabbit-4b.json','Layer counts and eligibility')],
                    ('Layer','Own','Donor','Other'),[[18,row['own'],row['donor'],row['other']]])

def gather(slug,file,d):
    pilot_path=SITE/'records/three-more'/(slug+'.json')
    pilot=load(pilot_path) if pilot_path.exists() else None
    grades=[]
    if slug!='awkward-pause':
        states=scored_states(slug,d,pilot)
        grades.extend(read_grades(slug,file,d,states))
        if file.endswith('-4b'):
            extra=file[:-3]; companion=load(SITE/record_path(extra))
            used={g.tool for g in grades}
            grades.extend(g for g in read_grades(slug,extra,companion,scored_states(slug,companion,None),True)
                          if g.tool not in used)
    if slug=='pass-the-brass':
        handoff=list(brass_grades(d))
        used={g.tool for g in handoff}
        grades=[g for g in grades if g.tool not in used]+handoff
    elif pilot:
        grades.extend(pilot_grades(pilot,slug,d))
    elif d['kind']=='Exploratory Qwen prompt-pair transplant':
        c=d['cases'][0]; a,b=d['target_tokens']
        clean=int(c['clean']['margin']>0); edit=int(c['edited']['margin']>0)
        grades.append(Grade('patch','Edit',f'Does the model now prefer “{b.strip()}”?', edit,1,clean,
                            'Keep the original two-choice answer',site_label(d),
                            'The donor answer is the second named token. A positive final margin favors that token.',
                            [(bench(file,c['id'],'patch'),'Inspect the transplant'),(record_path(file),'Source JSON')],
                            ('Case','Original margin','Edited margin','Target'),[[c['id'],c['clean']['margin'],c['edited']['margin'],b.strip()]]))
    grades.extend(special_grades(slug,d))
    return grades

def page(title,content,base='../'):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{h(title)} · Counterfactual Zoo</title><link rel="stylesheet" href="{base}assets/paper.css"><link rel="stylesheet" href="{base}assets/tiers.css"></head><body class="tier-page"><a class="skip" href="#main">Skip to content</a><nav class="topbar"><a class="brand" href="{base}index.html">Weekend field notes</a><span class="navlinks"><a href="{base}index.html#zoo">Zoo</a><a href="{base}tier-list.html">Tier list</a><a href="{base}range.html">Range</a></span></nav><main id="main">{content}</main></body></html>'''

def stamp(g):
    return f'<span class="stamp grade-{g.grade}" aria-label="Grade {h(g.grade)}">{g.grade}</span>'

def mini(g,href,name):
    return f'<a class="mini" href="{h(href)}">{stamp(g)}<span><b>{h(name)}</b><small>{g.mode} · {g.hit}/{g.total} hits</small></span></a>'

def evidence(g,name):
    denom=g.total-g.base
    gain=(f'{100*(g.hit-g.base)/denom:.1f}% of available improvement' if denom else 'Ungraded · the baseline already succeeds on every trial')
    threshold={'S':'S starts at 90%', 'A':'A starts at 65%', 'B':'B starts at 35%', 'C':'C is any gain below 35%', 'D':'D matches or trails the baseline'}.get(g.grade,'')
    if threshold:
        gain += ' · '+threshold
    sources=' · '.join(link('../'+u,t) for u,t in g.sources)
    rows=[]
    for row in g.rows:
        cells=[h(v) for v in row]
        if g.sources[0][0].startswith('range.html'):
            m='gradica' if g.tool=='gradient_ranked_ica' else 'means' if g.tool=='patch' else g.tool
            cells[0]=link('../'+run_link(row[0],g.mode.lower(),m),row[0])
        elif g.mode=='Read' and g.sources[0][0].startswith('instruments/matched/') and 'Saved pair' in g.headers:
            reader,fragment=g.sources[0][0].split('#',1)
            selection=fragment.split('/',1)[1]
            cells[0]=link('../'+reader+'#'+quote(str(row[0]),safe='')+'/'+selection,row[0])
        rows.append('<tr>'+''.join('<td>'+v+'</td>' for v in cells)+'</tr>')
    headings=''.join('<th scope="col">'+h(v)+'</th>' for v in g.headers)
    return f'''<article class="receipt" id="{h(g.anchor)}" tabindex="-1"><header>{stamp(g)}<div><small>{h(name)} · {g.mode}</small><h2>{h(g.question)}</h2></div></header><p class="math"><strong>{g.hit}/{g.total} hits</strong> · {h(g.baseline)}: {g.base}/{g.total}<br>{h(gain)}</p><p>{h(g.rule)}</p><p class="source">{h(g.site)}<br>{sources}</p><div class="tier-scroll" role="region" tabindex="0" aria-label="{h(name)} {g.mode.lower()} evidence"><table><thead><tr>{headings}</tr></thead><tbody>{''.join(rows)}</tbody></table></div></article>'''

def upsert(path,section,fragment,marker):
    text=re.sub(f'<!--{section}-->.*?<!--/{section}-->','',path.read_text(),flags=re.S)
    assert marker in text,(path,marker)
    path.write_text(text.replace(marker,marker+f'<!--{section}-->{fragment}<!--/{section}-->',1))

def nav(path,base):
    html=path.read_text()
    if 'class="navlinks"' in html:
        html=re.sub(r'(<span class="navlinks">\s*<a [^>]*>Zoo</a>)(?:<a href="[^"]*tier-list.html">Tier list</a>)?',
                    lambda m:m[1]+f'<a href="{base}tier-list.html">Tier list</a>',html,count=1)
    elif '<nav' in html and 'tier-list.html">Tier list' not in html:
        html=html.replace('</nav>',f'<a href="{base}tier-list.html">Tier list</a></nav>',1)
    path.write_text(html)

def style(path,base):
    html=path.read_text()
    if 'assets/tiers.css' not in html:
        path.write_text(html.replace('</head>',f'<link rel="stylesheet" href="{base}assets/tiers.css"></head>',1))

def summary_card(groups,slug,base,name):
    links=[]
    for g in groups:
        links.append(f'<a class="grade-face" href="{base}tiers/{slug}.html#{h(g.anchor)}">{stamp(g)}<span><b>{g.mode}</b><small>{g.hit}/{g.total} hits</small><small>Baseline {g.base}/{g.total}</small></span></a>')
    return f'<div class="tool-card"><h3>{h(name)}</h3>{"".join(links)}</div>'

def grouped(grades):
    groups=defaultdict(list)
    for g in grades:
        groups[g.tool].append(g)
    return groups

catalog=load(SITE/'records/matched-catalog.json')
for pilot in ('a-minor-adjustment','who-let-the-mouse-peek','nobody-drew-a-triangle'):
    catalog[pilot]=[dict(path='matched/'+pilot+'.html')]
atlas={}
toolnames={}
for slug,runs in catalog.items():
    if slug.endswith('-9b'):continue
    file=Path(runs[0]['path']).stem
    # Credit the actual checkpoint used by the primary exhibit's causal replay.
    d=load(SITE/record_path(file))
    path=SITE/(slug+'.html')
    if not path.is_file():path=SITE/'notes'/path.name
    base='../' if path.parent!=SITE else ''
    source=path.read_text()
    header=re.search(r'<header class="exhibit-head">.*?</header>',source,re.S)[0]
    title=unescape(re.search(r'<h1>(.*?)</h1>',header)[1])
    drawing=re.search(r'<svg.*?</svg>',header,re.S)[0]
    names=dict(d['tool_labels'],patch='Full-state patch',rome='ROME writer key',group='Neuron communities')
    toolnames.update(names)
    grades=gather(slug,file,d)
    assert all(0 <= g.hit <= g.total and 0 <= g.base <= g.total for g in grades)
    assert len({g.anchor for g in grades})==len(grades)
    groups=grouped(grades)
    order={'leg-day':['patch','ica','skeleton_full'],'pass-the-brass':['ace','means','patch'],
           'awkward-pause':['group','means'],'knock-on-sky':['brush_door','ica','pca'],
           'the-e6-incident':['probe','ica','pca']}.get(slug,['patch','ica','skeleton_full'])
    order=list(dict.fromkeys([k for k in order if k in groups]+list(groups)))
    cards=[summary_card(groups[k],slug,base,names[k]) for k in order]
    extra=('<details><summary>'+str(len(cards)-3)+' more techniques</summary><div class="card-row">'+''.join(cards[3:])+'</div></details>') if len(cards)>3 else ''
    next_link=link(base+'tier-list.html','Both tier lists')
    fragment=f'<section class="tier-hand" aria-label="Technique grades"><div class="hand-head"><h2>Technique grades</h2>{next_link}</div><div class="card-row">{"".join(cards[:3])}</div>{extra}<a class="tier-catalog" href="{base}tiers/{slug}.html">All grades, rules and ungraded readouts</a></section>'
    # Follow the header while leaving the causal figure and all its controls intact.
    upsert(path,'tier-hand',fragment,'</header>')
    style(path,base); nav(path,base)
    shortcut=link('../'+path.relative_to(SITE).as_posix(),'Play '+title)
    receipts=''.join(evidence(g,names[g.tool]) for k in order for g in groups[k])
    ungraded=[]
    for k,label in names.items():
        if k in groups:continue
        target_file=file
        for run in runs:
            if k in run.get('methods',{}).values():
                target_file=Path(run['path']).stem
                break
        ungraded.append(link('../'+bench(target_file,d['cases'][0]['id'],k),label))
    select=''.join(f'<option value="{h(g.anchor)}">{h(names[g.tool])} · {g.mode} · {g.grade}</option>' for k in order for g in groups[k])
    contents=f'''<header class="tier-hero"><div><p class="kicker">Grade book</p><h1>{h(title)}</h1><p>{shortcut} · {link('../tier-list.html','Both tier lists')}</p></div>{drawing}</header><label class="receipt-picker">Technique and trial <select id="receipt-picker">{select}</select></label>{receipts}<details class="rulebook"><summary>How the letters work</summary><p>{h(RULE)}</p></details><details class="rulebook" id="ungraded"><summary>Ungraded instruments ({len(ungraded)})</summary><p>These instruments have no scored trial here. Open one to see its readout or measurement status.</p><div class="ungraded">{' · '.join(ungraded)}</div></details><script src="../assets/tier-receipts.js"></script>'''
    (OUT/(slug+'.html')).write_text(page(title+' grades',contents))
    atlas[slug]=(title,drawing,grades,path.relative_to(SITE).as_posix())

def ranking_family(tool):
    if tool.startswith('brush_'):
        return 'GANPaint brushes'
    if tool.startswith('skeleton_'):
        return 'Skeleton Lens'
    if tool in ('J','J-1000'):
        return 'J-lens'
    return toolnames[tool]

def rankings(weighted):
    techniques=defaultdict(list)
    for slug,(title,_,grades,_) in atlas.items():
        families=defaultdict(list)
        for g in grades:
            if g.grade in WEIGHTS:
                families[ranking_family(g.tool)].append(g)
        for name,scored in families.items():
            techniques[name].append((slug,title,scored))
    entries=[]
    for k,animals in techniques.items():
        crowns=sum(any(g.grade=='S' for g in gg) for _,_,gg in animals)
        points=sum(Fraction(sum(WEIGHTS[g.grade] for g in gg),len(gg)) for _,_,gg in animals)/len(animals)
        value=points if weighted else crowns
        entries.append((value,k,animals))
    rows=[];prev=None
    for i,(value,name,animals) in enumerate(sorted(entries,key=lambda x:(-x[0],x[1])),1):
        if value!=prev:rank=i;prev=value
        contributors=[]
        for slug,title,gg in sorted(animals,key=lambda x:x[1]):
            if not weighted and value and not any(g.grade=='S' for g in gg):continue
            for g in gg:
                if weighted or not value or g.grade=='S':
                    label=title if name==toolnames[g.tool] else title+' · '+toolnames[g.tool]
                    contributors.append(mini(g,f'tiers/{slug}.html#{g.anchor}',label))
        coverage=f'{len(animals)} scored animal'+('' if len(animals)==1 else 's')
        num=f'{float(value):.2f}' if weighted else f'{value} S'
        rows.append(f'<details class="standing"><summary><span class="place">{rank}</span><span><b>{h(name)}</b><small>{coverage}</small></span><strong>{num}</strong></summary><div class="contributions">{"".join(contributors)}</div></details>')
    return ''.join(rows)

def favorites():
    # Editorial picks use the same instrument, case and checkpoint as their receipts.
    cards = []
    spider = atlas['leg-day'][1].replace('viewBox="0 0 194 96"', 'viewBox="4 8 84 84"')
    for tool, reader, flavor in [
        ('J', 'leg-day', 'We asked for a number. It found the spider.'),
        ('raw', 'leg-day-4b', 'The spider says “{top}”. Permanent spot on the team.'),
    ]:
        trial = next(g for g in atlas['leg-day'][2] if g.tool == tool and g.mode == 'Read')
        record = load(SITE / record_path(reader))
        case = next(c for c in record['cases'] if c['id'] == 'spider-from-bee')
        top = case['lenses'][tool][0]['top'][0]['token'].strip()
        portrait = spider if tool == 'J' else f'<span class="token-portrait">{h(top)}</span>'
        name = toolnames[tool]
        cards.append(f'''<article class="pull-card">
          <a class="pull-reader" href="{h(bench(reader,case['id'],tool))}" aria-label="Open {h(name)} on the spider clue">
            <span class="pull-portrait" aria-hidden="true">{portrait}</span>
            <span><b>{h(name)}</b><small>{h(record['model'].split('/')[-1])} · block {record['layer']}</small></span>
          </a>
          <p>{h(flavor.format(top=top))}</p>
          <a class="pull-score" href="tiers/leg-day.html#{h(trial.anchor)}">Leg Day score · {trial.grade} · {trial.hit}/{trial.total}</a>
        </article>''')
    return ('<section class="picks-row" id="s-plus" aria-labelledby="picks-title"><header>'
            '<strong>S+</strong><h2 id="picks-title">Zookeeper’s picks</h2></header>'
            + ''.join(cards) + '</section>')

animals=''.join(f'<a href="tiers/{slug}.html">{drawing}<span>{h(title)}</span></a>' for slug,(title,drawing,_,_) in sorted(atlas.items(),key=lambda x:x[1][0]))
content=f'''<header class="tier-hero ranking-hero"><div><p class="kicker">Counterfactual Zoo</p><h1>The tier list</h1><p>I get two S+ picks. The animals get to grade everything else.</p></div></header>
{favorites()}
<nav class="tier-jumps" aria-label="Jump to a ranking"><a href="#most-s">Most S grades</a><a href="#weighted">Weighted ranking</a><a href="#animals">By animal</a></nav>
<div class="rank-pair"><section id="most-s"><h2>Most S grades</h2><p>One S per animal. Click a technique to see who gave it one.</p>{rankings(False)}</section>
<section id="weighted"><h2>The zookeeper’s ranking</h2><p>S = 10 · A = 5 · B = 3 · C = 1 · D = 0. Average within each animal, then across animals.</p>{rankings(True)}</section></div>
<details class="rulebook"><summary>How the scoring works</summary><p>{h(RULE)}</p><p>Each animal gets one vote. Two spider states count as much as 200 key stories. Open a grade to see the rows.</p><p>Ungraded trials sit out. The three Skeleton Lens branches share a spot, as do the two J-lens fits and the GANPaint brushes. Ties share a place.</p></details>
<h2 id="animals">Find an animal</h2><div class="animal-directory">{animals}</div>'''
(SITE/'tier-list.html').write_text(page('The tier list',content,''))
for name in ['index','notebook','range']:
    nav(SITE/(name+'.html'),'')
