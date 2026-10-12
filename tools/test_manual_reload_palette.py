"""Production remapping/hierarchy: transient gun edits cannot contaminate hands."""
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
fp = (ROOT/'source/interface/first_person_weapons.c').read_text()
manual = (ROOT/'port/linux/game/vr_manual_reload.c').read_text()
start = fp.rindex('static void model_remap_node_matrices_to_match_animation_graph(')
remap = fp[start:fp.index('static struct first_person_weapon *first_person_weapon_get',start)]
start = manual.index('static boolean reload_node_under(')
hierarchy = manual[start:manual.index('static boolean reload_matrix_valid',start)]
# Assert the live caller's ordering as well as executing the real remap below.
call = fp.index('vr_manual_reload_model(first_person_weapon->weapon_index')
assert fp.rfind('model_remap_node_matrices_to_match_animation_graph(',0,call)>fp.rfind('render_model(',0,call)
assert fp.index('render_model(',call)<fp.index('model_remap_node_matrices_to_match_animation_graph(',call)
code = r'''
#include <assert.h>
#include <string.h>
#define TRUE 1
#define FALSE 0
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAXIMUM_NODES_PER_ANIMATION 64
#define match_assert(file,line,condition) assert(condition)
#define TAG_BLOCK_GET_ELEMENT(block,index,type) (&((type *)(block)->data)[index])
typedef int boolean;
struct real_matrix4x3 { float scale;float n[12]; };
struct model_node { short parent_node_index; };
struct block { int count;void *data; };
struct model { struct block nodes; };
struct animation_graph { struct block nodes; };
static struct model models[2];
static struct animation_graph graph;
static struct model *model_definition_get(long index) { return &models[index]; }
static struct animation_graph *animation_graph_definition_get(long index) { (void)index;return &graph; }
'''+remap+hierarchy+r'''
int main(void) {
 struct model_node nodes[5]={{-1},{0},{1},{0},{2}};
 struct real_matrix4x3 source[8],before[8],palette[64];
 short gunmap[5]={6,3,7,1,2},handsmap[3]={4,0,5};
 models[0].nodes=(struct block){5,nodes};models[1].nodes=(struct block){3,nodes};graph.nodes.count=8;
 for(int i=0;i<8;i++) {source[i].scale=1;for(int j=0;j<12;j++) source[i].n[j]=i*100+j;}
 memcpy(before,source,sizeof source);
 model_remap_node_matrices_to_match_animation_graph(0,palette,0,source,gunmap);
 for(int i=0;i<5;i++) assert(!memcmp(&palette[i],&source[gunmap[i]],sizeof palette[i]));
 /* Magazine index1, child2 and grandchild4; gun0 and slide3 stay untouched. */
 for(int i=0;i<5;i++) if(reload_node_under(&models[0],i,1)) palette[i].scale=0;
 assert(palette[0].scale==1&&palette[1].scale==0&&palette[2].scale==0&&palette[3].scale==1&&palette[4].scale==0);
 assert(!memcmp(source,before,sizeof source));
 model_remap_node_matrices_to_match_animation_graph(1,palette,0,source,handsmap);
 for(int i=0;i<3;i++) assert(!memcmp(&palette[i],&source[handsmap[i]],sizeof palette[i]));
 /* Next eye/frame starts from the original graph, not the previous edited palette. */
 model_remap_node_matrices_to_match_animation_graph(0,palette,0,source,gunmap);
 for(int i=0;i<5;i++) assert(!memcmp(&palette[i],&source[gunmap[i]],sizeof palette[i]));
 nodes[3].parent_node_index=3;assert(!reload_node_under(&models[0],3,1));
 assert(!reload_node_under(&models[0],-1,1)&&!reload_node_under(&models[0],5,1));
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c=Path(tmp)/'palette.c';exe=Path(tmp)/'palette'
    c.write_text(code)
    subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('manual reload palette isolation: passed (production remap/hierarchy, ASan/UBSan)')
