"""Test73 (10j): the stencil shadows (display.stencil_shadows) take away only the light their caster blocks.

render.c draws them once the level's lightmaps are in the frame and before the dynamic lights are added: there the
frame holds the level's light, which the diffuse textures multiply later (rasterizer_xbox_environment.c: the lights
add, ONE/ONE; the textures multiply, DESTCOLOR/ZERO), so a flashlight's or a shield's light falls into a shadow at its
full strength, and fog, particles and glass drawn after are no longer darkened.

At that point the game's stencil holds its bit 0, the first-person weapon's (rasterizer_xbox_models.c), which its
later passes test (the lights, decals, transparent geometry: mask 1 or 3). The production stencil_shadows_render and
its quads run here against a software stencil: every pixel's count of hidden back and front faces, the depth test as
the state has it, each stencil operation as GL does it. Checked: a pixel is darkened exactly where a volume covers it
(more hidden back faces than front), the game's bit 0 is the same after as before for every pixel, every render state
is as the game left it, and nothing is drawn with the depth test off for the volumes. Negative controls: the old
clear in place of the quads, the darkening's mask on every bit, the bit not put back, and the depth test left off.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
render = (ROOT / 'source/render/render.c').read_text(encoding='utf-8')
shadows = (ROOT / 'port/linux/game/stencil_shadows.c').read_text(encoding='utf-8')
environment = (ROOT / 'source/rasterizer/xbox/rasterizer_xbox_environment.c').read_text(encoding='utf-8')

# ---- the order: after the lightmaps and the game's own shadows, before the dynamic lights; once
assert render.count('stencil_shadows_render();') == 1
order = [render.index(call) for call in ('structure_render_lightmaps();', 'render_object_shadows();',
                                         'stencil_shadows_render();', 'lights_render_diffuse();',
                                         'structure_render_diffuse_texture();', 'rasterizer_transparent_geometry_stop();')]
assert order == sorted(order), order
# (the level's light is added, then multiplied by its textures: what the order relies on)
lights = environment[environment.index('void _rasterizer_environment_diffuse_lights_begin('):]
lights = lights[:lights.index('\n}\n')]
assert 'D3DDevice_SetRenderState(D3DRS_SRCBLEND, D3DBLEND_ONE);' in lights
assert 'D3DDevice_SetRenderState(D3DRS_DESTBLEND, D3DBLEND_ONE);' in lights
textures = environment[environment.index('void _rasterizer_environment_diffuse_textures_begin('):]
textures = textures[:textures.index('\n}\n')]
assert '? D3DBLEND_DESTCOLOR' in textures and 'rasterizer_debug_options.drawing_mode == _rasterizer_drawing_mode_overdraw);' in textures
assert 'D3DCLEAR_STENCIL' not in shadows  # (the game's bit 0 is kept, not cleared)


def function(text, name):
    match = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{]*\)\s*\{', text, re.M)
    assert match, name
    end = text.index('{', match.start()) + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[match.start():end]


defines = '\n'.join(re.findall(r'^#define (?:STENCIL_SHADOW_KEEP|STENCIL_SHADOW_GAME_BIT|STENCIL_SHADOW_COUNT_BITS|'
                               r'STENCIL_SHADOWS_ONE_FACE) .*$', shadows, re.M))
assert defines.count('#define') == 4, defines
code = function(shadows, 'stencil_shadow_stencil_quad') + '\n' + function(shadows, 'stencil_shadows_render') + '\n'

fixture = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef unsigned long DWORD;typedef DWORD D3DCOLOR;typedef int boolean;typedef short D3DRENDERSTATETYPE_SHORT;
#define TRUE 1
#define FALSE 0
#define NONE (-1)
enum {D3DRS_ZENABLE,D3DRS_ZWRITEENABLE,D3DRS_ZFUNC,D3DRS_ZBIAS,D3DRS_CULLMODE,D3DRS_COLORWRITEENABLE,
 D3DRS_ALPHABLENDENABLE,D3DRS_ALPHATESTENABLE,D3DRS_SRCBLEND,D3DRS_DESTBLEND,D3DRS_BLENDOP,D3DRS_STENCILENABLE,
 D3DRS_STENCILFUNC,D3DRS_STENCILREF,D3DRS_STENCILMASK,D3DRS_STENCILWRITEMASK,D3DRS_STENCILFAIL,D3DRS_STENCILZFAIL,
 D3DRS_STENCILPASS,D3DRS_COUNT};
typedef int D3DRENDERSTATETYPE;
/* the Xbox values (port/include/xdk/xdk_pdb.h): GL's enumerants, 0 for ZERO */
enum {D3DSTENCILOP_KEEP=7680,D3DSTENCILOP_ZERO=0,D3DSTENCILOP_REPLACE=7681,D3DSTENCILOP_INCRSAT=7682,
 D3DSTENCILOP_DECRSAT=7683,D3DSTENCILOP_INCR=34055,D3DSTENCILOP_DECR=34056};
enum {D3DCMP_NEVER=0x200,D3DCMP_LESS,D3DCMP_EQUAL,D3DCMP_LESSEQUAL,D3DCMP_GREATER,D3DCMP_NOTEQUAL,D3DCMP_GREATEREQUAL,D3DCMP_ALWAYS};
enum {D3DCULL_NONE=0,D3DCULL_CW=0x900,D3DCULL_CCW=0x901};
enum {D3DBLEND_ZERO=0,D3DBLEND_SRCCOLOR=0x300};
enum {D3DBLENDOP_ADD=0x8006};
enum {D3DCOLORWRITEENABLE_RED=1<<16,D3DCOLORWRITEENABLE_GREEN=1<<8,D3DCOLORWRITEENABLE_BLUE=1,D3DCOLORWRITEENABLE_ALPHA=1<<24,
 D3DCOLORWRITEENABLE_ALL=(1<<16)|(1<<8)|1|(1<<24)};
enum {D3DPT_TRIANGLELIST=4};
enum {STENCIL_SHADOW_MAXIMUM_OBJECTS=16};
static DWORD D3D__RenderState[D3DRS_COUNT];
static int device_value;static void *global_d3d_device=&device_value;
struct {struct {struct {short x0,y0,x1,y1;} viewport_bounds;} camera;} global_window_parameters={{{0,0,64,48}}};
static struct {float *positions;unsigned long count;} stencil_shadow_depth_fail,stencil_shadow_depth_pass;
static long stencil_shadow_frame;
#define PIXELS 12
/* each pixel: the stencil, its hidden back and front faces, whether darkened, whether the darkening wrote alpha */
static unsigned char stencil[PIXELS];static int hidden_back[PIXELS],hidden_front[PIXELS],darkened[PIXELS],alpha_written[PIXELS];
static int vertices,volume_draws_without_depth,quads;
static int enabled=1;
static boolean stencil_shadows_enabled(void){return enabled;}
static long stencil_shadow_own_unit(void){return NONE;}
static short stencil_shadow_casters(long casters[],long own_unit){(void)own_unit;casters[0]=7;return 1;}
static float volume[9];
static void stencil_shadow_object(long object,long own_unit){(void)object;(void)own_unit;stencil_shadow_depth_fail.positions=volume;stencil_shadow_depth_fail.count=3;}
static void IDirect3DDevice8_SetRenderState(void *device,int state,DWORD value){assert(device==global_d3d_device);D3D__RenderState[state]=value;}
static void IDirect3DDevice8_Clear(void *device,DWORD count,void *rects,DWORD flags,DWORD color,float z,DWORD s){
 (void)device;(void)count;(void)rects;(void)color;(void)z;assert(flags);for(int p=0;p<PIXELS;p++)stencil[p]=(unsigned char)s;}
static void _rasterizer_debug_immediate_begin(void){D3D__RenderState[D3DRS_ZENABLE]=TRUE;D3D__RenderState[D3DRS_ZWRITEENABLE]=TRUE;
 D3D__RenderState[D3DRS_ALPHABLENDENABLE]=FALSE;D3D__RenderState[D3DRS_ALPHATESTENABLE]=FALSE;D3D__RenderState[D3DRS_CULLMODE]=D3DCULL_NONE;}
static void _rasterizer_debug_immediate_begin_screenspace(void){D3D__RenderState[D3DRS_ZENABLE]=FALSE;D3D__RenderState[D3DRS_CULLMODE]=D3DCULL_NONE;
 D3D__RenderState[D3DRS_ALPHABLENDENABLE]=FALSE;D3D__RenderState[D3DRS_ALPHATESTENABLE]=FALSE;}
static int compare(DWORD function,unsigned reference,unsigned value){
 switch(function){case D3DCMP_NEVER:return 0;case D3DCMP_LESS:return reference<value;case D3DCMP_EQUAL:return reference==value;
 case D3DCMP_LESSEQUAL:return reference<=value;case D3DCMP_GREATER:return reference>value;case D3DCMP_NOTEQUAL:return reference!=value;
 case D3DCMP_GREATEREQUAL:return reference>=value;default:return 1;}}
static unsigned char operate(DWORD op,unsigned char value){
 unsigned ref=D3D__RenderState[D3DRS_STENCILREF]&0xff,result=value;
 switch(op){case D3DSTENCILOP_KEEP:return value;case D3DSTENCILOP_ZERO:result=0;break;case D3DSTENCILOP_REPLACE:result=ref;break;
 case D3DSTENCILOP_INCRSAT:result=value==255?255:value+1;break;case D3DSTENCILOP_DECRSAT:result=value?value-1:0;break;
 case D3DSTENCILOP_INCR:result=(value+1)&0xff;break;case D3DSTENCILOP_DECR:result=(value-1)&0xff;break;default:assert(!"op");}
 {unsigned mask=D3D__RenderState[D3DRS_STENCILWRITEMASK]&0xff;return (unsigned char)((value&~mask)|(result&mask));}}
static int stencil_passes(int p){
 unsigned mask=D3D__RenderState[D3DRS_STENCILMASK]&0xff;
 return !D3D__RenderState[D3DRS_STENCILENABLE]||compare(D3D__RenderState[D3DRS_STENCILFUNC],D3D__RenderState[D3DRS_STENCILREF]&mask,stencil[p]&mask);}
static void IDirect3DDevice8_Begin(void *device,int type){(void)device;assert(type==D3DPT_TRIANGLELIST);vertices=0;}
static void IDirect3DDevice8_SetVertexDataColor(void *device,int reg,D3DCOLOR color){(void)device;(void)reg;(void)color;}
static void IDirect3DDevice8_SetVertexData2s(void *device,int reg,short x,short y){(void)device;(void)reg;(void)x;(void)y;vertices++;}
/* a quad over the view, the depth test off: every pixel's stencil test and operation, and the colour where it passes */
static void IDirect3DDevice8_End(void *device){
 (void)device;assert(vertices==6);assert(!D3D__RenderState[D3DRS_ZENABLE]);quads++;
 for(int p=0;p<PIXELS;p++){int pass=stencil_passes(p);
  if(D3D__RenderState[D3DRS_STENCILENABLE])stencil[p]=operate(D3D__RenderState[pass?D3DRS_STENCILPASS:D3DRS_STENCILFAIL],stencil[p]);
  if(pass&&D3D__RenderState[D3DRS_COLORWRITEENABLE]){
   assert(D3D__RenderState[D3DRS_ALPHABLENDENABLE]&&D3D__RenderState[D3DRS_SRCBLEND]==D3DBLEND_ZERO&&D3D__RenderState[D3DRS_DESTBLEND]==D3DBLEND_SRCCOLOR);
   darkened[p]++;if(D3D__RenderState[D3DRS_COLORWRITEENABLE]&D3DCOLORWRITEENABLE_ALPHA)alpha_written[p]++;}}}
/* the volumes, one face a draw: the faces this cull keeps, where hidden (the depth test failing), take the zfail
operation; with the depth test off none fails */
static void d3d8_gl_draw_positions(const float *positions,unsigned long count,int again){
 (void)positions;(void)count;(void)again;assert(!D3D__RenderState[D3DRS_COLORWRITEENABLE]&&D3D__RenderState[D3DRS_STENCILENABLE]);
 if(!D3D__RenderState[D3DRS_ZENABLE]){volume_draws_without_depth++;return;}
 for(int p=0;p<PIXELS;p++){int faces=D3D__RenderState[D3DRS_CULLMODE]==D3DCULL_CW?hidden_back[p]:hidden_front[p];
  for(int f=0;f<faces;f++)stencil[p]=operate(D3D__RenderState[D3DRS_STENCILZFAIL],stencil[p]);}}
static void d3d8_gl_draw_shadow_volume(const float *positions,unsigned long count,int zfail){(void)positions;(void)count;(void)zfail;assert(!"two-sided");}
'''

checks = r'''
int main(void){
 /* the game's states before: what it must find after */
 DWORD before[D3DRS_COUNT];
 for(int s=0;s<D3DRS_COUNT;s++)D3D__RenderState[s]=before[s]=0x1000+s;
 D3D__RenderState[D3DRS_ZENABLE]=before[D3DRS_ZENABLE]=TRUE;
 /* pixels: the first-person weapon's (bit 0) or not, in no volume, in one, in two, in front of one, behind one */
 static const int game[PIXELS]={0,1,0,1,0,1,0,1,0,1,0,1};
 static const int back[PIXELS]={0,0,1,1,2,2,1,1,0,0,3,3};
 static const int front[PIXELS]={0,0,0,0,0,0,1,1,0,0,1,1};
 for(int p=0;p<PIXELS;p++){stencil[p]=(unsigned char)game[p];hidden_back[p]=back[p];hidden_front[p]=front[p];}
 stencil_shadows_render();
 assert(!volume_draws_without_depth);
 for(int p=0;p<PIXELS;p++){
  int inside=back[p]>front[p];
  if(darkened[p]!=inside){printf("pixel %d: darkened %d, inside %d\n",p,darkened[p],inside);return 1;}
  if(alpha_written[p]){printf("pixel %d: the darkening wrote alpha\n",p);return 1;}
  if(stencil[p]!=game[p]){printf("pixel %d: the game's stencil %d, was %d\n",p,stencil[p],game[p]);return 1;}
 }
 for(int s=0;s<D3DRS_COUNT;s++)if(D3D__RenderState[s]!=before[s]){printf("state %d left %lu, was %lu\n",s,D3D__RenderState[s],before[s]);return 1;}
 /* off: nothing drawn */
 enabled=0;quads=0;stencil_shadows_render();assert(!quads);
 puts("ok");return 0;
}
'''


def run(source, expect_pass):
    with tempfile.TemporaryDirectory(prefix='test73-shadow-lights-') as directory:
        path = Path(directory)
        (path / 'check.c').write_text(source, encoding='utf-8')
        subprocess.run(['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function',
                        '-Wno-unused-parameter', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        str(path / 'check.c'), '-o', str(path / 'check')], check=True)
        result = subprocess.run([str(path / 'check')], capture_output=True, text=True)
        if expect_pass:
            assert result.returncode == 0, result.stdout + result.stderr
        else:
            assert result.returncode != 0, 'a negative control passed'
        return result.stdout


def mutated(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


source = fixture + defines + '\n' + code + checks
run(source, True)
# negative controls: each a fault the checks above must catch
controls = [
    # the old clear before the volumes: the game's bit 0 lost
    ('\tstencil_shadow_stencil_quad(D3DCMP_NOTEQUAL, STENCIL_SHADOW_GAME_BIT, 0x01,\n\t\tD3DSTENCILOP_REPLACE, D3DSTENCILOP_ZERO);',
     '\tIDirect3DDevice8_Clear(global_d3d_device, 0, NULL, 1, 0, 1.f, 0);'),
    # the darkening over every bit: the first-person weapon darkened outside any shadow
    ('D3DRS_STENCILMASK, STENCIL_SHADOW_COUNT_BITS);', 'D3DRS_STENCILMASK, 0xff);'),
    # the game's bit not put back
    ('\tstencil_shadow_stencil_quad(D3DCMP_NOTEQUAL, 0x01, STENCIL_SHADOW_GAME_BIT,\n\t\tD3DSTENCILOP_REPLACE, D3DSTENCILOP_ZERO);', ''),
    # the volumes drawn with the depth test the quad left off
    ('\t_rasterizer_debug_immediate_begin();\n', '\n'),
    # the darkening written into alpha too
    ('D3DCOLORWRITEENABLE_RED | D3DCOLORWRITEENABLE_GREEN | D3DCOLORWRITEENABLE_BLUE);', 'D3DCOLORWRITEENABLE_ALL);'),
]
for before, after in controls:
    run(fixture + defines + '\n' + mutated(code, before, after) + checks, False)
print('PASS: the stencil shadows darken the level\'s light before the dynamic lights are added (after the lightmaps '
      'and the game\'s own shadows), exactly where a volume covers a pixel, the game\'s first-person stencil bit kept '
      'for its later passes and every state restored; %d negative controls caught' % len(controls))
