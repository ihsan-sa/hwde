# Layout op generator for pd-trigger-lite-dip (placement, hand route, silk). Run from the repo root.
# Input /tmp/lite_tracks.txt = pd-trigger-lite tracks/vias dumped with pcbnew (TRK/VIA lines).
import json,sys
OX,OY=17.69,25.817
WS='boards/pd-trigger-lite-dip'
def A(x,y): return [round(OX+x,3),round(OY+y,3)]
# lite abs -> new local: (x-18.47, y-27.7925+6)
def L(x,y): return (x-18.47, y-27.7925+6)
P=[("J1",4.55,13.5,270),("J2",22.8,12.3,0),("U1",12.6,18.35,90),("R7",17.4,16.55,270),
("C1",17.4,19.3,270),("R6",19.8,17.3,0),("D1",22.6,17.3,180),("SW1",16.5,6.0,90),
("R4",22.9,2.4,180),("R3",22.9,4.2,180),("R2",22.9,6.0,180),("R1",22.9,7.8,180),("R5",22.9,9.6,180)]
place=[{"op":"place","ref":r,"x":A(x,y)[0],"y":A(x,y)[1],"deg":d,"side":"front"} for r,x,y,d in P]
json.dump({"version":1,"ops":place},open(f'{WS}/reports/place_p6.ops.json','w'),indent=1)
ops=[]
def T(net,layer,pts,w=0.25):
    for a,b in zip(pts,pts[1:]):
        ops.append({"op":"add_track","start":A(*a),"end":A(*b),"width":w,"layer":layer,"net":net})
def V(net,p): ops.append({"op":"add_via","at":A(*p),"size":0.6,"drill":0.3,"net":net})
# --- reused from lite (translated)
lite=[l.split() for l in open('/tmp/lite_tracks.txt')]
for l in lite:
    net=l[1]
    if l[0]=='TRK':
        if net in('/CFG1',) or net.startswith('/SEL'): continue
        ly,x1,y1,x2,y2,w=l[2],*map(float,l[3:])
        if net=='GND' and y1<33.5 and x1>25: continue   # old grid GND
        if net=='GND' and abs(x1-41.82)<0.01: x2=x2  # D1 GND
        a,b=L(x1,y1),L(x2,y2)
        if net=='GND' and abs(x1-41.82)<.01: pass
        T(net,ly,[a,b],w)
    elif l[0]=='VIA':
        x,y=float(l[2]),float(l[3])
        if net=='/CFG1' or (net=='GND' and y<33.5): continue
        if net=='GND' and abs(x-31.07)<.01: continue   # EP vias: planes_gen adds
        V(net,L(x,y))
# --- CFG1: switch common column -> via -> B.Cu -> U1 pin 9
cx=16.5-3.81
T("/CFG1","F.Cu",[(cx,3.46),(cx,10.3)])
V("/CFG1",(cx,10.3))
T("/CFG1","B.Cu",[(cx,10.3),(10.6,12.39),(10.6,17.8),(9.05,19.35),(8.2,19.35)])
V("/CFG1",(8.2,19.35))
T("/CFG1","F.Cu",[(8.2,19.35),(9.6,19.35)])
# --- SEL fan-out: switch pad k (x 20.31) -> resistor inner pad (x 22.15)
sx,rx=16.5+3.81,22.15
for net,ys,yr in [("/SEL20",3.46,2.4),("/SEL15",4.73,4.2),("/SEL12",6.0,6.0),("/SEL9",7.27,7.8),("/SEL5",8.54,9.6)]:
    d=abs(yr-ys)
    T(net,"F.Cu",[(sx,ys),(rx-d,ys),(rx,yr)] if d>0 else [(sx,ys),(rx,yr)])
# --- GND on the Rset outer pads
T("GND","F.Cu",[(23.65,2.4),(23.65,7.8)])
V("GND",(23.65,3.3)); V("GND",(23.65,6.9))
# --- VHV to R5 (5 V pull-up): pad -> via -> B.Cu down the right edge -> via by R6
T("/VHV","F.Cu",[(23.65,9.6),(24.3,10.25)],0.2)
V("/VHV",(24.3,10.25))
T("/VHV","B.Cu",[(24.3,10.25),(24.3,16.433),(18.5,16.433)],0.2)
V("/VHV",(18.5,16.433))
T("/VHV","F.Cu",[(18.5,16.433),(19.05,17.3)],0.2)
json.dump({"ops":ops},open(f'{WS}/reports/route_edit_manual.json','w'),indent=1)
# --- silk
s=[{"op":"silk_clear","ref":r,"layer":"F.SilkS"} for r in ("R1","R2","R3","R4","R5","R6","R7","C1")]
s.append({"op":"silk_clear","ref":"J1","layer":"F.SilkS","only_offboard":True})
def TX(t,x,y,size=0.8,th=0.15): s.append({"op":"add_text","text":t,"x":A(x,y)[0],"y":A(x,y)[1],"layer":"F.SilkS","size":size,"thickness":th})
for t,y in [("20",3.46),("15",4.73),("12",6.0),("9",7.27),("5",8.54)]: TX(t,11.0,y)
TX("V",11.0,9.75)
TX("<ON",13.3,0.95)
TX("+",21.0,12.3,1.0,0.2); TX("-",21.0,14.84,1.0,0.2)
TX("PD DIP",4.2,19.7)
json.dump({"version":1,"ops":s},open(f'{WS}/kicad/silk_ops.json','w'),indent=1)
# constraints plane region
c=json.load(open(f'{WS}/kicad/constraints.json'))
for p in c['planes']:
    if p['net']=='VBUS': p['region']=A(5.9,11.3)+A(24.7,15.7)
c['_comment']=c['_comment'].replace('pd-trigger-lite P2','pd-trigger-lite-dip (from lite P2)')
json.dump(c,open(f'{WS}/kicad/constraints.json','w'),indent=1)
json.dump(c,open(f'{WS}/architecture/constraints.json','w'),indent=1)
print(len(place),len(ops),len(s))
