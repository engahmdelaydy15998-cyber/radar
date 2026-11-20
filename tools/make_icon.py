from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
import math, random
S=3; N=512*S; C=N//2
random.seed(7)
def lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
INTER="/usr/share/fonts/opentype/inter/Inter-Bold.otf"
def layer(): return Image.new("RGBA",(N,N),(0,0,0,0))
def over(base,top): base.alpha_composite(top)
def build(name, pal):
    bg=(5,5,9)
    base=Image.new("RGBA",(N,N),bg+(255,))
    # violet depth glow
    gl=layer(); gd=ImageDraw.Draw(gl)
    for i in range(50,0,-1):
        r=N*0.50*i/50; a=int(150*((1-i/50)**1.7)); gd.ellipse([C-r,C-r,C+r,C+r],fill=pal['glow']+(a,))
    over(base,gl.filter(ImageFilter.GaussianBlur(6*S)))
    # bokeh for depth
    bk=layer(); bd=ImageDraw.Draw(bk)
    for _ in range(9):
        a=random.uniform(0,2*math.pi); rr=random.uniform(0.30,0.47)*N; r=random.uniform(0.012,0.03)*N
        x=C+math.cos(a)*rr; y=C+math.sin(a)*rr; bd.ellipse([x-r,y-r,x+r,y+r],fill=pal['bokeh']+(random.randint(25,55),))
    over(base,bk.filter(ImageFilter.GaussianBlur(5*S)))
    # streak
    st=layer(); sd=ImageDraw.Draw(st)
    for k in range(12):
        h=int(N*0.006*(12-k)/12*3)+1; sd.rectangle([N*0.24,C-h,N*0.76,C+h],fill=pal['streak']+(int(10+k*6),))
    over(base,st.filter(ImageFilter.GaussianBlur(9*S)))
    # radar plate (screen disc with bezel)
    pl=layer(); pd=ImageDraw.Draw(pl); PR=N*0.445
    for i in range(40,0,-1):
        r=PR*i/40; pd.ellipse([C-r,C-r,C+r,C+r],fill=lerp(pal['plate'][0],pal['plate'][1],i/40)+(int(235*min(1,0.5+i/80)),))
    over(base,pl)
    # rings: depth of field (outer rings softer and dimmer)
    for i,r in enumerate([0.20,0.25,0.30,0.35,0.40]):
        rl=layer(); rd=ImageDraw.Draw(rl); R=N*r
        a=int(240-i*18)
        rd.ellipse([C-R,C-R,C+R,C+R],outline=pal['ring']+(a,),width=int((3.4-i*0.25)*S))
        over(base,rl.filter(ImageFilter.GaussianBlur(i*0.4*S)) if i else rl)
    # spokes, bezel ticks
    tk=layer(); td=ImageDraw.Draw(tk)
    for deg in range(0,360,30):
        a=math.radians(deg); td.line([(C+math.cos(a)*N*0.20,C-math.sin(a)*N*0.20),(C+math.cos(a)*N*0.40,C-math.sin(a)*N*0.40)],fill=pal['ring']+(46,),width=int(1.4*S))
    for deg in range(0,360,3):
        a=math.radians(deg); L=0.022 if deg%15==0 else 0.011
        td.line([(C+math.cos(a)*N*(0.445-L),C-math.sin(a)*N*(0.445-L)),(C+math.cos(a)*N*0.445,C-math.sin(a)*N*0.445)],fill=pal['ring']+(150 if deg%15==0 else 85,),width=int(1.4*S))
    td.ellipse([C-N*0.445,C-N*0.445,C+N*0.445,C+N*0.445],outline=pal['ring']+(170,),width=int(2.2*S))
    # HUD band like the reference: segmented outer ring, heavy dashes, thick bright arc, finer grid
    hd=layer(); hdd=ImageDraw.Draw(hd)
    for deg in range(0,360,4):
        a=math.radians(deg); heavy=(deg//12)%3==0
        r0=N*0.462; r1=N*(0.488 if heavy else 0.474)
        hdd.line([(C+math.cos(a)*r0,C-math.sin(a)*r0),(C+math.cos(a)*r1,C-math.sin(a)*r1)],fill=pal['ring']+(200 if heavy else 95,),width=int((2.6 if heavy else 1.4)*S))
    hdd.arc([C-N*0.452,C-N*0.452,C+N*0.452,C+N*0.452],70,190,fill=pal['ring']+(235,),width=int(5.5*S))
    hdd.ellipse([C-N*0.455,C-N*0.455,C+N*0.455,C+N*0.455],outline=pal['ring']+(80,),width=int(1.2*S))
    for r in (0.225,0.275,0.325,0.375):
        hdd.ellipse([C-N*r,C-N*r,C+N*r,C+N*r],outline=pal['ring']+(34,),width=int(1.0*S))
    for deg in range(15,360,30):
        a=math.radians(deg); hdd.line([(C+math.cos(a)*N*0.20,C-math.sin(a)*N*0.20),(C+math.cos(a)*N*0.40,C-math.sin(a)*N*0.40)],fill=pal['ring']+(22,),width=int(1.0*S))
    over(base,hd.filter(ImageFilter.GaussianBlur(0.4*S)))
    over(base,tk)
    # sweep: bright leading edge, fading tail (clockwise rotation, lead at LEAD deg)
    LEAD=300; TAIL=150
    sw=layer(); sd_=ImageDraw.Draw(sw)
    steps=115
    for i in range(steps):
        a0=LEAD+i*(TAIL/steps); al=int(150*(1-i/steps)**1.8)
        sd_.pieslice([C-N*0.445,C-N*0.445,C+N*0.445,C+N*0.445],(-(a0+TAIL/steps*1.4))%360,(-a0)%360,fill=pal['sweep']+(al,))
    over(base,sw)
    ed=layer(); edd=ImageDraw.Draw(ed); a=math.radians(LEAD)
    edd.line([(C,C),(C+math.cos(a)*N*0.445,C-math.sin(a)*N*0.445)],fill=pal['sweep']+(255,),width=int(3.2*S))
    over(base,ed.filter(ImageFilter.GaussianBlur(2.5*S))); over(base,ed)
    # lettering: extruded 3D, violet -> pink gradient
    LS=AI_SCALE; w=int(N*0.046*LS)
    mask=Image.new("L",(N,N),0); md=ImageDraw.Draw(mask)
    def stroke(p,q):
        md.line([(C+p[0]*N*LS,C+p[1]*N*LS),(C+q[0]*N*LS,C+q[1]*N*LS)],fill=255,width=w)
        for pt in (p,q):
            x=C+pt[0]*N*LS; y=C+pt[1]*N*LS; md.ellipse([x-w/2,y-w/2,x+w/2,y+w/2],fill=255)
    top,bot=-0.095,0.105
    stroke((-0.155,bot),(-0.075,top)); stroke((-0.075,top),(0.005,bot)); stroke((-0.118,0.04),(-0.032,0.04)); stroke((0.085,top),(0.085,bot))
    def spark(m_d,cx,cy,r):
        pts=[]
        for i in range(8):
            a=math.pi/4*i; rr=r if i%2==0 else r*0.26
            pts.append((cx+math.cos(a-math.pi/2)*rr,cy+math.sin(a-math.pi/2)*rr))
        m_d.polygon(pts,fill=255)
    spark(md,C+0.150*N*LS,C-0.115*N*LS,0.042*N*LS*1.2)
    if MAGIC:
        spark(md,C-0.205*N*LS,C-0.105*N*LS,0.022*N*LS)
        spark(md,C+0.185*N*LS,C+0.085*N*LS,0.018*N*LS)
    # shadow
    sh=Image.new("RGBA",(N,N),(0,0,0,0)); sh.paste((0,0,0,200),(0,0),mask.filter(ImageFilter.GaussianBlur(10*S)))
    sh=ImageChops.offset(sh,int(6*S),int(14*S)); over(base,sh)
    # glow
    gl2=Image.new("RGBA",(N,N),(0,0,0,0)); gl2.paste(pal['lglow']+(150,),(0,0),mask.filter(ImageFilter.GaussianBlur(14*S))); over(base,gl2)
    if MAGIC:
        # soft halo behind the letters so AI reads first at home-screen size
        hl=layer(); hd_=ImageDraw.Draw(hl); HR=N*0.17*LS/0.66
        for i in range(30,0,-1):
            r=HR*i/30; hd_.ellipse([C-r,C-r,C+r,C+r],fill=pal['lglow']+(int(70*(1-i/30)**1.4),))
        over(base,hl.filter(ImageFilter.GaussianBlur(8*S)))
        gl3=Image.new("RGBA",(N,N),(0,0,0,0)); gl3.paste(pal['lglow']+(110,),(0,0),mask.filter(ImageFilter.GaussianBlur(30*S))); over(base,gl3)
    # extrusion
    ext=Image.new("RGBA",(N,N),(0,0,0,0))
    for d in range(10,0,-1):
        m2=ImageChops.offset(mask,int(d*0.35*S),int(d*0.75*S))
        ext.paste(lerp((70,30,110),(150,60,130),1-d/10)+(255,),(0,0),m2)
    over(base,ext)
    # face gradient
    gr=Image.new("RGB",(N,N)); gp=ImageDraw.Draw(gr)
    y0=C+top*N*LS; y1=C+bot*N*LS
    for y in range(N):
        t=min(1,max(0,(y-y0)/(y1-y0))); gp.line([(0,y),(N,y)],fill=lerp(pal['grad'][0],pal['grad'][1],t))
    # faint world-map dots, only shows up where it falls inside the letters
    bx0,by0=C-0.21*N*LS,C-0.14*N*LS; bw,bh=0.42*N*LS,0.28*N*LS
    land=[(0.04,0.50),(0.10,0.36),(0.16,0.26),(0.22,0.20),(0.27,0.18),(0.31,0.28),(0.34,0.42),(0.37,0.58),(0.40,0.72),
          (0.50,0.26),(0.55,0.40),(0.58,0.55),(0.61,0.68),
          (0.60,0.20),(0.66,0.14),(0.72,0.16),(0.80,0.22),(0.87,0.30),(0.93,0.40)]
    rdot=bw*0.032
    for fx,fy in land:
        x=bx0+fx*bw; y=by0+fy*bh
        gp.ellipse([x-rdot,y-rdot,x+rdot,y+rdot],fill=lerp(pal['grad'][0],(8,5,18),0.42))
    face=Image.new("RGBA",(N,N),(0,0,0,0)); face.paste(gr,(0,0),mask); over(base,face)
    import numpy as np
    def pos(a,rr): a=math.radians(a); return C+math.cos(a)*N*rr, C-math.sin(a)*N*rr
    def lit_tile(R,col,cx,cy):
        size=int(2*R)+2
        yy,xx=np.mgrid[0:size,0:size].astype(float)
        vx,vy=C-cx,C-cy; L=math.hypot(vx,vy) or 1; vx/=L; vy/=L
        t=np.clip(((xx-size/2)*vx+(yy-size/2)*vy)/size+0.5,0,1)[...,None]
        lo=np.array(lerp(col,(14,10,30),0.60)); hi=np.array(lerp(col,(255,255,255),0.12))
        return Image.fromarray((lo*(1-t)+hi*t).astype("uint8"),"RGB").convert("RGBA")
    def lit_amount(a):
        d=(a-LEAD)%360
        return 1.0 if d<=TAIL else 0.0
    def echo(cx,cy,R,col,ring_r,ang,lit):
        el=layer(); ed2=ImageDraw.Draw(el)
        for m,al in ((1.7,90),(2.5,48),(3.4,22)):
            r=R*m; ed2.ellipse([cx-r,cy-r,cx+r,cy+r],outline=col+(int(al*(0.45+0.55*lit)),),width=max(1,int(S*1.1)))
        over(base,el.filter(ImageFilter.GaussianBlur(0.6*S)))
        gl=layer(); gd=ImageDraw.Draw(gl); gd.ellipse([cx-R*2.6,cy-R*2.6,cx+R*2.6,cy+R*2.6],fill=col+(int(40+80*lit),))
        over(base,gl.filter(ImageFilter.GaussianBlur(R*0.9)))
    def blip(a,ring,rad,col,draw_glyph,solid=None,far=0):
        cx,cy=pos(a,ring); R=N*rad; lit=lit_amount(a); cc=solid or col
        if MAGIC:
            # dark gap around the badge so ring lines stop short of it instead of cutting through
            kn=layer(); ImageDraw.Draw(kn).ellipse([cx-R*1.45,cy-R*1.45,cx+R*1.45,cy+R*1.45],fill=pal['plate'][0]+(235,))
            over(base,kn.filter(ImageFilter.GaussianBlur(R*0.18)))
        echo(cx,cy,R,cc,ring,a,lit)
        sh=layer(); ImageDraw.Draw(sh).ellipse([cx-R,cy-R+R*0.14,cx+R,cy+R+R*0.14],fill=(0,0,0,170)); over(base,sh.filter(ImageFilter.GaussianBlur(R*0.2)))
        tile=lit_tile(R,cc,cx,cy); size=tile.size[0]
        m=Image.new("L",(size,size),0); ImageDraw.Draw(m).ellipse([0,0,size-1,size-1],fill=255)
        t=layer(); t.paste(tile,(int(cx-size/2),int(cy-size/2)),m)
        rim=layer(); ImageDraw.Draw(rim).ellipse([cx-R,cy-R,cx+R,cy+R],outline=cc+(int(150+90*lit),),width=max(2,int(S*1.8)))
        if far: t=t.filter(ImageFilter.GaussianBlur(far)); rim=rim.filter(ImageFilter.GaussianBlur(far))
        over(base,t); over(base,rim)
        draw_glyph(cx,cy,R,0 if MAGIC else far)
        if not lit and not MAGIC:
            dm=layer(); ImageDraw.Draw(dm).ellipse([cx-R*1.1,cy-R*1.1,cx+R*1.1,cy+R*1.1],fill=(6,5,14,60)); over(base,dm.filter(ImageFilter.GaussianBlur(R*0.15)))
    def txt(label,k,col):
        def fn(cx,cy,R,far):
            ff=ImageFont.truetype(INTER,int(R*k)); tl=layer(); td=ImageDraw.Draw(tl); tb=td.textbbox((0,0),label,font=ff)
            xy=(cx-(tb[2]-tb[0])/2-tb[0],cy-(tb[3]-tb[1])/2-tb[1])
            if MAGIC:
                sh_=layer(); ImageDraw.Draw(sh_).text((xy[0],xy[1]+S*1.5),label,font=ff,fill=(0,0,0,200)); over(base,sh_.filter(ImageFilter.GaussianBlur(S*1.2)))
            td.text(xy,label,font=ff,fill=((255,255,255) if MAGIC else col)+(255,))
            over(base,tl.filter(ImageFilter.GaussianBlur(far)) if far else tl)
        return fn
    def sparkg(col):
        def fn(cx,cy,R,far):
            tl=layer(); td=ImageDraw.Draw(tl); pts=[]
            for i in range(8):
                a=math.pi/4*i; rr=R*0.62 if i%2==0 else R*0.15
                pts.append((cx+math.cos(a-math.pi/2)*rr,cy+math.sin(a-math.pi/2)*rr))
            td.polygon(pts,fill=col+(255,)); over(base,tl.filter(ImageFilter.GaussianBlur(far)) if far else tl)
        return fn
    def rssg(col):
        def fn(cx,cy,R,far):
            k=R*0.5; lw=max(2,int(R*0.14)); ox,oy=cx-k*0.95,cy+k*0.95
            tl=layer(); td=ImageDraw.Draw(tl); td.ellipse([ox-lw*0.8,oy-lw*0.8,ox+lw*0.8,oy+lw*0.8],fill=col+(255,))
            for rr in (k*1.0,k*1.9): td.arc([ox-rr,oy-rr,ox+rr,oy+rr],-90,0,fill=col+(255,),width=lw)
            over(base,tl.filter(ImageFilter.GaussianBlur(far)) if far else tl)
        return fn
    W=lambda c:lerp(c,(255,255,255),0.82)
    cc=pal['c']
    R40=0.35 if MAGIC else 0.40
    blip(122,0.35,0.046,cc[0],txt("C#",1.3,W(cc[0])))
    blip(150,R40,0.040,cc[1],txt("{ }",1.0,W(cc[1])))
    blip(178,0.30,0.034,cc[2],txt("Py",1.0,W(cc[2])),far=0.4*S)
    blip(204,0.35,0.030,cc[3],txt("JS",1.0,W(cc[3])),far=0.7*S)
    blip(229,0.30,0.026,cc[4],txt(">_",1.0,W(cc[4])),far=0.9*S)
    blip(255,R40,0.030,cc[5],sparkg(W(cc[5])),far=0.7*S)
    blip(288,0.35,0.028,cc[6],rssg(W(cc[6])),far=0.8*S)
    def playg(cx,cy,R,far):
        tl=layer(); td=ImageDraw.Draw(tl); k=R*0.5
        td.polygon([(cx-k*0.55,cy-k),(cx-k*0.55,cy+k),(cx+k,cy)],fill=(255,255,255,255)); over(base,tl)
    blip(318,0.35,0.050,(236,52,52),playg,solid=(236,52,52))
    # mud-brick dome + two vaults + arched doors (Hassan Fathy spirit), drawn as a mask; u = drawing unit
    def dome_mask(sz,u,ox,oy):
        G=Image.new("L",(sz,sz),0); gd_=ImageDraw.Draw(G)
        def Q(p): return (ox+p[0]*u, oy+p[1]*u)
        def domeP(cx,by,rx,ry):
            return [Q((cx+rx*math.cos(math.pi*k/40),by-ry*math.sin(math.pi*k/40))) for k in range(41)]
        gd_.polygon(domeP(0,0.60,0.62,0.86),fill=255)
        gd_.rectangle([*Q((-0.80,0.60)),*Q((0.80,0.90))],fill=255)
        gd_.polygon(domeP(-1.32,0.72,0.38,0.46),fill=255); gd_.rectangle([*Q((-1.70,0.72)),*Q((-0.94,0.90))],fill=255)
        gd_.polygon(domeP(1.32,0.72,0.38,0.38),fill=255);  gd_.rectangle([*Q((0.94,0.72)),*Q((1.70,0.90))],fill=255)
        def cut(cx,top,w_,bot):
            gd_.rectangle([*Q((cx-w_,top+w_)),*Q((cx+w_,bot))],fill=0)
            gd_.polygon([Q((cx+w_*math.cos(math.pi*k/30),top+w_-w_*math.sin(math.pi*k/30))) for k in range(31)],fill=0)
        cut(0,0.50,0.15,0.90); cut(-1.32,0.74,0.07,0.90); cut(1.32,0.74,0.07,0.90)
        return G
    archcol=pal['wall'][1]
    if ARCH_MARK=="arc":
        blip(54,0.325,0.038,archcol,txt("ARC",0.85,W(archcol)))
    elif ARCH_MARK=="domebadge":
        def domeg(col):
            def fn(cx,cy,R,far):
                sz=int(R*2)+2; u=R*0.55
                G=dome_mask(sz,u,sz/2,sz/2-0.32*u).filter(ImageFilter.GaussianBlur(0.5*S))
                tl=layer(); tl.paste(col+(255,),(int(cx-sz/2),int(cy-sz/2)),G); over(base,tl)
            return fn
        bc=lerp(archcol,(0,0,0),0.35); blip(60,0.36,0.050,bc,domeg(W(archcol)))
    else:
        ax,ay=pos(60,0.36); AW=N*0.088
        echo(ax,ay,AW*0.30,pal['arch_echo'],0.36,60,0.4)
        gl=layer(); ImageDraw.Draw(gl).ellipse([ax-AW*1.0,ay-AW*0.9,ax+AW*1.0,ay+AW*0.9],fill=pal['arch_echo']+(34,))
        over(base,gl.filter(ImageFilter.GaussianBlur(AW*0.35)))
        sz=int(AW*2.6); u=AW*0.62; ox,oy=sz/2,sz/2+0.15*u
        G=dome_mask(sz,u,ox,oy)
        fade=Image.new("L",(sz,sz)); fp=ImageDraw.Draw(fade)
        for y in range(sz):
            t=(y-(oy-0.9*u))/(1.8*u); fp.line([(0,y),(sz,y)],fill=int(255*max(0.85,min(1,1.5-t*0.6))))
        G=ImageChops.multiply(G,fade).filter(ImageFilter.GaussianBlur(0.7*S))
        col=Image.new("RGB",(sz,sz)); cp_=ImageDraw.Draw(col)
        for x in range(sz): cp_.line([(x,0),(x,sz)],fill=lerp(pal['wall'][0],pal['wall'][1],x/sz))
        sh2=layer(); sh2.paste((0,0,0,170),(int(ax-sz/2),int(ay-sz/2)+int(S*4)),G.filter(ImageFilter.GaussianBlur(5*S))); over(base,sh2)
        t=layer(); t.paste(col.convert("RGBA"),(int(ax-sz/2),int(ay-sz/2)),G); over(base,t)
    # MEP (mechanical/electrical/plumbing): same text-badge language as the code marks
    if not MAGIC:
        blip(14,0.40,0.030,pal['mep'],txt("MEP",0.95,W(pal['mep'])),far=0.5*S)
    else:
        def gearg(col):
            def fn(cx,cy,R,far):
                tl=layer(); td=ImageDraw.Draw(tl); ro,ri,n=R*0.62,R*0.46,8; pts=[]
                for i in range(n*4):
                    a=2*math.pi*i/(n*4); rr=ro if (i%4) in (0,1) else ri
                    pts.append((cx+math.cos(a)*rr,cy+math.sin(a)*rr))
                td.polygon(pts,fill=col+(255,)); h=R*0.20
                over(base,tl.filter(ImageFilter.GaussianBlur(far)) if far else tl)
                dot=layer(); ImageDraw.Draw(dot).ellipse([cx-h,cy-h,cx+h,cy+h],fill=lerp(col,(10,20,14),0.7)+(255,)); over(base,dot)
            return fn
        def beamg(col):
            def fn(cx,cy,R,far):
                tl=layer(); td=ImageDraw.Draw(tl); w,h,t=R*1.0,R*1.05,R*0.22
                td.rectangle([cx-w/2,cy-h/2,cx+w/2,cy-h/2+t],fill=col+(255,))
                td.rectangle([cx-w/2,cy+h/2-t,cx+w/2,cy+h/2],fill=col+(255,))
                td.rectangle([cx-t/2,cy-h/2,cx+t/2,cy+h/2],fill=col+(255,))
                over(base,tl.filter(ImageFilter.GaussianBlur(far)) if far else tl)
            return fn
        mc=lerp(pal['mep'],(0,0,0),0.25)
        blip(14,0.35,0.032,mc,gearg(W(pal['mep'])),far=0.4*S)
        blip(90,0.35,0.030,mc,beamg(W(pal['mep'])),far=0.4*S)
    out=base.convert("RGB").resize((512,512),Image.LANCZOS)
    # vignette
    v=Image.new("L",(512,512),0); vd=ImageDraw.Draw(v)
    for i in range(30):
        r=256*(1.25-i/30*0.55); vd.ellipse([256-r,256-r,256+r,256+r],fill=int(255*(i/30)**0.8))
    dark=Image.new("RGB",(512,512),(0,0,0)); out=Image.composite(out,dark,v.filter(ImageFilter.GaussianBlur(20)).point(lambda p:min(255,int(p*0.9)+110)))
    out.save(name); return out
PV={'glow': (120, 80, 210), 'bokeh': (170, 130, 255), 'ring': (176, 140, 255), 'streak': (255, 130, 170), 'grad': ((232, 222, 255), (255, 120, 175)), 'lglow': (255, 110, 170), 'plate': ((6, 5, 14), (26, 16, 52)), 'sweep': (190, 150, 255), 'c': [(140, 165, 255), (165, 150, 255), (190, 160, 255), (215, 185, 255), (200, 160, 255), (255, 150, 200), (225, 150, 255)], 'arch_echo': (214, 196, 255), 'sky': ((34, 26, 84), (118, 92, 200)), 'plaza': (186, 172, 238), 'wall': ((250, 244, 255), (176, 160, 226)), 'course': (196, 184, 238), 'door': (30, 24, 70), 'arch_rim': (235, 225, 255), 'mep': (120, 190, 200)}
PG={'glow': (20, 110, 60), 'bokeh': (70, 200, 120), 'ring': (90, 235, 130), 'streak': (80, 255, 150), 'grad': ((226, 255, 232), (80, 235, 130)), 'lglow': (60, 220, 110), 'plate': ((2, 10, 6), (10, 44, 22)), 'sweep': (110, 255, 150), 'c': [(80, 230, 140), (110, 235, 120), (60, 210, 150), (150, 240, 130), (90, 225, 170), (190, 255, 160), (120, 240, 190)], 'arch_echo': (150, 255, 180), 'sky': ((6, 40, 22), (30, 110, 60)), 'plaza': (70, 160, 95), 'wall': ((236, 255, 238), (130, 200, 150)), 'course': (150, 205, 165), 'door': (6, 40, 22), 'arch_rim': (190, 255, 205), 'mep': (205, 190, 90)}
import os
ARCH_MARK=os.environ.get("ARCH_MARK","dome")
AI_SCALE=float(os.environ.get("AI_SCALE","0.66"))
MAGIC=os.environ.get("MAGIC")=="1"
a=build("v14_violet.png",PV)
b=build("v14_green.png",PG)
def maskable(im,name):
    bgc=im.getpixel((6,6)); canvas=Image.new("RGB",(512,512),(5,5,9)); k=0.92
    r=im.resize((int(512*k),int(512*k)),Image.LANCZOS); canvas.paste(r,((512-r.width)//2,(512-r.height)//2)); canvas.save(name)
maskable(a,"v14_violet_maskable.png")
maskable(b,"v14_green_maskable.png")
sheet=Image.new("RGB",(512*2+60,512+40),(24,24,26))
for i,im in enumerate((a,b)):
    m=Image.new("L",(512,512),0); ImageDraw.Draw(m).rounded_rectangle([0,0,512,512],radius=112,fill=255)
    sheet.paste(im,(20+i*(512+20),20),m)
sheet.save("v14_sheet.png")
