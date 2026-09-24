"""Answer key for T3, computed from the figures in report.md (not typed by hand)."""
from decimal import Decimal as D, ROUND_HALF_UP
import json
frozen=[4820,5130,5960,5210]; bev=[3410,3980,3150,2870]; biz=[2240,2310,2905,2760]
moved=[380,415,452,430]  # Q1,Q2 still inside 飲料; Q3,Q4 already inside 業務用
usd=[10200,11050,12400,13100]; fx=[145,148,152,150]
op_frozen=[412,445,538,401]  # errata applied (table says 468 for Q2)
op_bev=[198,260,171,122]; op_biz=[150,139,204,188]; op_os=612
corp=[95,95,95,125]
def r1(x): return str(D(x).quantize(D("0.1"),ROUND_HALF_UP))
os_yen=[D(u)*f/1000 for u,f in zip(usd,fx)]
bev_new=[bev[0]-moved[0],bev[1]-moved[1],bev[2],bev[3]]
biz_new=[biz[0]+moved[0],biz[1]+moved[1],biz[2],biz[3]]
total=sum(frozen)+sum(bev)+sum(biz)+sum(os_yen)
dom_op=sum(op_frozen)+sum(op_bev)+sum(op_biz)
margins=[D(o)/D(s) for o,s in zip(op_frozen,frozen)]
key={
 "q01":str(sum(frozen)),"q02":str(sum(op_frozen)),"q03":str(biz_new[1]),"q04":str(sum(bev_new)),
 "q05":r1(os_yen[2]),"q06":r1(total),"q07":str(dom_op),"q08":str(dom_op+op_os-sum(corp)),
 "q09":r1((D(sum(frozen))/D(19800)-1)*100),"q10":"Q%d"%(margins.index(max(margins))+1),
 "q11":str(420+1150+980+312),"q12":r1(total/D(50000)*100),"q13":"記載なし","q14":"30",
 "q15":str(bev[2]+moved[2]),"q16":str(biz_new[2]-biz_new[0]),
}
# traps: what a reader gets if they miss the catch
traps={"q02":str(412+468+538+401),"q03":str(biz[1]),"q04":str(sum(bev)),"q10":"Q2","q11":str(420+1150+980),
       "q15":str(bev[2]),"q16":str(biz[2]-biz[0]),"q08":str(dom_op+op_os-95*4)}
if __name__=="__main__":
    json.dump({"key":key,"traps":traps},open(__file__.replace(".py",".json"),"w"),ensure_ascii=False,indent=1)
    print(json.dumps(key,ensure_ascii=False)); print(traps)
