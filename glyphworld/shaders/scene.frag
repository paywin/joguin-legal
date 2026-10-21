#version 330
in vec2 uv;
layout(location=0) out vec4 scene_color;
layout(location=1) out vec4 scene_info;
uniform sampler2D geometry;
uniform int box_count;
uniform vec2 resolution;
uniform vec2 camera_position;
uniform vec3 camera_origin, camera_forward, camera_right, camera_up;
uniform bool first_person;
uniform vec2 player_position;
uniform float zoom;
uniform float time;
uniform float daylight;
uniform bool rain;
uniform bool lighting;
uniform bool interior;

float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
vec4 row(int i,int j){return texelFetch(geometry,ivec2(j,i),0);}

float intersectBox(vec3 origin,vec3 inv,vec3 lo,vec3 hi,out vec3 normal){
    vec3 t0=(lo-origin)*inv,t1=(hi-origin)*inv;
    vec3 a=min(t0,t1),b=max(t0,t1);
    float near=max(max(a.x,a.y),a.z),far=min(min(b.x,b.y),b.z);
    normal=-sign(inv)*step(a.yzx,a.xyz)*step(a.zxy,a.xyz);
    return far>max(near,0.)?max(near,0.):1e5;
}

float letters(vec2 p){
    // TOKYO, an original 5x7 bitmap sign, subsequently sampled by the glyph field.
    ivec2 a=ivec2(floor(p*vec2(29,7)));
    if(a.x<0||a.x>=29||a.y<0||a.y>=7) return 0.;
    int letter=a.x/6, x=a.x%6, y=6-a.y;
    if(x>4)return 0.;
    int bits=0;
    if(letter==0) bits=y==0?31:4;
    if(letter==1||letter==4) bits=(y==0||y==6)?14:17;
    if(letter==2) bits=int[7](17,18,20,24,20,18,17)[y];
    if(letter==3) bits=int[7](17,17,10,4,4,4,4)[y];
    return float((bits>>(4-x))&1);
}

