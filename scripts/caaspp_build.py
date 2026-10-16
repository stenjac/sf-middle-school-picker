import json
P='./'  # folder holding raw.json (from caaspp_extract.py) and state.json
raw=json.load(open(P+'raw.json')); st=json.load(open(P+'state.json'))
GROUPS=[(1,'All students'),(31,'Low-income'),(111,'Not low-income'),(160,'English learners'),(128,'Students with disabilities'),(76,'Asian'),(74,'Black'),(77,'Filipino'),(78,'Latino'),(79,'Pacific Islander'),(80,'White'),(144,'Two or more races'),(4,'Girls'),(3,'Boys')]
def clean(d): return {subj:{str(g):v for g,v in d[subj].items()} for subj in d}
res=raw['result']
out={'meta':{
  'year':'2025–26','priorYear':'2024–25','grades':'6–8',
  'measure':'Share of students scoring Proficient or Advanced (called "Standard Met" or "Exceeded" before 2026)',
  'source':'California Department of Education / ETS, CAASPP Smarter Balanced research files (San Francisco County, all student groups; statewide all-students file)',
  'sourceUrl':'https://caaspp-elpac.ets.org/caaspp/ResearchFileListSB?ps=true&lstTestYear=2026&lstTestType=B&lstCounty=38&lstDistrict=00000',
  'suppression':'Groups with fewer than 11 students tested are not reported by the state.',
  'method':'Grades 6, 7 and 8 only. K-8 schools and KIPP (grades 5-8) are combined from per-grade student counts, so every school is compared on its middle grades.'},
 'groups':[{'id':str(g),'label':l} for g,l in GROUPS],
 'benchmarks':{'sfusd':{yr:clean(v) for yr,v in res['benchmarks']['sfusd'].items()},'state':st},
 'schools':{sid:{'cds':f'38{d}{c}',**{yr:clean(v) for yr,v in res['schools'][sid].items()}} for sid,(d,c) in raw['codes'].items()}}
json.dump(out,open('data/caaspp.json','w'),indent=1,ensure_ascii=False)
print(json.dumps(out['schools']['everett']['2026']['ela']))
