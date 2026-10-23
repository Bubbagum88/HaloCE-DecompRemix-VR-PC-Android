"""Sanitizer tests for production menu platform helpers; no SDL/game launch.

SDL events/window/clipboard/time are deterministic doubles. The capture,
settling, key state, config refresh and window safety logic is real source.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "port/linux/src/sdl_platform.c").read_text()
header = (ROOT / "port/linux/src/sdl_platform.h").read_text()

def fn(name):
    match = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{]*\)\s*\{', source, re.M)
    assert match, name
    start = source.index('{', match.start())
    end, depth = start + 1, 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[match.start():end] + '\n'

pump = fn('platform_pump_events')
assert 'if (binding_capture_event(&event))' in pump
assert pump.index('if (binding_capture_event(&event))') < pump.index('switch (event.type)')
assert 'mouse_buttons_down = 0;' in pump
assert 'binding_clear_pending();' in pump[pump.index('case SDL_EVENT_WINDOW_FOCUS_LOST:'):]
assert 'platform_quit_requested' in pump
assert 'vr_initialize();' in fn('platform_video_initialize')
assert 'SDL_GL_CreateContext' in fn('platform_video_initialize')
apply = fn('platform_display_apply')
assert not any(s in apply for s in ('SDL_CreateWindow', 'SDL_GL_CreateContext', 'vr_initialize'))
# Test73 (OpenCE 244's display modes on flat PC): the window is resized or switched only outside the VR build
vr_guarded = apply[apply.index('#ifndef HALO_VR'):apply.rindex('#endif')]
assert all(s in vr_guarded for s in ('SDL_SetWindowSize', 'platform_window_set_fullscreen'))
assert apply.index('#ifndef HALO_VR') < apply.index('SDL_SetWindowSize') and \
    apply.index('#ifndef HALO_ANDROID') < apply.index('SDL_SetWindowSize')


def region(start, end):
    a = source.index(start)
    return source[a:source.index(end, a) + len(end)]


# the lists, real on the desktop and stubs on Android (and the helpers they read)
lists = region('/* the size added to the list unless it has it already; the count */',
               '#else\nint platform_display_resolutions(long *widths, long *heights, int maximum)\n{\n\t(void)widths;')
lists = '#ifndef HALO_ANDROID\n' + \
    source[source.index(lists):source.index('#endif', source.index(lists)) + len('#endif')]
helpers = ''.join(fn(n) for n in ('platform_size_parse', 'platform_resolution_setting', 'platform_window_size_setting',
                                  'platform_display_size'))

shim = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
typedef int BOOL;
typedef unsigned char BYTE;
typedef char CHAR;
typedef uint64_t Uint64;
typedef uint32_t SDL_AudioDeviceID;
typedef int SDL_ThreadID;
typedef void SDL_Window;
typedef uint32_t SDL_DisplayID;
typedef struct { int w, h; float pixel_density, refresh_rate; } SDL_DisplayMode;
typedef struct { int x, y, w, h; } SDL_Rect;
#define FALSE 0
#define TRUE 1
#define SDL_SCANCODE_COUNT 512
#define SDL_SCANCODE_UNKNOWN 0
#define SDL_SCANCODE_A 4
#define SDL_SCANCODE_RETURN 40
#define SDL_SCANCODE_ESCAPE 41
#define SDL_SCANCODE_DELETE 76
#define SDL_SCANCODE_BACKSPACE 42 /* Test72: a binding's default */
#define SDL_SCANCODE_F11 68
#define SDL_SCANCODE_F12 69
enum { SDL_EVENT_KEY_DOWN=1,SDL_EVENT_KEY_UP,SDL_EVENT_MOUSE_BUTTON_DOWN,
 SDL_EVENT_MOUSE_BUTTON_UP,SDL_EVENT_MOUSE_WHEEL,SDL_EVENT_MOUSE_MOTION,
 SDL_EVENT_WINDOW_FOCUS_LOST,SDL_EVENT_GAMEPAD_ADDED,SDL_EVENT_FINGER_DOWN };
typedef struct { int type; struct {int scancode;bool down,repeat;} key;
 struct {unsigned button;bool down;} button;struct {float y;} wheel; } SDL_Event;
static int locks;
static void pthread_mutex_lock(int *lock){(void)lock;assert(!locks);locks++;}
static void pthread_mutex_unlock(int *lock){(void)lock;assert(locks==1);locks--;}
static Uint64 now=1;
static Uint64 SDL_GetTicks(void){return now;}
static int generation, vsync=1, interpolation=1;
static unsigned long config_changes(void){return generation;}
static int config_boolean(const char *name){return !strcmp(name,"display.interpolation")?interpolation:vsync;}
static int window_w=1920,window_h=1080,thread=7,swap_calls,last_interval,clipboard_frees;
static void SDL_GetWindowSizeInPixels(void *w,int *x,int *y){assert(w);*x=window_w;*y=window_h;}
static int SDL_GetCurrentThreadID(void){return thread;}
static void SDL_GL_SetSwapInterval(int value){swap_calls++;last_interval=value;}
static const char *clipboard="hello";
static char written_clipboard[100];
static char *SDL_GetClipboardText(void){return clipboard?strdup(clipboard):NULL;}
static void SDL_free(void *p){if(p)clipboard_frees++;free(p);}
static void SDL_SetClipboardText(const char *p){snprintf(written_clipboard,sizeof(written_clipboard),"%s",p);}
/* Test73: the display (1920x1080, its usable part 1920x1040 under a taskbar) and its fullscreen modes */
static const char *resolution_setting="native",*window_size_setting="";
static const char *config_string(const char *name){return !strcmp(name,"display.resolution")?resolution_setting:
 !strcmp(name,"display.window_size")?window_size_setting:"";}
static long config_integer(const char *name){(void)name;return 2;}
static BOOL platform_sdl_initialize(void){return TRUE;}
static SDL_DisplayID SDL_GetDisplayForWindow(void *w){return w?1:0;}
static SDL_DisplayID SDL_GetPrimaryDisplay(void){return 1;}
static const SDL_DisplayMode desktop_mode={1920,1080,1.0f,60.0f};
static const SDL_DisplayMode *SDL_GetDesktopDisplayMode(SDL_DisplayID d){return d?&desktop_mode:NULL;}
static SDL_DisplayMode **SDL_GetFullscreenDisplayModes(SDL_DisplayID d,int *count){
 static const int sizes[][2]={{1920,1080},{1600,900},{1280,720},{1280,720},{800,600},{640,480},{320,240}};
 SDL_DisplayMode **modes=malloc(sizeof(*modes)*7+sizeof(SDL_DisplayMode)*7);SDL_DisplayMode *m=(SDL_DisplayMode*)(modes+7);
 (void)d;for(int i=0;i<7;i++){m[i].w=sizes[i][0];m[i].h=sizes[i][1];m[i].pixel_density=1.0f;m[i].refresh_rate=60.0f;modes[i]=&m[i];}
 *count=7;return modes;}
static bool SDL_GetDisplayUsableBounds(SDL_DisplayID d,SDL_Rect *r){(void)d;r->x=r->y=0;r->w=1920;r->h=1040;return true;}
/* platform_display_apply's window: the mode set, F11's, the fullscreen kind's applies, resizes */
enum { _display_mode_windowed = 0, _display_mode_borderless, _display_mode_fullscreen };
static int mode_setting=_display_mode_borderless,kind_applies,fullscreen_switches,resizes,last_fullscreen=-1;
static int platform_display_mode(void){return mode_setting;}
static BOOL platform_fullscreen_setting(void){return mode_setting!=_display_mode_windowed;}
static void platform_fullscreen_kind_apply(void){kind_applies++;}
static void platform_window_set_fullscreen(BOOL f){fullscreen_switches++;last_fullscreen=f;}
static void SDL_SetWindowSize(void *w,int x,int y){(void)w;(void)x;(void)y;resizes++;}
'''

globals_c = r'''
static SDL_Window *platform_window=(void*)1;
static SDL_ThreadID platform_event_thread=7;
static BOOL platform_quit_requested;
static int input_lock;
static struct platform_input_state input_state;
static unsigned char keys_pressed[SDL_SCANCODE_COUNT];
static unsigned char mouse_buttons_pressed[PLATFORM_MOUSE_BUTTON_COUNT];
#ifndef HALO_ANDROID
static struct platform_ui_pointer ui_pointer;
static float ui_pointer_wheel;
#endif
enum { _binding_capture_idle, _binding_capture_waiting, _binding_capture_taken };
static int binding_capture,binding_capture_result,binding_captured_input;
static BOOL binding_settling;
static Uint64 binding_taken_ms,binding_polled_ms;
static unsigned mouse_buttons_down;
#define BINDING_ABANDONED_MS 500
#define BINDING_UNCLAIMED_MS 2000
static unsigned long keystroke_head,keystroke_count;
#ifndef HALO_ANDROID
static long platform_window_width=1280,platform_window_height=960;
static int platform_window_mode=_display_mode_borderless;
#endif
'''

checks = r'''
static BOOL event(int type,int code,int repeat){
 SDL_Event e={0};e.type=type;
 if(type==SDL_EVENT_KEY_DOWN||type==SDL_EVENT_KEY_UP){e.key.scancode=code;e.key.down=type==SDL_EVENT_KEY_DOWN;e.key.repeat=repeat;}
 if(type==SDL_EVENT_MOUSE_BUTTON_DOWN||type==SDL_EVENT_MOUSE_BUTTON_UP){e.button.button=code;e.button.down=type==SDL_EVENT_MOUSE_BUTTON_DOWN;}
 if(type==SDL_EVENT_MOUSE_WHEEL)e.wheel.y=(float)code;
 pthread_mutex_lock(&input_lock);BOOL consumed=binding_capture_event(&e);pthread_mutex_unlock(&input_lock);return consumed;
}
int main(void){
 struct platform_input_state snapshot;int input=-99;long w[2]={-1,-2},h[2]={-1,-2};char text[5];
 (void)w;(void)h;
#ifndef HALO_ANDROID
 {
  /* Test73: the display's modes below its own, largest first, each once, none under 640x480; a set one the
  display lacks is shown too; the offered window sizes that fit the usable desktop, with the Xbox's */
  long rw[16],rh[16];int n=platform_display_resolutions(rw,rh,16);
  assert(n==4&&rw[0]==1600&&rh[0]==900&&rw[1]==1280&&rh[1]==720&&rw[2]==800&&rh[2]==600&&rw[3]==640&&rh[3]==480);
  resolution_setting="1366x768";n=platform_display_resolutions(rw,rh,16);
  assert(n==5&&rw[1]==1366&&rh[1]==768);resolution_setting="native";
  assert(!platform_display_resolutions(rw,rh,0));
  n=platform_window_sizes(rw,rh,16);
  /* (640x480, 800x600, 1024x768, 1280x960, 1280x800, 1440x900, 1280x720, 1600x900: those that fit) */
  assert(n==8&&rw[0]==640&&rh[0]==480&&rw[7]==1600&&rh[7]==900);
  for(int i=0;i<n;i++)assert((rw[i]<=1920&&rh[i]<=1040)||(rw[i]==1280&&rh[i]==960));
  window_size_setting="2560x1440";n=platform_window_sizes(rw,rh,16);
  assert(rw[n-1]==2560&&rh[n-1]==1440);window_size_setting="";
 }
#else
 {long rw[2],rh[2];assert(!platform_display_resolutions(rw,rh,2)&&!platform_window_sizes(rw,rh,2));}
#endif
 platform_window=NULL;platform_display_apply();assert(!swap_calls);
 platform_window=(void*)1;thread=8;platform_display_apply();assert(!swap_calls);thread=7;
 platform_display_apply();
#ifdef HALO_VR
 assert(!swap_calls);
#else
 assert(swap_calls==1&&last_interval==1);vsync=0;platform_display_apply();assert(last_interval==0);
#ifndef HALO_ANDROID
 /* nothing changed: no resize, no switch (F11's choice kept); a new window size resizes once; a new mode
 switches once, to its kind */
 assert(!resizes&&!fullscreen_switches&&kind_applies==2);
 window_size_setting="1600x900";platform_display_apply();platform_display_apply();assert(resizes==1);
 mode_setting=_display_mode_windowed;platform_display_apply();platform_display_apply();
 assert(fullscreen_switches==1&&last_fullscreen==0);
 thread=8;window_size_setting="800x600";platform_display_apply();assert(resizes==1);thread=7;window_size_setting="";
#endif
#endif
 clipboard_frees=0;
 assert(halo_interpolation_enabled()==1);interpolation=0;generation++;assert(!halo_interpolation_enabled());
 assert(platform_clipboard_get(text,sizeof(text))&&!strcmp(text,"hell")&&clipboard_frees==1);
 assert(!platform_clipboard_get(NULL,2)&&!platform_clipboard_get(text,0));
 clipboard=NULL;assert(!platform_clipboard_get(text,sizeof(text))&&!*text);
 platform_clipboard_set("invite");platform_clipboard_set(NULL);assert(!strcmp(written_clipboard,"invite"));
 platform_request_quit();assert(platform_quit_requested&&!locks);

 platform_menus_set_active(TRUE);assert(input_state.menus);
 keystroke_count=5;keys_pressed[SDL_SCANCODE_RETURN]=1;input_state.mouse_dx=200;
 platform_binding_capture_begin();assert(!keystroke_count&&!keys_pressed[SDL_SCANCODE_RETURN]&&!input_state.mouse_dx);
 assert(!platform_binding_capture_poll(&input)&&input==-99);
 assert(event(SDL_EVENT_KEY_DOWN,SDL_SCANCODE_A,1));assert(!platform_binding_capture_poll(&input));
 assert(event(SDL_EVENT_KEY_DOWN,-1,0));assert(event(SDL_EVENT_KEY_DOWN,SDL_SCANCODE_COUNT,0));
 assert(!platform_binding_capture_poll(&input));
 assert(event(SDL_EVENT_KEY_DOWN,SDL_SCANCODE_A,0));
 assert(platform_binding_capture_poll(&input)==1&&input==SDL_SCANCODE_A);
 input_state.mouse_dx=40;platform_input_read(&snapshot,TRUE);
 assert(!snapshot.keys[SDL_SCANCODE_A]&&!snapshot.mouse_dx&&binding_settling);
 assert(event(SDL_EVENT_KEY_UP,SDL_SCANCODE_A,0));platform_input_read(&snapshot,TRUE);assert(!binding_settling);
 assert(!event(SDL_EVENT_KEY_DOWN,SDL_SCANCODE_A,0));platform_input_read(&snapshot,TRUE);assert(snapshot.keys[SDL_SCANCODE_A]);
 event(SDL_EVENT_KEY_UP,SDL_SCANCODE_A,0);

 platform_binding_capture_begin();event(SDL_EVENT_KEY_DOWN,SDL_SCANCODE_ESCAPE,0);assert(platform_binding_capture_poll(NULL)==3);
 event(SDL_EVENT_KEY_UP,SDL_SCANCODE_ESCAPE,0);platform_input_read(&snapshot,TRUE);
 platform_binding_capture_begin();event(SDL_EVENT_KEY_DOWN,SDL_SCANCODE_DELETE,0);assert(platform_binding_capture_poll(&input)==2);
 event(SDL_EVENT_KEY_UP,SDL_SCANCODE_DELETE,0);platform_input_read(&snapshot,TRUE);
 platform_binding_capture_begin();event(SDL_EVENT_KEY_DOWN,SDL_SCANCODE_F11,0);assert(!platform_binding_capture_poll(&input));
 event(SDL_EVENT_KEY_UP,SDL_SCANCODE_F11,0);
 event(SDL_EVENT_MOUSE_BUTTON_DOWN,1,0);assert(platform_binding_capture_poll(&input)==1&&input==INPUT_MOUSE+1);
 platform_input_read(&snapshot,TRUE);assert(binding_settling&&!snapshot.mouse_buttons[1]);
 event(SDL_EVENT_MOUSE_BUTTON_UP,1,0);platform_input_read(&snapshot,TRUE);assert(!binding_settling&&!input_state.mouse_buttons[1]);
 platform_binding_capture_begin();event(SDL_EVENT_MOUSE_WHEEL,-1,0);assert(platform_binding_capture_poll(&input)==1&&input==INPUT_WHEEL_DOWN);
 platform_input_read(&snapshot,TRUE);assert(!binding_settling);

 /* Screen abandoned / result unclaimed / closing menu all release capture. */
 platform_binding_capture_begin();now+=501;platform_input_read(&snapshot,TRUE);assert(!binding_capture&&!binding_settling);
 platform_binding_capture_begin();event(SDL_EVENT_MOUSE_WHEEL,1,0);now+=2001;platform_input_read(&snapshot,TRUE);assert(!binding_capture&&!binding_settling);
 platform_binding_capture_begin();assert(!event(SDL_EVENT_FINGER_DOWN,0,0));assert(!event(SDL_EVENT_GAMEPAD_ADDED,0,0));
 platform_menus_set_active(FALSE);platform_input_read(&snapshot,TRUE);assert(!binding_capture&&!binding_settling&&!snapshot.menus);
 platform_binding_capture_begin();assert(!event(SDL_EVENT_WINDOW_FOCUS_LOST,0,0));assert(platform_binding_capture_poll(&input)==3);
 platform_input_read(&snapshot,TRUE);assert(!binding_settling&&!locks);
 /* A press and release between reads remains visible once outside capture. */
 keys_pressed[SDL_SCANCODE_A]=1;mouse_buttons_pressed[1]=1;platform_input_read(&snapshot,TRUE);
 assert(snapshot.keys[SDL_SCANCODE_A]&&snapshot.mouse_buttons[1]);platform_input_read(&snapshot,TRUE);
 assert(!snapshot.keys[SDL_SCANCODE_A]&&!snapshot.mouse_buttons[1]);
 puts("PASS: menu platform capture/settling, untouched touch/gamepad events, clipboard, config refresh and safe display helpers");
}
'''

functions = '#ifndef HALO_ANDROID\n' + helpers + '#endif\n' + lists + '\n' + ''.join(fn(n) for n in (
    'halo_interpolation_enabled',
    'platform_display_apply','platform_clipboard_get','platform_clipboard_set','platform_request_quit',
    'binding_clear_pending','binding_take','binding_capture_event','platform_binding_capture_begin',
    'platform_binding_capture_poll','platform_menus_set_active','platform_input_read'))
out = ROOT / 'build/test31-menu-platform'
out.mkdir(parents=True, exist_ok=True)
cfile = out / 'menu_platform.c'
cfile.write_text(shim + re.sub(r'^#include <SDL3/[^\n]*\n', '', header, flags=re.M) + globals_c + functions + checks)
for variant, flags in (('desktop',[]),('android',['-DHALO_ANDROID']),('vr',['-DHALO_ANDROID','-DHALO_VR'])):
    exe = out / variant
    subprocess.run(['clang','-std=gnu11','-O1','-fsanitize=address,undefined',*flags,str(cfile),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
