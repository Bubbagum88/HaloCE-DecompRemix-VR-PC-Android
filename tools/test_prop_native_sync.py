"""Execute native scenery transform sender: roll, unchanged state and refresh."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'port/linux/game/network_coop.c').read_text()
a=s.rfind('static struct',0,s.index('} host_sent_transforms['))
b=s.index('/* host: how each object looked',a)
production=s[a:b]
code=r'''
#include <assert.h>
#include <string.h>
typedef int boolean;typedef struct{float n[3];}real_point3d,real_vector3d;
#define NONE (-1)
#define TRUE 1
#define FALSE 0
#define MAXIMUM_OBJECTS_PER_MAP 16
#define MAXIMUM_OBJECT_TRANSFORMS_PER_MESSAGE 8
#define COOP_MOVED_OBJECTS 1
#define DATUM_INDEX_TO_ABSOLUTE_INDEX(x) ((x)&15)
#define DISTRIBUTED_UNIT_SCALE 1
#define _distributed_message_coop_object_transforms 99
struct object_datum{long definition_index;struct{long parent_object_index;short name_index;real_point3d position;real_vector3d forward,up;}object;};
struct object_iterator{long index;int done;};
struct distributed_coop_object_transform{short name_index,pad;long object_index,definition_index;real_point3d position;real_vector3d forward,up;};
struct distributed_coop_object_transforms_message{struct distributed_coop_object_transform transforms[8];};
static struct{int refresh;}host_resend;
static struct object_datum object={.definition_index=44,.object={.parent_object_index=NONE,.name_index=NONE,.forward={{1,0,0}},.up={{0,0,1}}}};
static int packets;static struct distributed_coop_object_transform received;
static void object_iterator_new(struct object_iterator*i,int mask,int flags){(void)mask;(void)flags;i->done=0;i->index=0x1231;}
static struct object_datum*object_iterator_next(struct object_iterator*i){return i->done++?0:&object;}
static float distance_squared3d(real_point3d const*a,real_point3d const*b){float d=0;for(int i=0;i<3;i++)d+=(a->n[i]-b->n[i])*(a->n[i]-b->n[i]);return d;}
static float dot_product3d(real_vector3d const*a,real_vector3d const*b){return a->n[0]*b->n[0]+a->n[1]*b->n[1]+a->n[2]*b->n[2];}
static void distributed_vector_pack(real_vector3d const*a,int scale,real_vector3d*b){(void)scale;*b=*a;}
static void send_to_clients(struct distributed_coop_object_transforms_message*m,int type,int count,int size){assert(type==99&&count==1&&size==sizeof received);received=m->transforms[0];packets++;}
'''+production+r'''
int main(void){
 host_send_object_transforms();assert(packets==0);
 host_send_object_transforms();assert(packets==0);
 object.object.up=(real_vector3d){{0,1,0}};
 host_send_object_transforms();assert(packets==1&&received.up.n[1]==1&&received.forward.n[0]==1);
 host_send_object_transforms();assert(packets==1);
 host_resend.refresh=1;host_send_object_transforms();assert(packets==2);
 host_resend.refresh=0;object.object.position.n[0]=1;host_send_object_transforms();assert(packets==3&&received.position.n[0]==1);
 object.object.parent_object_index=5;object.object.up=(real_vector3d){{0,0,1}};host_send_object_transforms();assert(packets==3);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c=Path(tmp)/'sync.c';exe=Path(tmp)/'sync';c.write_text(code)
    subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('native scenery transform roll + refresh passed (production sender, ASan/UBSan)')
