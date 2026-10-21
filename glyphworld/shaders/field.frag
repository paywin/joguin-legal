#version 330
in vec2 uv;
out vec4 field;
uniform sampler2D scene;
uniform sampler2D info;
uniform sampler2D previous;
uniform vec2 grid;
uniform float threshold;
uniform bool history_valid;
float lum(vec3 c) { return dot(c,vec3(.2126,.7152,.0722)); }
void main() {
    vec2 d=1./vec2(textureSize(scene,0));
    vec3 color=texture(scene,uv).rgb;
    float L=lum(color);
    float dx=lum(texture(scene,uv+vec2(d.x,0)).rgb)-lum(texture(scene,uv-vec2(d.x,0)).rgb);
    float dy=lum(texture(scene,uv+vec2(0,d.y)).rgb)-lum(texture(scene,uv-vec2(0,d.y)).rgb);
    float contrast=length(vec2(dx,dy));
    vec3 meta=texture(info,uv).rgb;
    int material=int(round(meta.x*8.));
    // Brightness, material microtexture and depth influence density together.
    float density=clamp(sqrt(max(L,0.))*1.10+(meta.z-.5)*.10*(1.-meta.y),0.,.999);
    const int ramp[10]=int[10](0,2,3,7,9,8,10,11,12,12);
    int glyph=ramp[int(density*10.)];
    if(contrast>.22) {
        if(abs(dx)>abs(dy)*2.2) glyph=14; // vertical edge
        else if(abs(dy)>abs(dx)*2.2) glyph=13;
        else glyph=dx*dy>0.?16:15; // tangent, not gradient
    } else if(material==3 && density>.30) {
        glyph=meta.z>.53?18:17;
    } else if(material==2 && density>.40 && meta.z>.55) glyph=7;
    else if(material==4 && contrast>.018) glyph=15;
    // A conservative hysteresis prevents static cells flickering at thresholds.
    // Do not retain stale symbols across material or strong edge transitions.
    vec4 old=texture(previous,uv);
    float reference_luminance=L;
    if(history_valid && abs(old.y-L)<threshold && abs(old.z-meta.x)<.02 && contrast<.22) {
        glyph=int(round(old.x));
        reference_luminance=old.y; // Accumulate slow changes instead of locking a glyph forever.
    }
    field=vec4(float(glyph),reference_luminance,meta.x,atan(dy,dx));
}
