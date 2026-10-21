"""Render production shaders through a minimal validation harness, not the application."""
from gpu_probe_windows import *
import time, json
import numpy as np
from PIL import Image
sys.path.insert(0,str(root))
from glyphworld.atlas import build_atlas, GLYPHS
from glyphworld.scene import City, city_geometry, MAX_BOXES
from glyphworld.character import Character
from glyphworld.lighting import Atmosphere

gen_tex=fn('glGenTextures',None,I,c.POINTER(U)); bind_tex=fn('glBindTexture',None,U,U)
tex_image=fn('glTexImage2D',None,U,I,I,I,I,I,U,U,P)
tex_param=fn('glTexParameteri',None,U,U,I)
active=fn('glActiveTexture',None,U)
gen_fbo=fn('glGenFramebuffers',None,I,c.POINTER(U)); bind_fbo=fn('glBindFramebuffer',None,U,U)
attach_tex=fn('glFramebufferTexture2D',None,U,U,U,U,I)
draw_buffers=fn('glDrawBuffers',None,I,c.POINTER(U))
check_fbo=fn('glCheckFramebufferStatus',U,U)
viewport=fn('glViewport',None,I,I,I,I)
use=fn('glUseProgram',None,U)
location=fn('glGetUniformLocation',I,U,c.c_char_p)
uni1f=fn('glUniform1f',None,I,F); uni1i=fn('glUniform1i',None,I,I)
uni2=fn('glUniform2f',None,I,F,F); uni3=fn('glUniform3f',None,I,F,F,F)
gen_vao=fn('glGenVertexArrays',None,I,c.POINTER(U)); bind_vao=fn('glBindVertexArray',None,U)
draw=fn('glDrawArrays',None,U,I,I)
read=fn('glReadPixels',None,I,I,I,I,U,U,P)
finish=fn('glFinish',None)
vao=U(); gen_vao(1,c.byref(vao)); bind_vao(vao)

def texture(width,height,data=None,mono=False):
    t=U(); gen_tex(1,c.byref(t)); bind_tex(0x0DE1,t)
    for p,v in [(0x2801,0x2600),(0x2800,0x2600),(0x2802,0x812F),(0x2803,0x812F)]: tex_param(0x0DE1,p,v)
    tex_image(0x0DE1,0,0x8229 if mono else 0x881A,width,height,0,0x1903 if mono else 0x1908,
              0x1401 if mono else 0x1406,None if data is None else data.ctypes.data)
    return t.value

def fbo(textures):
    f=U(); gen_fbo(1,c.byref(f)); bind_fbo(0x8D40,f)
    for i,t in enumerate(textures): attach_tex(0x8D40,0x8CE0+i,0x0DE1,t,0)
    draw_buffers(len(textures),(U*len(textures))(*[0x8CE0+i for i in range(len(textures))]))
    assert check_fbo(0x8D40)==0x8CD5
    return f.value

def uniforms(name,**values):
    use(programs[name])
    for key,value in values.items():
        loc=location(programs[name],key.encode())
        if isinstance(value,(bool,int)): uni1i(loc,int(value))
        elif isinstance(value,tuple): (uni2 if len(value)==2 else uni3)(loc,*value)
        else: uni1f(loc,value)

def bind(unit,t): active(0x84C0+unit); bind_tex(0x0DE1,t)

W,H=1280,720
GW,GH=256,103
scene=texture(GW*2,GH*2); info=texture(GW*2,GH*2); sf=fbo([scene,info])
fields=[texture(GW,GH),texture(GW,GH)]; ff=[fbo([t]) for t in fields]
out=texture(W,H); of=fbo([out])
pixels,_=build_atlas(); atlas=texture(pixels.shape[1],pixels.shape[0],pixels,True)
tex_param(0x0DE1,0x2801,0x2601); tex_param(0x0DE1,0x2800,0x2601)
geometry=texture(3,MAX_BOXES)
city=City(42)
character=Character()
for f in ff:
    bind_fbo(0x8D40,f); gl.glClear(0x4000)

