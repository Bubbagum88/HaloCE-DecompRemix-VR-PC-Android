package com.halo.decomp;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Managed, immutable-at-import game-data sets. No live maps are replaced. */
final class GameDataLibrary {
    static final int MAX_PROFILES=64, MAX_MAPS=512;
    static final long MAX_BYTES=12L*1024*1024*1024;
    private static final Object SELECTION_LOCK=new Object();
    final File base, versions, inbox;
    static final class Profile {
        final String id,label,build,fingerprint; final File root;
        Profile(String id,String label,String build,String fingerprint,File root) {
            this.id=id;this.label=label;this.build=build;this.fingerprint=fingerprint;this.root=root;
        }
        String description(){return label+" — "+build+" — "+fingerprint.substring(0,Math.min(12,fingerprint.length()));}
    }
    GameDataLibrary(File base) throws IOException {
        if(base==null)throw new IOException("Game storage is unavailable");
        this.base=base.getCanonicalFile();versions=new File(this.base,"game-versions");inbox=new File(versions,"inbox");
        if(!inbox.isDirectory()&&!inbox.mkdirs())throw new IOException("Cannot create game-data library");
    }
    static boolean idValid(String id){return id!=null&&id.matches("p-[a-f0-9]{32}");}
    static File activeRoot(File base) {
        if(base==null)return null;
        File marker=new File(base,"active-data.txt");
        try {
            if(!marker.exists())return base;
            if(marker.length()>64)throw new IOException("Invalid selection");
            String id=new String(Files.readAllBytes(marker.toPath()),StandardCharsets.UTF_8).replaceAll("^\\s+|\\s+$","");
            if(id.isEmpty())return base;
            if(!idValid(id))throw new IOException("Invalid profile ID");
            File root=new File(new File(base,"game-versions"),id);
            if(!root.getCanonicalFile().getParentFile().equals(new File(base,"game-versions").getCanonicalFile())||!new File(root,"profile.properties").isFile()||!new File(root,"maps/ui.map").isFile())
                throw new IOException("Selected profile is incomplete");
            return root;
        } catch(IOException e){return null;} // never silently launch a different set
    }
    List<Profile> list() throws IOException {
        List<Profile> result=new ArrayList<>();
        if(new File(base,"maps/ui.map").isFile())result.add(new Profile("","Existing game data",MapInfo.read(new File(base,"maps/ui.map")).summary(),"existing",base));
        File[] dirs=versions.listFiles();if(dirs==null)return result;
        Arrays.sort(dirs,Comparator.comparing(File::getName));
        for(File dir:dirs) if(idValid(dir.getName())&&dir.isDirectory()&&dir.getCanonicalFile().equals(dir.getAbsoluteFile())) {
            File file=new File(dir,"profile.properties");if(!file.isFile()||file.length()>262144)continue;
            Properties props=new Properties();try(InputStream in=new FileInputStream(file)){props.load(in);}
            if(!new File(dir,"maps/ui.map").isFile())continue;
            result.add(new Profile(dir.getName(),props.getProperty("label","Imported data"),props.getProperty("build","unknown"),props.getProperty("fingerprint","unknown"),dir));
        }
        return result;
    }
    File stage() throws IOException {
        if(list().size()>=MAX_PROFILES)throw new IOException("Library limit reached (64 sets)");
        File dir=new File(versions,"partial-"+UUID.randomUUID().toString());
        if(!dir.mkdir())throw new IOException("Cannot create import staging folder");return dir;
    }
    /**
     * Accept the same safe Custom Edition leaf-name characters as the native
     * network map-name validator. The Android library handles leaf filenames
     * only, so path separators remain forbidden; Windows device names are
     * rejected too because imported profiles may later be used on desktop.
     */
    static boolean mapName(String name){
        if(name==null||name.length()<5||name.length()>104||!name.regionMatches(true,name.length()-4,".map",0,4)||name.contains(".."))return false;
        int stemEnd=name.length()-4;
        if(stemEnd>100)return false;
        for(int i=0;i<stemEnd;i++){
            char c=name.charAt(i);
            if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-'||c=='.'||c==' '||c=='['||c==']'||c=='('||c==')'||c=='+'))return false;
        }
        for(int i=0;i<stemEnd;i++)if(name.charAt(i)=='.'||name.charAt(i)==' '){stemEnd=i;break;}
        String stem=name.substring(0,stemEnd).toLowerCase(Locale.ROOT);
        if(stem.equals("con")||stem.equals("prn")||stem.equals("aux")||stem.equals("nul"))return false;
        return !(stem.length()==4&&(stem.startsWith("com")||stem.startsWith("lpt"))&&stem.charAt(3)>='0'&&stem.charAt(3)<='9');
    }
    static void copy(InputStream in,File target,long limit) throws IOException {
        byte[] buffer=new byte[1024*1024];long total=0;
        try(OutputStream out=new FileOutputStream(target)) {for(int n;(n=in.read(buffer))!=-1;){
            if(Thread.currentThread().isInterrupted())throw new InterruptedIOException("Import cancelled");
            total+=n;if(total>limit)throw new IOException("Import exceeds size limit");out.write(buffer,0,n);
        }}
    }
    static void copyMaps(File source,File stage) throws IOException {
        File maps=new File(stage,"maps");if(!maps.mkdir())throw new IOException("Cannot create maps staging folder");
        File[] files=source.listFiles();if(files==null)throw new IOException("Cannot read maps folder");long total=0;int count=0;
        for(File f:files)if(f.isFile()&&mapName(f.getName())) {
            if(!f.getCanonicalFile().equals(f.getAbsoluteFile()))throw new IOException("Linked files are not imported");
            total+=f.length();if(++count>MAX_MAPS||total>MAX_BYTES)throw new IOException("Game data exceeds library limits");
            File target=new File(maps,f.getName().toLowerCase(Locale.ROOT));
            if(target.exists())throw new IOException("Duplicate map name: "+f.getName());
            try(InputStream in=new FileInputStream(f)){copy(in,target,MAX_BYTES);}
        }
    }
    Profile finish(File stage,String label) throws Exception {
        if(Thread.currentThread().isInterrupted())throw new InterruptedIOException("Import cancelled");
        if(!stage.getCanonicalFile().getParentFile().equals(versions.getCanonicalFile())||!stage.getName().startsWith("partial-"))throw new IOException("Invalid staging directory");
        File maps=new File(stage,"maps");MapInfo ui=MapInfo.read(new File(maps,"ui.map"));
        if(!ui.problem.isEmpty()||ui.region.equals("unknown")||ui.type!=2)throw new IOException("Requires supported Xbox Halo CE menu/cache data; "+ui.summary());
        File[] files=maps.listFiles((d,n)->mapName(n));if(files==null||files.length==0||files.length>MAX_MAPS)throw new IOException("Invalid map count");
        Arrays.sort(files,Comparator.comparing(File::getName));MessageDigest digest=MessageDigest.getInstance("SHA-256");
        Properties props=new Properties();Set<String> builds=new TreeSet<>();long total=0;
        for(File f:files){
            total+=f.length();if(total>MAX_BYTES)throw new IOException("Game data exceeds 12 GiB");
            if(!Arrays.asList("bitmaps.map","sounds.map","loc.map").contains(f.getName())){
                MapInfo info=MapInfo.read(f);if(!info.problem.isEmpty()||info.region.equals("unknown")||info.type>2)throw new IOException("Unsupported map: "+f.getName()+"; "+info.summary());
                builds.add(info.region+" "+info.build);
            }
            String hash=MapInfo.sha256(f);props.setProperty("map."+f.getName(),hash);
            digest.update((f.getName()+":"+f.length()+":"+hash+"\n").getBytes(StandardCharsets.UTF_8));
        }
        StringBuilder hex=new StringBuilder();for(byte b:digest.digest())hex.append(String.format("%02x",b&255));
        String fingerprint=hex.toString();for(Profile p:list())if(p.fingerprint.equals(fingerprint))return p;
        String id="p-"+UUID.randomUUID().toString().replace("-","");
        label=label==null?"Imported data":label.replaceAll("[\\p{Cntrl}]"," ").trim();if(label.length()>80)label=label.substring(0,80);
        String build=String.join(", ",builds);props.setProperty("label",label);props.setProperty("build",build);props.setProperty("fingerprint",fingerprint);
        props.setProperty("revision","unverified");props.setProperty("schema","1");
        File current=activeRoot(base);File config=new File(current==null?base:current,"config.toml");if(config.isFile()&&config.length()<1024*1024)Files.copy(config.toPath(),new File(stage,"config.toml").toPath());
        try(OutputStream out=new FileOutputStream(new File(stage,"profile.properties"))){props.store(out,"Detected cache builds and exact per-map SHA-256; disc revision not inferred from filenames");}
        if(Thread.currentThread().isInterrupted())throw new InterruptedIOException("Import cancelled");
        File finished=new File(versions,id);if(!stage.renameTo(finished))throw new IOException("Cannot finalize game data");
        return new Profile(id,label,build,fingerprint,finished);
    }
    void discard(File stage)throws IOException {
        if(!stage.exists())return;
        if(!stage.getCanonicalFile().getParentFile().equals(versions.getCanonicalFile())||!stage.getName().startsWith("partial-"))throw new IOException("Refusing cleanup outside import staging");
        Files.walkFileTree(stage.toPath(),new SimpleFileVisitor<Path>(){
            @Override public FileVisitResult visitFile(Path p,java.nio.file.attribute.BasicFileAttributes a)throws IOException{Files.delete(p);return FileVisitResult.CONTINUE;}
            @Override public FileVisitResult postVisitDirectory(Path p,IOException e)throws IOException{if(e!=null)throw e;Files.delete(p);return FileVisitResult.CONTINUE;}
        });
    }
    void select(String id) throws IOException {
        synchronized(SELECTION_LOCK){
            boolean found=false;for(Profile p:list())if(p.id.equals(id)){found=true;break;}
            if(!found)throw new IOException("Profile is unavailable");
            File tmp=new File(base,"active-data.txt.tmp");Files.write(tmp.toPath(),id.getBytes(StandardCharsets.UTF_8));
            Files.move(tmp.toPath(),new File(base,"active-data.txt").toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
        }
    }
    /** Delete only an inactive, complete library-owned copy. Original images and base data are never addressed here. */
    void delete(String id) throws IOException {
        if(!idValid(id))throw new IOException("Only imported game-data sets can be deleted");
        synchronized(SELECTION_LOCK){
            File marker=new File(base,"active-data.txt");String activeId="";
            if(marker.exists()){
                if(marker.length()>64)throw new IOException("Cannot safely delete while the selected game-data marker is invalid");
                activeId=new String(Files.readAllBytes(marker.toPath()),StandardCharsets.UTF_8).trim();
                if(!activeId.isEmpty()&&!idValid(activeId))throw new IOException("Cannot safely delete while the selected game-data marker is invalid");
            }
            if(id.equals(activeId))throw new IOException("Select another complete game-data set before deleting this one");
            File versionsPath=versions.getAbsoluteFile(),versionsCanonical=versions.getCanonicalFile();
            if(!versions.isDirectory()||!versionsCanonical.equals(versionsPath))throw new IOException("The managed game-data folder is not a safe local directory");
            Profile selected=null;for(Profile p:list())if(p.id.equals(id)){selected=p;break;}
            if(selected==null)throw new IOException("Imported game-data set is unavailable");
            File target=new File(versions,id).getAbsoluteFile(),canonical=target.getCanonicalFile();
            if(!canonical.equals(target)||!canonical.getParentFile().equals(versionsCanonical)||canonical.equals(base))
                throw new IOException("Refusing to delete outside the managed game-data folder");
            if(!new File(canonical,"profile.properties").isFile()||!new File(canonical,"maps/ui.map").isFile())
                throw new IOException("Imported game-data set is incomplete; it was not deleted");
            Files.walkFileTree(canonical.toPath(),new SimpleFileVisitor<Path>(){
                @Override public FileVisitResult visitFile(Path path,java.nio.file.attribute.BasicFileAttributes attrs)throws IOException{
                    Files.delete(path);return FileVisitResult.CONTINUE;
                }
                @Override public FileVisitResult postVisitDirectory(Path path,IOException error)throws IOException{
                    if(error!=null)throw error;Files.delete(path);return FileVisitResult.CONTINUE;
                }
            });
        }
    }
    /** Images explicitly placed in the import inbox can be removed to reclaim their copied storage. */
    void deleteInboxImage(String name) throws IOException {
        if(name==null||name.length()<5||name.length()>255||!name.matches("[A-Za-z0-9][A-Za-z0-9 _().+-]*\\.(?i:iso|xiso)"))
            throw new IOException("Choose an ISO/XISO file directly inside the import inbox");
        File inboxPath=inbox.getAbsoluteFile(),inboxCanonical=inbox.getCanonicalFile();
        File target=new File(inbox,name).getAbsoluteFile(),canonical=target.getCanonicalFile();
        if(!inbox.isDirectory()||!inboxCanonical.equals(inboxPath)||!canonical.equals(target)||
            !canonical.getParentFile().equals(inboxCanonical)||!canonical.isFile())
            throw new IOException("The inbox image is unavailable or not a safe local file");
        Files.delete(canonical.toPath());
    }
    List<String> inboxImages() throws IOException {
        List<String> names=new ArrayList<>();File[] files=inbox.listFiles();if(files==null)return names;
        for(File file:files)if(file.isFile()&&file.getCanonicalFile().equals(file.getAbsoluteFile())&&
            file.getName().matches("(?i).+\\.(iso|xiso)"))names.add(file.getName());
        Collections.sort(names,String.CASE_INSENSITIVE_ORDER);return names;
    }
    void rename(Profile p,String label) throws IOException {
        if(p.id.isEmpty())throw new IOException("Existing data keeps its original label");
        Properties props=new Properties();File file=new File(p.root,"profile.properties");
        try(InputStream in=new FileInputStream(file)){props.load(in);}label=label.trim();
        if(label.isEmpty()||label.length()>80||label.matches(".*[\\p{Cntrl}].*"))throw new IOException("Use a label of 1-80 characters");
        props.setProperty("label",label);File tmp=new File(p.root,"profile.properties.tmp");
        try(OutputStream out=new FileOutputStream(tmp)){props.store(out,"User label; detected identity unchanged");}
        Files.move(tmp.toPath(),file.toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
    }
    List<Profile> withMap(String map) throws IOException {
        List<Profile> result=new ArrayList<>();if(!map.matches("[A-Za-z0-9_-]{1,80}"))return result;
        for(Profile p:list())if(MapInfo.read(new File(p.root,"maps/"+map+".map")).multiplayer)result.add(p);return result;
    }
}
