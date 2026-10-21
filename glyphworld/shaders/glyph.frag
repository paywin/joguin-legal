#version 330
in vec2 uv;
out vec4 frag;
uniform sampler2D atlas;
uniform sampler2D field;
uniform sampler2D scene;
uniform sampler2D info;
uniform vec2 grid;
uniform vec2 resolution;
uniform float glyph_count;
uniform float exposure;
uniform int debug_view;
void main() {
    vec2 cell=floor(uv*grid);
    vec2 center=(cell+.5)/grid;
    vec4 data=texture(field,center);
    vec2 local=fract(uv*grid);
    // Half-texel inset prevents atlas bleeding between neighboring glyphs.
    vec2 tile=vec2(textureSize(atlas,0))/vec2(glyph_count,1.);
    vec2 inset=(local*(tile-1.)+.5)/tile;
    float ink=texture(atlas,vec2((data.x+inset.x)/glyph_count,inset.y)).r;
    vec3 col=texture(scene,center).rgb;
    if(debug_view==1) col=vec3(dot(col,vec3(.2126,.7152,.0722)));
    if(debug_view==2) col=.5+.5*cos(data.w+vec3(0,2.094,4.189));
    if(debug_view==3) col=vec3(1.-texture(info,center).g);
    if(debug_view==4) col=.5+.5*cos(data.z*31.+vec3(0,2.,4.));
    col=pow(clamp(col*exposure,0.,1.),vec3(.62));
    // All color is gated by the glyph mask. No scene/background compositing.
    frag=vec4(col*sqrt(ink),1.);
}
