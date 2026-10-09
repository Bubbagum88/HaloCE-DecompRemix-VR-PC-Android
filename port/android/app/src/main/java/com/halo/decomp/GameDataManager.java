package com.halo.decomp;

import android.app.*;
import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import android.widget.*;
import java.io.*;
import java.nio.channels.FileChannel;
import java.util.*;

/** Launcher UI and scoped-storage import; core identity/selection is testable Java. */
final class GameDataManager {
    static final int PICK_ISO=71, PICK_FOLDER=72;
    final LauncherActivity activity;final File base;final Runnable changed;
    volatile Thread worker;
    GameDataManager(LauncherActivity a,File base,Runnable changed){activity=a;this.base=base;this.changed=changed;}
    boolean busy(){return worker!=null;}
    void close(){Thread t=worker;if(t!=null)t.interrupt();}
    void show(){
        if(busy())return;
        try {
            GameDataLibrary library=new GameDataLibrary(base);List<GameDataLibrary.Profile> profiles=library.list();final AlertDialog[] visible={null};
            LinearLayout rows=new LinearLayout(activity);rows.setOrientation(LinearLayout.VERTICAL);rows.setPadding(24,16,24,16);
            TextView intro=new TextView(activity);intro.setText("Choose which imported game-data set the next launch will use. The first-run import is shown as protected Existing game data. If that is your only row, this is expected; use Import ISO / XISO or Scan inbox below to add another managed set. Byte-identical managed imports share one profile; the Existing game data base row stays separate. You can label managed sets yourself. Revision names are not inferred from filenames.\n\nIMPORTANT: Importing with Android's file picker copies supported maps only. The original ISO/XISO remains in its original location; the launcher does not retain or delete it. Use Android Files to delete that source image. Only image copies placed in the import inbox can be deleted below.\n\nManaged-set deletion removes that set's maps, settings and local saves only; the active set and Existing game data are protected.\n\nDrop ISO/XISO files or folders containing maps into:\n"+library.inbox+"\nThen Scan inbox. You can also import directly with Android's file picker.");rows.addView(intro);
            TextView compatibility=new TextView(activity);compatibility.setText(LauncherHelp.DATA_COMPATIBILITY_NOTE);rows.addView(compatibility);
            File active=GameDataLibrary.activeRoot(base);
            for(GameDataLibrary.Profile p:profiles){
                boolean selected=p.root.equals(active);
                TextView heading=new TextView(activity);heading.setText(p.description());heading.setTextSize(14);rows.addView(heading);
                Button b=new Button(activity);b.setAllCaps(false);b.setText(selected?"Currently selected: "+p.label:"Use this set: "+p.label);b.setEnabled(!selected);rows.addView(b);
                b.setOnClickListener(v->{if(busy())return;try{library.select(p.id);if(visible[0]!=null)visible[0].dismiss();changed.run();Toast.makeText(activity,"Selected "+p.label+" for the next launch. Its saves stay with this set.",Toast.LENGTH_LONG).show();}catch(Exception e){error(e);}});
                if(!p.id.isEmpty()){
                    LinearLayout actions=new LinearLayout(activity);actions.setOrientation(LinearLayout.HORIZONTAL);rows.addView(actions);
                    Button rename=new Button(activity);rename.setAllCaps(false);rename.setText("Rename");actions.addView(rename,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));
                    rename.setOnClickListener(v->{if(busy())return;EditText name=new EditText(activity);name.setText(p.label);
                        new GamepadNavigation.Builder(activity).setTitle("Label this set (detected identity is retained)").setView(name).setPositiveButton("Save",(d,w)->{try{library.rename(p,name.getText().toString());if(visible[0]!=null)visible[0].dismiss();show();}catch(Exception e){error(e);}}).setNegativeButton("Cancel",null).show();});
                    Button delete=new Button(activity);delete.setAllCaps(false);delete.setText(selected?"Delete (select another set first)":"Delete imported copy");delete.setEnabled(!selected);actions.addView(delete,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));
                    delete.setOnClickListener(v->{if(busy()||selected)return;
                        new GamepadNavigation.Builder(activity).setTitle("Delete imported game data?")
                            .setMessage("Delete '"+p.label+"' ("+p.fingerprint.substring(0,Math.min(12,p.fingerprint.length()))+")? This removes only this inactive managed copy, including its local saves and settings. The active set, existing game data and source ISO/XISO are not deleted.")
                            .setPositiveButton("Delete",(d,w)->{try{library.delete(p.id);if(visible[0]!=null)visible[0].dismiss();changed.run();Toast.makeText(activity,"Deleted imported copy: "+p.label,Toast.LENGTH_LONG).show();}catch(Exception e){error(e);}})
                            .setNegativeButton("Cancel",null).show();
                    });
                }
            }
            List<String> images=library.inboxImages();
            if(!images.isEmpty()){
                TextView inboxTitle=new TextView(activity);inboxTitle.setText("ISO/XISO files copied into the import inbox");inboxTitle.setTextSize(16);rows.addView(inboxTitle);
                for(String image:images)add(rows,"Delete inbox image: "+image,()->new GamepadNavigation.Builder(activity)
                    .setTitle("Delete inbox image?").setMessage("This permanently removes only the copied file inside game-versions/inbox:\n"+image)
                    .setPositiveButton("Delete",(d,w)->{try{library.deleteInboxImage(image);if(visible[0]!=null)visible[0].dismiss();show();}catch(Exception e){error(e);}})
                    .setNegativeButton("Cancel",null).show());
            }
            add(rows,"Import ISO / XISO",()->{visible[0].dismiss();pick(PICK_ISO);});add(rows,"Import / scan a folder",()->{visible[0].dismiss();pick(PICK_FOLDER);});
            add(rows,"Scan inbox",()->{visible[0].dismiss();run("Scanning inbox",()->scanInbox(library));});
            ScrollView scroll=new ScrollView(activity);scroll.addView(rows);
            visible[0]=new GamepadNavigation.Builder(activity).setTitle("Game files & versions").setView(scroll).setPositiveButton("Close",null).show();
        }catch(Exception e){error(e);}
    }
    private void add(LinearLayout rows,String text,Runnable action){Button b=new Button(activity);b.setText(text);b.setOnClickListener(v->{if(!busy())action.run();});rows.addView(b);}
    private void pick(int request){Intent i=new Intent(request==PICK_ISO?Intent.ACTION_OPEN_DOCUMENT:Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        if(request==PICK_ISO){i.setType("*/*");i.addCategory(Intent.CATEGORY_OPENABLE);i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);}activity.startActivityForResult(i,request);}
    boolean result(int request,int result,Intent data){
        if(request!=PICK_ISO&&request!=PICK_FOLDER)return false;
        if(result!=Activity.RESULT_OK||data==null)return true;
        run("Importing game files",()->{
            GameDataLibrary library=new GameDataLibrary(base);
            if(request==PICK_FOLDER){Uri tree=data.getData();if(tree==null)throw new IOException("No folder selected");scanTree(library,tree,DocumentsContract.getTreeDocumentId(tree));}
            else {List<Uri> uris=new ArrayList<>();if(data.getClipData()!=null)for(int n=0;n<data.getClipData().getItemCount();n++)uris.add(data.getClipData().getItemAt(n).getUri());else if(data.getData()!=null)uris.add(data.getData());
                if(uris.size()>64)throw new IOException("Select at most 64 images");for(Uri uri:uris)importIso(library,uri,name(uri));}
        });return true;
    }
    interface Job{void run()throws Exception;}
    private void run(String title,Job job){
        if(busy())return;ProgressDialog progress=new ProgressDialog(activity);progress.setTitle(title);progress.setMessage("Reading, validating and fingerprinting. Original files are retained.");progress.setIndeterminate(true);progress.setCancelable(true);progress.setOnCancelListener(d->close());progress.show();
        worker=new Thread(()->{String failure=null;try{job.run();}catch(Exception e){failure=e.getMessage();RunLog.line("Game data import: "+e.getClass().getSimpleName()+": "+failure);}final String message=failure;
            activity.runOnUiThread(()->{worker=null;if(activity.isFinishing()||activity.isDestroyed())return;progress.dismiss();changed.run();if(message!=null)LauncherHelp.page(activity,"Import not completed",message);else show();});},"halo-data-import");worker.start();
    }
    private void importIso(GameDataLibrary library,Uri uri,String label)throws Exception{
        File stage=library.stage();try(ParcelFileDescriptor descriptor=activity.getContentResolver().openFileDescriptor(uri,"r")){
            if(descriptor==null)throw new IOException("Cannot open image");try(FileInputStream stream=new FileInputStream(descriptor.getFileDescriptor())){
                XisoExtractor.extractMaps(stream.getChannel(),stage,(f,d,t)->{if(Thread.currentThread().isInterrupted())throw new java.util.concurrent.CancellationException("Import cancelled");});
            }GameDataLibrary.Profile p=library.finish(stage,label);RunLog.line("Data imported: "+p.description());
        }finally{library.discard(stage);}
    }
    private void scanInbox(GameDataLibrary library)throws Exception{
        File[] items=library.inbox.listFiles();if(items==null||items.length==0)throw new IOException("Inbox is empty. Add ISO/XISO files or folders containing maps, or use Import.");
        if(items.length>64)throw new IOException("Scan at most 64 data sets at once");
        int imported=0;
        for(File item:items){if(Thread.currentThread().isInterrupted())throw new InterruptedIOException("Cancelled");
            if(!item.getCanonicalFile().equals(item.getAbsoluteFile()))continue;
            if(item.isFile()&&item.getName().toLowerCase(Locale.ROOT).matches(".*\\.(iso|xiso)")){
                File stage=library.stage();try(FileInputStream in=new FileInputStream(item)){XisoExtractor.extractMaps(in.getChannel(),stage,(f,d,t)->{if(Thread.currentThread().isInterrupted())throw new java.util.concurrent.CancellationException("Cancelled");});library.finish(stage,item.getName());imported++;}finally{library.discard(stage);}
            }else if(item.isDirectory()){
                File maps=item.getName().equalsIgnoreCase("maps")?item:new File(item,"maps");if(!maps.isDirectory())continue;
                File stage=library.stage();try{GameDataLibrary.copyMaps(maps,stage);library.finish(stage,item.getName());imported++;}finally{library.discard(stage);}
            }
        }if(imported==0)throw new IOException("No ISO/XISO or extracted maps folder found in inbox");
    }
    static final class Doc {String id,name,mime;Doc(String id,String name,String mime){this.id=id;this.name=name;this.mime=mime;}boolean dir(){return DocumentsContract.Document.MIME_TYPE_DIR.equals(mime);}}
    private List<Doc> children(Uri tree,String parent)throws IOException{
        List<Doc> result=new ArrayList<>();Uri uri=DocumentsContract.buildChildDocumentsUriUsingTree(tree,parent);
        String[] columns={DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE};
        try(Cursor c=activity.getContentResolver().query(uri,columns,null,null,null)){
            if(c==null)throw new IOException("Folder cannot be read");while(c.moveToNext()){if(result.size()>=1024)throw new IOException("Folder has too many entries");result.add(new Doc(c.getString(0),c.getString(1),c.getString(2)));}
        }return result;
    }
    private void scanTree(GameDataLibrary library,Uri tree,String root)throws Exception{
        List<Doc> docs=children(tree,root);boolean direct=docs.stream().anyMatch(d->!d.dir()&&d.name.equalsIgnoreCase("ui.map"));
        if(direct){importMaps(library,tree,root,"Imported maps");return;}
        int imported=0;
        for(Doc d:docs){if(d.dir()&&d.name.equalsIgnoreCase("maps")){importMaps(library,tree,d.id,"Imported game data");imported++;}
            else if(d.dir()){for(Doc child:children(tree,d.id))if(child.dir()&&child.name.equalsIgnoreCase("maps")){importMaps(library,tree,child.id,d.name);imported++;break;}}
            else if(d.name.toLowerCase(Locale.ROOT).matches(".*\\.(iso|xiso)")){importIso(library,DocumentsContract.buildDocumentUriUsingTree(tree,d.id),d.name);imported++;}
            if(imported>=64)break;
        }if(imported==0)throw new IOException("No ISO/XISO or extracted maps folder found");
    }
    private void importMaps(GameDataLibrary library,Uri tree,String folder,String label)throws Exception{
        File stage=library.stage();try{
            File maps=new File(stage,"maps");if(!maps.mkdir())throw new IOException("Cannot create staging maps");long total=0;int count=0;
            for(Doc doc:children(tree,folder))if(!doc.dir()&&GameDataLibrary.mapName(doc.name)){
                if(++count>GameDataLibrary.MAX_MAPS)throw new IOException("Too many maps");File target=new File(maps,doc.name.toLowerCase(Locale.ROOT));
                if(target.exists())throw new IOException("Duplicate map name: "+doc.name);
                try(InputStream in=activity.getContentResolver().openInputStream(DocumentsContract.buildDocumentUriUsingTree(tree,doc.id))){if(in==null)throw new IOException("Cannot read "+doc.name);GameDataLibrary.copy(in,target,GameDataLibrary.MAX_BYTES-total);}
                total+=target.length();
            }library.finish(stage,label);
        }finally{library.discard(stage);}
    }
    private String name(Uri uri){try(Cursor c=activity.getContentResolver().query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)){if(c!=null&&c.moveToFirst())return c.getString(0);}catch(Exception ignored){}return "Imported image";}
    private void error(Exception e){LauncherHelp.page(activity,"Game data",e.getMessage()==null?e.getClass().getSimpleName():e.getMessage());}
}
