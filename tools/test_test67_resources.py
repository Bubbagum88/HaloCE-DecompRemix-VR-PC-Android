"""Execute production CE offset routing and converted-audio cache identity.

The resource sizes reproduce the owner's Altheros failure without bundling or
allocating the files. Virtual byte sources check both ends of every interval.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "port/linux/game/custom_edition_cache.c").read_text(encoding="utf-8")


def function(name):
    match = re.search(r"^(?:static )?[\w *]+\b" + name + r"\s*\([^;{]*\)\s*\{", SOURCE, re.M)
    assert match, name
    end = SOURCE.index("{", match.start()) + 1
    depth = 1
    while depth:
        depth += (SOURCE[end] == "{") - (SOURCE[end] == "}")
        end += 1
    return SOURCE[match.start():end]


def structure(name):
    start = SOURCE.index("struct " + name + "\n{")
    end = SOURCE.index("\n};", start) + 3
    return SOURCE[start:end]


constants = "\n".join(re.findall(r"^#define (?:COMBINED_\w+|AUDIO_CACHE_\w+|READ_STAGING_BYTES|FREE_IF).*", SOURCE, re.M))
enum_start = SOURCE.index("enum\n{", SOURCE.index("#define AUDIO_CACHE_VERSION"))
constants += "\n" + SOURCE[enum_start:SOURCE.index("};", enum_start) + 2]
prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
typedef int boolean;
typedef unsigned char byte;
#define TRUE 1
#define FALSE 0
#define NONE (-1)
#define MIN(a,b) ((a)<(b)?(a):(b))
#define csmemset memset
#define csmemcpy memcpy
#define _error_silent 0
#define error(...) ((void)0)
enum { _resource_map_none, _resource_map_bitmaps, _resource_map_sounds, _resource_map_locale, NUMBER_OF_RESOURCE_MAP_TYPES };
struct cache_file_source {void *context;uint32_t size;int (*read)(void*,uint32_t,uint32_t,void*);};
struct cache_file_identity {uint32_t file_size,checksum;};
''' + constants + "\n" + "\n".join(structure(name) for name in (
    "audio_cache_entry", "custom_edition_audio_cache", "custom_edition_file")) + r'''
struct custom_edition_cache_globals {
 struct custom_edition_file map,audio_file,resource_files[NUMBER_OF_RESOURCE_MAP_TYPES];
 struct custom_edition_audio_cache audio;
 uint32_t sounds_offset,loaded_bytes;
 uint8_t *tag_cache;
 char map_path[256];
 byte read_staging[READ_STAGING_BYTES];
};
static struct custom_edition_cache_globals custom_edition_cache_globals;
static int bitmap_arrivals;
static void custom_edition_bitmap_pixels_arrived(void *cache,uint32_t bytes,long tag,long offset,void *buffer)
{(void)cache;(void)bytes;(void)tag;(void)offset;(void)buffer;bitmap_arrivals++;}
static int custom_edition_file_open(struct custom_edition_file *file,char const *path)
{file->stream=fopen(path,"rb");return file->stream!=NULL;}
'''
production = "\n".join(function(name) for name in (
    "custom_edition_resource_layout", "audio_cache_word", "audio_cache_set_word",
    "combined_read", "audio_cache_open", "audio_cache_finish", "custom_edition_cache_read"))
cases = r'''
struct virtual_source {uint32_t size;unsigned char value;};
static int virtual_read(void *context,uint32_t offset,uint32_t size,void *buffer)
{
 struct virtual_source *s=context;
 if(offset>s->size || size>s->size-offset)return 0;
 memset(buffer,s->value,size);return 1;
}
static void bind(struct custom_edition_file *file,struct virtual_source *s)
{file->stream=(FILE*)1;file->source.context=s;file->source.read=virtual_read;file->source.size=s->size;}
static void read_value(uint32_t offset,unsigned char expected)
{unsigned char value=99;custom_edition_cache_read(NONE,(int32_t)offset,1,&value);assert(value==expected);}
static void cache_close(void)
{
 struct custom_edition_cache_globals *g=&custom_edition_cache_globals;
 if(g->audio.stream)fclose(g->audio.stream);
 if(g->audio_file.stream)fclose(g->audio_file.stream);
 free(g->audio.entries);memset(&g->audio,0,sizeof(g->audio));memset(&g->audio_file,0,sizeof(g->audio_file));
}
static void write_cache(unsigned version,uint32_t sounds_offset,unsigned complete)
{
 byte header[AUDIO_CACHE_HEADER_BYTES]={0},entry[16]={0};
 FILE *f=fopen("fixture.audio","wb");assert(f);
 audio_cache_set_word(header,_audio_cache_signature,AUDIO_CACHE_SIGNATURE);
 audio_cache_set_word(header,_audio_cache_version,version);
 audio_cache_set_word(header,_audio_cache_map_size,12345);
 audio_cache_set_word(header,_audio_cache_map_checksum,6789);
 audio_cache_set_word(header,_audio_cache_entry_count,1);
 audio_cache_set_word(header,_audio_cache_index_offset,AUDIO_CACHE_HEADER_BYTES);
 audio_cache_set_word(header,_audio_cache_complete,complete);
 audio_cache_set_word(header,_audio_cache_sounds_offset,sounds_offset);
 audio_cache_set_word(entry,0,sounds_offset+27);
 assert(fwrite(header,1,sizeof(header),f)==sizeof(header));
 assert(fwrite(entry,1,sizeof(entry),f)==sizeof(entry));fclose(f);
}
int main(void)
{
 struct custom_edition_cache_globals *g=&custom_edition_cache_globals;
 struct cache_file_identity identity={12345,6789};
 uint32_t offset=0xdeadbeef;
 struct virtual_source map={COMBINED_AUDIO_OFFSET,1},audio={COMBINED_BITMAPS_OFFSET-COMBINED_AUDIO_OFFSET,2};
 struct virtual_source bitmaps={613838703,3},sounds={333893198,4};
 assert(custom_edition_resource_layout(0,0,&offset)&&offset==COMBINED_SOUNDS_OFFSET);
 assert(custom_edition_resource_layout(123547749,41718640,&offset)&&offset==COMBINED_SOUNDS_OFFSET);
 assert(custom_edition_resource_layout(0x20000000,0x20000000,&offset)&&offset==COMBINED_SOUNDS_OFFSET);
 assert(custom_edition_resource_layout(bitmaps.size,sounds.size,&offset));
 assert(offset==COMBINED_BITMAPS_OFFSET+bitmaps.size&&offset+sounds.size<COMBINED_OFFSET_LIMIT);
 assert(custom_edition_resource_layout(0x20000001,0x1fffffff,&offset)&&offset==0x60000001);
 offset=0xdeadbeef;
 assert(!custom_edition_resource_layout(0x20000001,0x20000000,&offset)&&offset==0xdeadbeef);
 assert(!custom_edition_resource_layout(0xffffffff,1,&offset)&&offset==0xdeadbeef);
 assert(!custom_edition_resource_layout(0,0xffffffff,&offset)&&offset==0xdeadbeef);
 assert(!custom_edition_resource_layout(0x40000000,1,&offset)&&offset==0xdeadbeef);
 assert(custom_edition_resource_layout(0x40000000,0,&offset)&&offset==COMBINED_OFFSET_LIMIT);
 assert(custom_edition_resource_layout(bitmaps.size,sounds.size,&g->sounds_offset));
 bind(&g->map,&map);bind(&g->audio_file,&audio);bind(&g->resource_files[_resource_map_bitmaps],&bitmaps);bind(&g->resource_files[_resource_map_sounds],&sounds);
 read_value(0,1);read_value(COMBINED_AUDIO_OFFSET-1,1);read_value(COMBINED_AUDIO_OFFSET,2);
 read_value(COMBINED_BITMAPS_OFFSET-1,2);read_value(COMBINED_BITMAPS_OFFSET,3);
 read_value(COMBINED_SOUNDS_OFFSET,3);read_value(g->sounds_offset-1,3);
 read_value(g->sounds_offset,4);read_value(g->sounds_offset+sounds.size-1,4);
 read_value(g->sounds_offset+sounds.size,0);read_value(0x80000000,0);read_value(0xffffffff,0);
 {
  byte bytes[READ_STAGING_BYTES+13];
  custom_edition_cache_read(NONE,(int32_t)g->sounds_offset,sizeof(bytes),bytes);
  for(size_t i=0;i<sizeof(bytes);i++)assert(bytes[i]==4);
  memset(bytes,99,sizeof(bytes));custom_edition_cache_read(NONE,(int32_t)(g->sounds_offset-1),2,bytes);assert(!bytes[0]&&!bytes[1]);
  assert(combined_read(g->sounds_offset+11,1,bytes)&&bytes[0]==4);
  assert(!combined_read(g->sounds_offset-1,1,bytes));assert(!combined_read(COMBINED_AUDIO_OFFSET,1,bytes));
  assert(combined_read(11,1,bytes)&&bytes[0]==1);
 }
 assert(!bitmap_arrivals);
 /* The historical layout continues routing stock CE/SPV1 resources. */
 bitmaps.size=123547749;sounds.size=41718640;
 assert(custom_edition_resource_layout(bitmaps.size,sounds.size,&g->sounds_offset));
 read_value(COMBINED_BITMAPS_OFFSET,3);read_value(COMBINED_SOUNDS_OFFSET,4);
 g->audio_file.stream=NULL;strcpy(g->map_path,"fixture");
 write_cache(2,0,1);audio_cache_open(&identity);assert(!g->audio.building&&g->audio.entry_count==1);cache_close();
 g->sounds_offset=COMBINED_BITMAPS_OFFSET+613838703;
 write_cache(2,0,1);audio_cache_open(&identity);assert(g->audio.building&&g->audio.entry_count==0);audio_cache_finish();
 audio_cache_open(&identity);assert(!g->audio.building);cache_close();
 write_cache(AUDIO_CACHE_VERSION,g->sounds_offset,1);audio_cache_open(&identity);
 assert(!g->audio.building&&g->audio.entry_count==1&&g->audio.entries[0].original_offset==g->sounds_offset+27);cache_close();
 write_cache(AUDIO_CACHE_VERSION,g->sounds_offset+1,1);audio_cache_open(&identity);assert(g->audio.building);cache_close();
 write_cache(AUDIO_CACHE_VERSION,g->sounds_offset,0);audio_cache_open(&identity);assert(g->audio.building);cache_close();
 write_cache(1,g->sounds_offset,1);audio_cache_open(&identity);assert(g->audio.building);cache_close();
 write_cache(AUDIO_CACHE_VERSION,g->sounds_offset,1);identity.checksum++;audio_cache_open(&identity);assert(g->audio.building);cache_close();
 remove("fixture.audio");puts("PASS: Test67 bounded Altheros resource layout, streaming reads, signed bounds and audio cache identity");
 return 0;
}
'''

with tempfile.TemporaryDirectory(prefix="test67-resources-") as directory:
    work = Path(directory)
    source = work / "resources.c"
    binary = work / "resources"
    source.write_text(prefix + production + cases)
    command = ["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
               "-fsanitize=address,undefined", "-fno-sanitize-recover=all", str(source), "-o", str(binary)]
    subprocess.run(command, check=True)
    subprocess.run([str(binary)], cwd=work, check=True)
    # The failing old boundary must be detected by these same executable cases.
    old = production.replace("if (bitmaps_bytes > COMBINED_OFFSET_LIMIT - COMBINED_BITMAPS_OFFSET)",
                             "if (bitmaps_bytes > COMBINED_SOUNDS_OFFSET - COMBINED_BITMAPS_OFFSET)")
    assert old != production
    source.write_text(prefix + old + cases)
    subprocess.run(command, check=True)
    result = subprocess.run([str(binary)], cwd=work, capture_output=True, text=True)
    assert result.returncode != 0 and "custom_edition_resource_layout(bitmaps.size,sounds.size,&offset)" in result.stderr
    print("PASS: restoring the old 512 MiB bitmap cap fails the Altheros regression")

# Keep every consumer on the selected layout, including schema ranges and the
# converter which rewrites each raw resource offset before runtime reads.
assert "globals->sounds_offset" in function("custom_edition_cache_tags_validate")
assert "custom_edition_cache_globals.sounds_offset" in function("custom_edition_cache_tags_convert")
assert "custom_edition_resource_layout(" in function("custom_edition_cache_tags_load")
