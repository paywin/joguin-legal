"""Optional Windows-only shader validation; not used by the application."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import sys

u, g, gl = c.windll.user32, c.windll.gdi32, c.windll.opengl32
u.CreateWindowExW.restype=w.HWND
u.GetDC.argtypes=[w.HWND]; u.GetDC.restype=w.HDC
u.DestroyWindow.argtypes=[w.HWND]
u.ReleaseDC.argtypes=[w.HWND,w.HDC]
class PFD(c.Structure):
    _fields_=[('nSize',w.WORD),('nVersion',w.WORD),('dwFlags',w.DWORD),
              ('iPixelType',c.c_byte),('cColorBits',c.c_byte),('cRedBits',c.c_byte),
              ('cRedShift',c.c_byte),('cGreenBits',c.c_byte),('cGreenShift',c.c_byte),
              ('cBlueBits',c.c_byte),('cBlueShift',c.c_byte),('cAlphaBits',c.c_byte),
              ('cAlphaShift',c.c_byte),('cAccumBits',c.c_byte),('cAccumRedBits',c.c_byte),
              ('cAccumGreenBits',c.c_byte),('cAccumBlueBits',c.c_byte),('cAccumAlphaBits',c.c_byte),
              ('cDepthBits',c.c_byte),('cStencilBits',c.c_byte),('cAuxBuffers',c.c_byte),
              ('iLayerType',c.c_byte),('bReserved',c.c_byte),('dwLayerMask',w.DWORD),
              ('dwVisibleMask',w.DWORD),('dwDamageMask',w.DWORD)]
g.ChoosePixelFormat.argtypes=[w.HDC,c.POINTER(PFD)]
g.SetPixelFormat.argtypes=[w.HDC,c.c_int,c.POINTER(PFD)]
gl.wglCreateContext.argtypes=[w.HDC]; gl.wglCreateContext.restype=c.c_void_p
gl.wglMakeCurrent.argtypes=[w.HDC,c.c_void_p]
gl.wglDeleteContext.argtypes=[c.c_void_p]
gl.wglGetProcAddress.argtypes=[c.c_char_p]; gl.wglGetProcAddress.restype=c.c_void_p
gl.glGetString.argtypes=[c.c_uint]; gl.glGetString.restype=c.c_char_p
h=u.CreateWindowExW(0,'STATIC','GlyphWorld validation',0,0,0,1280,720,None,None,None,None)
dc=u.GetDC(h)
p=PFD(); p.nSize=c.sizeof(PFD); p.nVersion=1; p.dwFlags=0x24; p.cColorBits=24; p.cDepthBits=24
fmt=g.ChoosePixelFormat(dc,c.byref(p))
assert fmt and g.SetPixelFormat(dc,fmt,c.byref(p)), 'Pixel format unavailable'
rc=gl.wglCreateContext(dc)
assert rc and gl.wglMakeCurrent(dc,rc), 'OpenGL context unavailable'
print('GL renderer:',gl.glGetString(0x1F01))
print('GL version:',gl.glGetString(0x1F02))

def fn(name,result,*args):
    ptr=gl.wglGetProcAddress(name.encode())
    if not ptr or ptr in (1,2,3,-1):
        native=getattr(gl,name,None)
        if native is None: raise RuntimeError('Unavailable GL function '+name)
        native.restype=result; native.argtypes=list(args); return native
    return c.WINFUNCTYPE(result,*args)(ptr)

U=c.c_uint; I=c.c_int; F=c.c_float; P=c.c_void_p
create=fn('glCreateShader',U,U)
source=fn('glShaderSource',None,U,I,c.POINTER(c.c_char_p),c.POINTER(I))
compile_shader=fn('glCompileShader',None,U)
get_shader=fn('glGetShaderiv',None,U,U,c.POINTER(I))
shader_log=fn('glGetShaderInfoLog',None,U,I,c.POINTER(I),c.c_char_p)
create_program=fn('glCreateProgram',U)
attach=fn('glAttachShader',None,U,U)
link=fn('glLinkProgram',None,U)
get_program=fn('glGetProgramiv',None,U,U,c.POINTER(I))
program_log=fn('glGetProgramInfoLog',None,U,I,c.POINTER(I),c.c_char_p)

def shader(path,kind):
    data=path.read_bytes(); src=c.c_char_p(data); obj=create(kind)
    source(obj,1,c.byref(src),None); compile_shader(obj)
    ok=I(); get_shader(obj,0x8B81,c.byref(ok))
    if not ok.value:
        log=c.create_string_buffer(8192); shader_log(obj,8192,None,log)
        raise RuntimeError(f'{path.name}: {log.value.decode()}')
    return obj

programs={}
root=Path(__file__).resolve().parents[1]
vertex=shader(root/'glyphworld/shaders/fullscreen.vert',0x8B31)
for name in ('scene','field','glyph'):
    frag=shader(root/f'glyphworld/shaders/{name}.frag',0x8B30)
    program=create_program(); attach(program,vertex); attach(program,frag); link(program)
    ok=I(); get_program(program,0x8B82,c.byref(ok))
    if not ok.value:
        log=c.create_string_buffer(8192); program_log(program,8192,None,log)
        raise RuntimeError(log.value.decode())
    programs[name]=program
    print('COMPILED + LINKED',name)

if __name__=='__main__':
    gl.wglMakeCurrent(None,None); gl.wglDeleteContext(rc)
    u.ReleaseDC(h,dc); u.DestroyWindow(h)
