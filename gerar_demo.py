"""Create a repeatable fictional demo in data/vaultvet.db; never overwrite a database."""
from pathlib import Path
from datetime import date, timedelta
import random, sys, json, collections
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from database import Database, VACCINES

def generate():
    target = ROOT / 'data' / 'vaultvet.db'
    if target.exists():
        raise SystemExit('O banco já existe. Geração cancelada para preservar os dados.')
    rng = random.Random(20261002)
    db = Database(str(target))
    conn = db.conn
    names = ['Ana','Bruno','Carla','Daniel','Elisa','Felipe','Gabriela','Henrique','Isabela','João','Lara','Marcos','Nina','Otávio','Paula','Rafael','Sofia','Tiago','Vanessa','William']
    surnames = ['Silva','Costa','Pereira','Oliveira','Souza','Almeida','Santos','Lima','Rocha','Ferreira']
    petnames = ['Luna','Thor','Mel','Simba','Nina','Bento','Amora','Fred','Pipoca','Mia','Bob','Tom','Lola','Chico','Belinha','Max','Kiara','Zeca','Nala','Toby']
    pets = []
    for i in range(1, 401):
        first, last = names[(i-1)%len(names)], surnames[((i-1)//len(names))%len(surnames)] + f' Demo {i:03d}'
        cid = conn.execute('''INSERT INTO clients (first_name,last_name,zip_code,address,number,complement,phone,email,emergency_contact,emergency_phone,cpf,rg) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (first,last,'','Rua Fictícia da Demonstração',str(i),'Dados fictícios','',f'tutor{i:03d}@example.invalid','Contato fictício','','','')).lastrowid
        for j in range(rng.choices([1,2,3],[.62,.30,.08])[0]):
            species = rng.choices(['Canino','Felino'],[.70,.30])[0]
            breed = rng.choice(['SRD','Poodle','Shih Tzu','Labrador','Beagle'] if species=='Canino' else ['SRD','Siamês','Persa'])
            born = date(2026,1,1)-timedelta(days=rng.randint(90,4500))
            name = f'{rng.choice(petnames)} {i:03d}{chr(65+j)}'
            weight = round(rng.uniform(2,35) if species=='Canino' else rng.uniform(2,7),1)
            pid=conn.execute('''INSERT INTO patients (client_id,pet_name,gender,neutered,species,breed,birth_date,age,weight,microchip,photo_path) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (cid,name,rng.choice(['Macho','Fêmea']),rng.choice(['Sim','Não']),species,breed,born.strftime('%d/%m/%Y'),f'{(date(2026,1,1)-born).days//365} anos',weight,'','')).lastrowid
            pets.append(dict(id=pid,cid=cid,name=name,tutor=f'{first} {last}',species=species,born=born))
    conn.commit()
    last_visit, last_vax = {}, {}
    day = date(2026,1,1)
    counts = collections.Counter()
    daily = {}
    months = collections.defaultdict(lambda:collections.Counter())
    exam_dir=ROOT/'data'/'exames_demo'
    exam_dir.mkdir(parents=True,exist_ok=True)
    while day.year == 2026:
        if day.weekday()==6:
            day += timedelta(days=1)
            continue
        n=rng.randint(5,10)
        daily[day.isoformat()]=n
        slots=sorted(rng.sample(range(108),n)) # 08:00 through 16:55, five-minute grid
        chosen=set()
        for slot in slots:
            eligible=[p for p in pets if p['id'] not in chosen]
            returns=[p for p in eligible if p['id'] in last_visit and 5 <= (day-last_visit[p['id']][0]).days <= 21 and last_visit[p['id']][1]=='Consulta']
            service=rng.choices(['Consulta','Vacina','Retorno'],[.55,.28,.17])[0]
            if service=='Retorno' and not returns: service='Consulta'
            p=rng.choice(returns if service=='Retorno' else eligible)
            chosen.add(p['id'])
            time=f'{8+slot//12:02d}:{(slot%12)*5:02d}'
            aid=conn.execute('INSERT INTO appointments(date,time,client_name,pet_name,service_type) VALUES (?,?,?,?,?)',(day.isoformat(),time,p['tutor'],p['name'],service)).lastrowid
            vaccines=[]
            notes=f'DEMONSTRAÇÃO — atendimento fictício\nTipo: {service}\nHorário: {time}\nPaciente: {p["name"]}\nPeso registrado: acompanhamento de rotina.'
            if service=='Consulta':
                complaint=rng.choice(['Avaliação de rotina','Queixa dermatológica','Avaliação gastrointestinal','Avaliação odontológica','Acompanhamento de mobilidade'])
                notes+=f'\nMotivo: {complaint}\nAvaliação e conduta fictícias para testar o histórico.\nReavaliação sugerida em 7 a 14 dias.'
                price=rng.choice([100,120,150,180,200])
            elif service=='Retorno':
                prior=last_visit[p['id']][0]
                notes+=f'\nRetorno da consulta de {prior.strftime("%d/%m/%Y")}.\nEvolução fictícia: melhora do quadro. Registro de acompanhamento.'
                price=rng.choice([0,0,40,60])
            else:
                candidates=['V8','V10','Antirrábica','Giárdia','Gripe Canina'] if p['species']=='Canino' else ['V4','V5','Antirrábica','FeLV']
                candidates=[v for v in candidates if (p['id'],v) not in last_vax or (day-last_vax[p['id'],v]).days>=330]
                if not candidates:
                    service='Consulta'
                    conn.execute('UPDATE appointments SET service_type=? WHERE id=?',(service,aid))
                    notes=notes.replace('Tipo: Vacina','Tipo: Consulta')+'\nAvaliação de rotina: vacinação já registrada no período.'
                    price=120
                else:
                    vaccines=[rng.choice(candidates)]
                    if rng.random()<.18 and vaccines[0]!='Antirrábica' and 'Antirrábica' in candidates: vaccines.append('Antirrábica')
                    notes+='\n• Vacinas Aplicadas: '+', '.join(vaccines)
                    price=sum({'V8':85,'V10':110,'V4':95,'V5':120,'Antirrábica':55,'Giárdia':95,'Gripe Canina':100,'FeLV':130}[v] for v in vaccines)
            method=rng.choices(['PIX','Dinheiro','Crédito parcelado','Débito'],[.48,.18,.20,.14])[0]
            status='Pendente' if price and rng.random()<.07 else 'Pago'
            installments=rng.choice([1,2,3]) if method=='Crédito parcelado' else 1
            payments=[(method,price,installments,status)] if price else []
            if price and status=='Pago' and rng.random()<.12:
                payments=[('PIX',round(price*.5,2),1,'Pago'),('Dinheiro',round(price*.5,2),1,'Pago')]
            conn.commit()
            hid=db.save_consultation_with_stock(None,p['id'],p['cid'],day.isoformat(),notes,vaccines,payments)
            conn.execute('UPDATE consultation_history SET appointment_id=? WHERE id=?',(aid,hid))
            for v in vaccines:
                last_vax[p['id'],v]=day
                # Calculate vaccine dates from the simulated attendance, not the system clock.
                due=day.replace(year=2027)
                if (day-p['born']).days<365 and v!='Antirrábica': due=day+timedelta(days=21)
                conn.execute('UPDATE pet_vaccines SET next_due_date=? WHERE id=(SELECT vaccine_record_id FROM consultation_vaccine_stock WHERE consultation_id=? AND code=?)',(due.isoformat(),hid,v))
            if service=='Consulta' and rng.random()<.20:
                exam=rng.choice(['Hemograma','Bioquímica','Urina','Ultrassonografia'])
                filename=f'{exam}_{hid:05d}.txt'
                rel='data/exames_demo/'+filename
                (exam_dir/filename).write_text(f'DADOS FICTÍCIOS — SEM VALOR CLÍNICO\nExame: {exam}\nPaciente: {p["name"]}\nData: {day.strftime("%d/%m/%Y")}\nResultado ilustrativo: registro de avaliação simulada, sem valores clínicos reais.\n',encoding='utf-8')
                conn.execute('INSERT INTO pet_exams(pet_id,file_name,file_path) VALUES (?,?,?)',(p['id'],filename,rel))
                counts['exames']+=1
            last_visit[p['id']]=(day,service)
            counts[service]+=1
            counts['doses']+=len(vaccines)
            months[day.strftime('%Y-%m')][service]+=1
            conn.commit()
        day+=timedelta(days=1)
    for i,code in enumerate(VACCINES):
        conn.execute('UPDATE inventory_vaccines SET quantity=?,expiry_date=?,unit_cost=? WHERE code=?',
            (rng.randint(8,90),['2026-10-25','2026-11-15','2026-12-10','2027-02-20'][i%4],{'V8':40,'V10':55,'V4':45,'V5':60,'Antirrábica':20,'Giárdia':48,'Gripe Canina':50,'FeLV':65}[code],code))
    conn.commit()
    assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    assert all(5<=n<=10 and date.fromisoformat(d).weekday()!=6 for d,n in daily.items())
    assert conn.execute("SELECT COUNT(*) FROM appointments WHERE time<'08:00' OR time>'17:00'").fetchone()[0]==0
    assert conn.execute('SELECT COUNT(*) FROM consultation_history').fetchone()[0]==sum(daily.values())
    assert conn.execute('SELECT COUNT(*) FROM pet_vaccines').fetchone()[0]==counts['doses']
    assert conn.execute('SELECT COUNT(*) FROM consultation_history ch JOIN patients p ON p.id=ch.pet_id WHERE ch.client_id!=p.client_id').fetchone()[0]==0
    summary={'ano':2026,'tutores':400,'pets':len(pets),'dias':len(daily),'atendimentos':sum(daily.values()),'media_diaria':round(sum(daily.values())/len(daily),2),'tipos':dict(counts),'mensal':{k:dict(v) for k,v in months.items()},'pagamentos_pendentes':conn.execute("SELECT COUNT(*) FROM consultation_payments WHERE status='Pendente'").fetchone()[0]}
    (ROOT/'resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    db.close()
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': generate()