def render(t,index,history=True,rain=False,light=True,debug=0,hour=9.):
    boxes,count=city_geometry(city,character,t)
    bind(4,geometry)
    tex_image(0x0DE1,0,0x8814,3,MAX_BOXES,0,0x1908,0x1406,boxes.ctypes.data)
    bind_fbo(0x8D40,sf); viewport(0,0,GW*2,GH*2)
    uniforms('scene',resolution=(W,H),time=t,camera_position=(character.x,character.z),zoom=1.,
             player_position=(character.x,character.z),geometry=4,box_count=count,
             daylight=Atmosphere(hour=hour).daylight,interior=city.interior is not None,rain=rain,lighting=light)
    draw(4,0,3)
    bind_fbo(0x8D40,ff[index]); viewport(0,0,GW,GH)
    bind(0,scene); bind(1,info); bind(2,fields[1-index])
    uniforms('field',scene=0,info=1,previous=2,grid=(GW,GH),threshold=.045,history_valid=history)
    draw(4,0,3)
    bind_fbo(0x8D40,of); viewport(0,0,W,H)
    bind(0,atlas); bind(1,fields[index]); bind(2,scene); bind(3,info)
    uniforms('glyph',atlas=0,field=1,scene=2,info=3,grid=(GW,GH),resolution=(W,H),glyph_count=float(len(GLYPHS)),exposure=1.35,debug_view=debug)
    draw(4,0,3)
    finish()
    assert gl.glGetError()==0

def capture(path):
    data=np.empty((H,W,3),dtype=np.uint8)
    read(0,0,W,H,0x1907,0x1401,data.ctypes.data)
    Image.fromarray(data[::-1]).save(path)
    return data

outdir=root/'docs'; outdir.mkdir(exist_ok=True)
render(0.,0,False)
first=capture(outdir/'preview.png')
samples=[]
for frame in range(90):
    start=time.perf_counter(); render(frame/60.,frame%2); samples.append(time.perf_counter()-start)
capture_dir=root/'captures'
capture_dir.mkdir(exist_ok=True)
second=capture(capture_dir/'probe-later.png')
assert np.mean(first!=second)>.01, 'Animation must change image'
assert np.max(second)>80, 'Image unexpectedly dark or empty'
print('Animated pixel fraction:',float(np.mean(first!=second)))
print('Probe FPS (not application FPS):',1/np.mean(samples[10:]))
render(1.5,0,False)
paused_a=capture(capture_dir/'probe-paused.png')
render(1.5,1,True)
paused_b=capture(capture_dir/'probe-paused.png')
assert np.array_equal(paused_a,paused_b), 'Frozen time must produce stable image'
bind_fbo(0x8D40,ff[1])
field_data=np.empty((GH,GW,4),dtype=np.float32)
read(0,0,GW,GH,0x1908,0x1406,field_data.ctypes.data)
assert np.all(np.isfinite(field_data)), 'Field contains non-finite values'
assert np.all((field_data[:,:,0]>=0)&(field_data[:,:,0]<len(GLYPHS)))
for view in range(1,5): render(1.5,view%2,False,debug=view)
render(1.5,0,False,rain=False,light=False)
capture(capture_dir/'probe-dry.png')
render(4.,1,False,hour=23.)
capture(outdir/'preview-night.png')
door=city.nearby(character.x,character.z,0)[0]
character.x,character.z=door.door
assert city.interact(character)
render(4.,0,False,hour=23.)
capture(outdir/'preview-interior.png')
assert city.interact(character)
report={'renderer':gl.glGetString(0x1F01).decode(),'opengl':gl.glGetString(0x1F02).decode(),
        'harness':'ctypes WGL, hidden window + offscreen FBO; NOT ModernGL/GLFW application',
        'resolution':[W,H],'grid':[GW,GH],'sample_frames':80,'warmup_frames':10,
        'mean_ms':float(np.mean(samples[10:])*1000),'p95_ms':float(np.percentile(samples[10:],95)*1000),
        'fps':float(1/np.mean(samples[10:])), 'animated_pixel_fraction':float(np.mean(first!=second)),
        'diagnostic_views_rendered':4,'rain_and_light_off_rendered':True,
        'night_and_interior_rendered':True,'city_boxes':city_geometry(city,character,0)[1],
        'paused_frames_identical':True,'field_indices_finite_and_in_range':True}
(outdir/'gpu-probe.json').write_text(json.dumps(report,indent=2))
gl.wglMakeCurrent(None,None); gl.wglDeleteContext(rc); u.ReleaseDC(h,dc); u.DestroyWindow(h)