void main(){
    vec2 screen=(uv-.5)*vec2(resolution.x/resolution.y,1.);
    vec3 origin=camera_origin;
    vec3 direction=normalize(camera_forward+(camera_right*screen.x+camera_up*screen.y)*1.18);
    vec3 inv=1./(direction+vec3(0.000001));
    float distanceHit=direction.y<-.0001 ? min(120.,-origin.y/direction.y) : 120.;
    vec3 normal=vec3(0,1,0);
    int hit=-1;
    // Fixed upper bound, actual scene count supplied by CPU; no per-glyph Python objects.
    for(int i=0;i<512;++i){
        if(i>=box_count)break;
        vec4 low=row(i,0),high=row(i,1);
        vec3 n;
        float d=intersectBox(origin,inv,low.xyz,high.xyz,n);
        if(first_person && i>=box_count-7)continue;
        if(d<distanceHit){distanceHit=d;normal=n;hit=i;}
    }
    if(hit<0 && (direction.y>=-.0001 || distanceHit>=119.9)){
        vec3 sky=mix(vec3(.62,.76,.86),vec3(.30,.57,.80),smoothstep(0.,.65,direction.y));
        sky=mix(vec3(.16,.23,.34),sky,daylight);
        scene_color=vec4(sky,1.);scene_info=vec4(0.,1.,.5,1.);return;
    }
    vec3 p=origin+direction*distanceHit;
    vec3 col;
    float mat=0.,emission=0.;
    float grain=hash(floor(p.xz*14.));
    if(hit<0){
        vec2 road=abs(mod(p.xz+13.,26.)-13.);
        bool asphalt=min(road.x,road.y)<3.2;
        col=asphalt?vec3(.20,.27,.32):vec3(.55,.59,.57);
        col*=.94+.06*grain;
        if(!asphalt){
            vec2 tile=fract(p.xz*1.4);
            if(min(tile.x,tile.y)<.04)col*=.72;
            if(min(road.x,road.y)<3.5) col=vec3(.82,.80,.66);
        }else{
            bool lane=(road.x<.07&&fract(p.z*.22)<.55)||(road.y<.07&&fract(p.x*.22)<.55);
            bool crossing=(road.x<2.9&&road.y>3.8&&road.y<5.5&&fract(p.x*1.5)<.62)||
                          (road.y<2.9&&road.x>3.8&&road.x<5.5&&fract(p.z*1.5)<.62);
            if(lane)col=vec3(.88,.72,.34);
            if(crossing)col=vec3(.85,.86,.79);
            if(rain){col+=vec3(.08,.14,.17)*(.5+.5*sin(p.z*4.+p.x*3.+time));mat=4.;}
        }
        if(interior){
            col=vec3(.68,.56,.39);
            if(fract(p.z*2.)<.025||fract(p.x*.6+floor(p.z*2.)*.5)<.02)col*=.68;
            if(abs(p.x)>5.8||abs(p.z)>4.8)col=vec3(.12,.20,.24);
            if(abs(p.x)<1.1&&p.z< -3.8&&p.z> -4.5){col=vec3(.34,.83,.78);emission=.5;}
        }
        float ring=abs(length(p.xz-player_position)-.64);
        if(!first_person && ring<.04){col=vec3(.38,.93,.94);emission=.7;}
        if(!interior && lighting && daylight>.05){
            vec3 lightRay=normalize(vec3(-.5,.85,-.3));
            for(int i=0;i<512;++i){
                if(i>=box_count)break;
                vec4 low=row(i,0);
                if(int(low.w)!=1)continue;
                vec3 n;
                float shadow=intersectBox(p+vec3(0,.04,0),1./lightRay,low.xyz,row(i,1).xyz,n);
                if(shadow<70.){col*=1.-.27*daylight;break;}
            }
        }
    }else{
        vec4 lo=row(hit,0),hi=row(hit,1),base=row(hit,2);
        mat=lo.w;col=base.rgb;
        vec3 local=p-lo.xyz,extent=hi.xyz-lo.xyz;
        if(int(mat)==1){
            float horizontal=abs(normal.x)>.5?local.z:local.x;
            vec2 face=vec2(horizontal,p.y);
            vec2 cells=fract(face/vec2(1.25,2.5));
            if(normal.y<.5){
                col*=.97+.03*hash(floor(face));
                if(cells.y<.075)col*=.62;
                bool window=cells.x>.13&&cells.x<.86&&cells.y>.25&&cells.y<.86;
                if(window&&p.y>2.6){
                    float occupied=step(.44,hash(floor(face/vec2(1.25,2.5))+lo.xz));
                    vec3 glass=mix(vec3(.23,.39,.47),vec3(.56,.76,.80),cells.y);
                    col=mix(glass,vec3(.95,.76,.42),occupied*(1.-daylight)*.85);
                    emission=occupied*(1.-daylight)*.6;
                    if(abs(cells.x-.5)<.025)col*=.50;
                }
                if(p.y<2.35){
                    col=vec3(.20,.31,.34);
                    float span=abs(normal.x)>.5?extent.z:extent.x;
                    float mid=span*.5;
                    if(normal.z<-.5 || abs(normal.x)>.5){
                        if(abs(horizontal-mid)<.65){
                            col=vec3(.41,.79,.78);emission=.22;
                            if(abs(horizontal-mid)<.035)col*=.35;
                            if(p.y>1.15&&p.y<1.25)col=vec3(1.,.86,.5);
                        }else{
                            col=mix(vec3(.25,.38,.41),vec3(.72,.66,.45),.35);
                            if(p.y<.35||abs(fract(horizontal*.4)-.5)<.03) col=vec3(.72,.72,.64);
                        }
                    }
                }
                // Light band, store identity, service panels and thin structural seams.
                if(p.y>2.6&&p.y<3.3){
                    col=vec3(.13,.32,.36);
                    float mark=letters(vec2(horizontal/extent.x,(p.y-2.65)/.55));
                    col=mix(col,vec3(.96,.84,.55),mark);emission=mark*.9;
                }
                if(fract(horizontal/3.8)<.035)col*=.65;
                if(p.y>hi.y-1.)col+=vec3(.15,.22,.22);
            }
        }else if(int(mat)==2){
            col*=.82+.18*step(.3,fract((p.x+p.y+p.z)*5.));
            if(hi.w==2.&&normal.z<-.5){
                vec2 f=fract(vec2(local.x*5.,local.y*3.));
                col=f.x>.2&&f.y>.2?vec3(.7,.86,.78):vec3(.12,.25,.3);
            }
        }else if(int(mat)==3){
            col*=.7+.4*hash(floor((p.xz+p.y)*7.));
            mat=3.;
        }else if(int(mat)==4){
            col=mix(col,vec3(.74,.88,.92),pow(max(0.,normal.y),2.)*.65);
        }else if(int(mat)==5){
            if(hi.w==1.&&normal.z<-.5&&local.y>.12&&local.y<.25)col=vec3(.10,.20,.23);
            emission=.15;
        }else if(int(mat)==6){
            if(p.y<.3)col*=.3;
            if(p.y>.45&&p.y<.65 && (abs(normal.x)>.5||abs(normal.z)>.5)){
                col=mix(col,vec3(1.,.88,.59),.55);emission=.35;
            }
        }else if(int(mat)==7){
            float horizontal=abs(normal.x)>.5?local.z:local.x;
            float span=abs(normal.x)>.5?extent.z:extent.x;
            float strokes=letters(vec2(horizontal/span,local.y/extent.y));
            if(hi.w==3.){
                vec2 q=fract(vec2(horizontal/span,local.y/.65));
                strokes=float((abs(q.x-.5)<.065 && q.y>.15 && q.y<.85) ||
                              (abs(q.y-.5)<.07 && q.x>.18 && q.x<.82) ||
                              (abs(q.x-.25)<.05 && q.y>.3 && q.y<.7));
            }
            col=mix(col,vec3(.98,.96,.83),strokes);emission=.45;
        }else if(int(mat)==8){
            col*=.85+.15*sin(p.x*8.+p.z*14.);
        }
    }
    vec3 sun=normalize(vec3(-.5,.85,-.3));
    float diffuse=max(0.,dot(normal,sun));
    // Readable night floor: darkness never erases streets and entrances.
    float ambient=mix(.68,.95,daylight);
    if(interior)ambient=.92;
    if(lighting)col*=ambient+diffuse*daylight*.35;
    col+=col*emission*(1.1-daylight*.5);
    if(!interior){
        float streetlight=exp(-pow(mod(p.x+13.,26.)-13.,2.)*.035);
        col+=vec3(.12,.19,.22)*streetlight*(1.-daylight);
        float haze=smoothstep(22.,65.,distance(p.xz,camera_position))*.85;
        col=mix(col,mix(vec3(.13,.23,.31),vec3(.63,.76,.78),daylight),haze);
        if(rain){
            vec2 raincell=vec2(uv.x*220.+uv.y*25.,uv.y*75.+time*25.);
            vec2 f=fract(raincell);
            float drop=step(.88,hash(vec2(floor(raincell.x),floor(raincell.y*.1))));
            if(f.x<.08&&f.y>.4&&drop>.5){col+=vec3(.15,.22,.24);mat=4.;}
        }
    }
    scene_color=vec4(clamp(col,0.,1.4),1.);
    scene_info=vec4(mat/8.,clamp(distanceHit/160.,0.,1.),grain,1.);
}
