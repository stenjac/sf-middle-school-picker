import csv, json, sys, collections
D='caaspp_raw/'  # unzip the CAASPP research files here: x26/, x25/, ent/
MAP = {  # our id -> (district code, school name in CAASPP entities)
 'presidio':('68478','Presidio Middle'),'giannini':('68478','Giannini (A.P.) Middle'),'hoover':('68478','Hoover (Herbert) Middle'),
 'roosevelt':('68478','Roosevelt Middle'),'marina':('68478','Marina Middle'),'francisco':('68478','Francisco Middle'),
 'aptos':('68478','Aptos Middle'),'james_lick':('68478','Lick (James) Middle'),'everett':('68478','Everett Middle'),
 'willie_brown':('68478','Brown Jr. (Willie L) Middle'),'vis_valley':('68478','Visitacion Valley Middle'),
 'mlk':('68478','King Jr. (Martin Luther) Academic Middle'),'denman':('68478','Denman (James) Middle'),
 'alice_fong_yu':('68478','Yu (Alice Fong) Elementary'),'claire_lilienthal':('68478','Lilienthal (Claire) Elementary'),
 'lawton':('68478','Lawton Alternative'),'rooftop':('68478','Rooftop Elementary'),'bvhm':('68478','Buena Vista/ Horace Mann K-8'),
 'bessie_carmichael':('68478','Carmichael (Bessie)/FEC'),'paul_revere':('68478','Revere (Paul) Elementary'),
 'sfcs':('68478','San Francisco Community Alternative'),'gateway':('68478','Gateway Middle'),
 'teca':('68478','Thomas Edison Charter Academy'),'creative_arts':('68478','Creative Arts Charter'),
 'new_school_sf':('76927','The New School of San Francisco'),'kipp_bayview':('68478','KIPP Bayview Academy'),
 'kipp_sf_bay':('68478','KIPP San Francisco Bay Academy'),
}
GROUPS = [(1,'All students'),(31,'Low-income (socioeconomically disadvantaged)'),(111,'Not low-income'),
 (160,'English learners'),(128,'Students with disabilities'),(76,'Asian'),(74,'Black or African American'),
 (77,'Filipino'),(78,'Hispanic or Latino'),(79,'Pacific Islander'),(80,'White'),(144,'Two or more races'),(4,'Female'),(3,'Male')]
GIDS={g for g,_ in GROUPS}

ent={}
for r in csv.DictReader(open(D+'ent/sb_ca2026entities_csv.txt',encoding='latin-1'),delimiter='^'):
    if r['County Code']=='38': ent[(r['District Code'],r['School Name'])]=r['School Code']
codes={}
for k,(d,n) in MAP.items():
    codes[k]=(d,ent[(d,n)])

def num(x):
    try: return float(x)
    except: return None

def load(path, want):
    # want: set of (district, school) ; also district 68478 school 0000000 ; county 38 row
    out=collections.defaultdict(dict)
    for r in csv.DictReader(open(path,encoding='latin-1'),delimiter='^'):
        key=(r['District Code'],r['School Code'])
        if key not in want: continue
        g=int(r['Student Group ID'])
        if g not in GIDS: continue
        grade=int(r['Grade']); test=int(r['Test ID'])
        if test not in (1,2) or grade not in (6,7,8,13): continue
        cc=r.get('Count Proficient and Above', r.get('Count Standard Met and Above')); pc=r.get('Percentage Proficient and Above', r.get('Percentage Standard Met and Above'))
        out[key][(test,g,grade)]=(num(r['Total Students Tested with Scores']),num(cc),num(pc))
    return out

want={v for v in codes.values()}|{('68478','0000000')}
def summarize(rows, key, k8):
    res={}
    for test,subj in ((1,'ela'),(2,'math')):
        res[subj]={}
        for g,_ in GROUPS:
            if k8:
                tot=cnt=0; ok=True; any_=False
                for gr in (6,7,8):
                    v=rows[key].get((test,g,gr))
                    if not v: continue
                    any_=True
                    if v[0] is None or v[1] is None: ok=False; break
                    tot+=v[0]; cnt+=v[1]
                if any_ and ok and tot>=11: res[subj][g]={'pct':round(100*cnt/tot),'n':int(tot)}
                elif any_: res[subj][g]=None
            else:
                v=rows[key].get((test,g,13))
                if v and v[2] is not None and v[0] is not None: res[subj][g]={'pct':round(v[2]),'n':int(v[0])}
                elif v: res[subj][g]=None
    return res

K8={'kipp_bayview','kipp_sf_bay','alice_fong_yu','claire_lilienthal','lawton','rooftop','bvhm','bessie_carmichael','paul_revere','sfcs','teca','creative_arts','new_school_sf'}
result={'meta':{}, 'schools':{}, 'benchmarks':{}}
for yr,f in (('2026',D+'x26/sb_ca2026_all_38_csv_v1.txt'),('2025',D+'x25/sb_ca2025_all_38_csv_v1.txt')):
    rows=load(f,want)
    for sid,key in codes.items():
        if key not in rows: print('MISSING',yr,sid); continue
        result['schools'].setdefault(sid,{})[yr]=summarize(rows,key,sid in K8)  # 6-8 schools: all-grades row; others: grades 6-8 combined
    result['benchmarks'].setdefault('sfusd',{})[yr]=summarize(rows,('68478','0000000'),True)
json.dump({'codes':codes,'result':result},open('raw.json','w'))
for sid in codes:
    a=result['schools'].get(sid,{}).get('2026',{})
    print(f"{sid:18} ELA {a.get('ela',{}).get(1)} MATH {a.get('math',{}).get(1)}")
print('SFUSD', result['benchmarks']['sfusd']['2026']['ela'][1], result['benchmarks']['sfusd']['2026']['math'][1])
