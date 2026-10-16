"""Build data/growth.json from CDE's Dashboard growth-model file.

Usage: python3 scripts/growth_build.py path/to/growthmodeldownload2025.txt
Source: https://www.cde.ca.gov/TA/ac/cm/growthmodeldatafiles.asp
Matches schools by the CDS code stored in data/caaspp.json.
"""
import csv, json, sys

SRC = sys.argv[1]
caaspp = json.load(open('data/caaspp.json'))
cds_to_id = {s['cds']: sid for sid, s in caaspp['schools'].items()}
GROUPS = [('ALL', 'All students'), ('SED', 'Low-income'), ('EL', 'English learners'),
          ('SWD', 'Students with disabilities'), ('AS', 'Asian'), ('AA', 'Black'),
          ('FI', 'Filipino'), ('HI', 'Latino'), ('PI', 'Pacific Islander'),
          ('WH', 'White'), ('MR', 'Two or more races')]
GIDS = {g for g, _ in GROUPS}

def val(r):
    try:
        status = int(float(r['status']))
    except ValueError:
        return None
    return {'score': status, 'n': int(r['denom'] or 0), 'level': int(r['performancecategory'] or 0),
            'pctImproved': float(r['percentimprove']) if r['percentimprove'] else None}

schools, sfusd = {}, {}
for r in csv.DictReader(open(SRC, encoding='latin-1'), delimiter='\t'):
    if r['studentgroup'] not in GIDS:
        continue
    subj = r['subject'].lower()
    if r['rtype'] == 'S' and r['cds'] in cds_to_id:
        schools.setdefault(cds_to_id[r['cds']], {'ela': {}, 'math': {}})[subj][r['studentgroup']] = val(r)
    elif r['rtype'] == 'D' and r['cds'] == '38684780000000':
        sfusd.setdefault(subj, {})[r['studentgroup']] = val(r)

missing = sorted(set(cds_to_id.values()) - set(schools))
if missing:
    print('No growth data for:', missing)
out = {
    'meta': {
        'dashboard': '2025 California School Dashboard',
        'covers': 'Growth from spring 2023 to spring 2025 (weighted two-year average), grades 4-8',
        'measure': 'Average growth score: test-score points above or below students statewide who had similar scores the year before. 0 = typical.',
        'levels': {'1': 'Minimal Growth', '2': 'Moderate Growth', '3': 'Average Growth', '4': 'Accelerated Growth', '5': 'Exceptional Growth'},
        'cuts': 'Minimal: below -20 · Moderate: -20 to -6 · Average: -5 to +4 · Accelerated: +5 to +19 · Exceptional: +20 and up',
        'source': 'California Department of Education, Growth Model downloadable data file (2025)',
        'sourceUrl': 'https://www.cde.ca.gov/TA/ac/cm/growthmodeldatafiles.asp',
        'note': 'Level 0 means the state did not assign a level (too few students).'},
    'groups': [{'id': g, 'label': l} for g, l in GROUPS],
    'sfusd': sfusd,
    'schools': schools}
json.dump(out, open('data/growth.json', 'w'), indent=1, ensure_ascii=False)
print(len(schools), 'schools written')
