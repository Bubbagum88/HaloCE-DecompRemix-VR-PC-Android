"""Test67 optional campaign preparation and content verification, offline Java."""
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
java=r'''
package com.halo.decomp;
import java.io.*;import java.nio.file.*;import java.security.*;import java.util.*;
public class PrepareCheck {
 static void check(boolean b){if(!b)throw new AssertionError();}
 static byte[] bytes={1,2,3,4};
 static String hash()throws Exception{StringBuilder s=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))s.append(String.format("%02x",b&255));return s.toString();}
 static ByteArrayInputStream recipe(String id)throws Exception{
  String s="recipe.version=1\nmod.id="+id+"\nsource=synthetic test fixture\n";
  for(String n:new String[]{"a10.map","bitmaps.map","sounds.map","loc.map"})s+="file."+n+".size=4\nfile."+n+".sha256="+hash()+"\n";
  return new ByteArrayInputStream(s.getBytes("UTF-8"));
 }
 public static void main(String[] args)throws Exception{
  File root=new File(args[0]);ModInstaller m=new ModInstaller(root);ModInstaller.Progress quiet=(s,p)->{};
  // Private four-byte fixtures exercise the real transaction, not copyrighted maps.
  Arrays.fill(ModInstaller.RESOURCE_SIZES,4);
  ModInstaller.Mod mod=new ModInstaller.Mod("fixture","Fixture","",new ModInstaller.ModMap[]{new ModInstaller.ModMap("a10",-1,4)},".map",true,null,null,ModInstaller.STATUS_SUPPORTED,"fixture");
  m.prepare(mod,recipe("fixture"),quiet);
  check(new File(root,"mods/fixture/support.properties").isFile());
  check(new File(root,"mods/fixture/maps").isDirectory()&&new File(root,"mods/ce").isDirectory());
  check(m.missingForSetup(mod).contains("a10.map")&&m.missingForSetup(mod).contains("bitmaps.map"));
  long[] size=new long[1];
  check(m.importTarget(mod,"../a10.map",size)==null&&m.importTarget(mod,"ui.map",size)==null);
  File target=m.importTarget(mod,"A10.MAP",size);check(size[0]==4);
  for(String n:new String[]{"a10.map","bitmaps.map","sounds.map","loc.map"}){
   File f=m.importTarget(mod,n,size);m.importFile(mod,new ByteArrayInputStream(bytes),f,size[0],n,quiet);
  }
  check(m.missingForSetup(mod).equals("none"));m.validatePrepared(mod,true,quiet);
  m.importFile(mod,new InputStream(){public int read(){throw new AssertionError("valid file must be reused");}},target,4,"already here",quiet);
  Files.write(target.toPath(),new byte[]{9,9,9,9}); // same size is not sufficient
  boolean rejected=false;try{m.validatePrepared(mod,true,quiet);}catch(IOException e){rejected=e.getMessage().contains("SHA-256");}check(rejected);
  rejected=false;try{m.importFile(mod,new ByteArrayInputStream(new byte[]{8,8,8,8}),target,4,"bad",quiet);}catch(IOException e){rejected=true;}check(rejected&&Files.readAllBytes(target.toPath())[0]==9);
  m.importFile(mod,new ByteArrayInputStream(bytes),target,4,"repair",quiet);m.prepare(mod,recipe("fixture"),quiet);
  check(Files.readAllBytes(target.toPath())[0]==1);
  File original=new File(root,"maps/a10.map");original.getParentFile().mkdirs();try(RandomAccessFile out=new RandomAccessFile(original,"rw")){out.setLength(4096);out.write(new byte[]{'d','a','e','h',5,0,0,0});}
  m.install(mod,quiet);check(m.installed(mod)&&Files.readAllBytes(original.toPath())[0]==1);
  m.prepare(mod,recipe("fixture"),quiet);m.restore(mod,quiet);check(Files.readAllBytes(original.toPath())[0]=='d');
  // Missing/bad recipes cannot be accepted; unsupported maps cannot overwrite base content.
  rejected=false;try{m.prepare(mod,recipe("other"),quiet);}catch(IOException e){rejected=true;}check(rejected);
  File bitmap=m.importTarget(mod,"bitmaps.map",size);Files.write(bitmap.toPath(),new byte[]{0,0,0,0});
  rejected=false;try{m.install(mod,quiet);}catch(IOException e){rejected=true;}check(rejected&&!m.installed(mod)&&Files.readAllBytes(original.toPath())[0]=='d');
  System.out.println("PASS: Test67 campaign prepare/repeat/import/resource routing/hash rejection/repair/reuse/install/active verification/restore; original maps preserved");
 }
}
'''
with tempfile.TemporaryDirectory(prefix='test67-campaigns-') as d:
 p=Path(d);(p/'PrepareCheck.java').write_text(java)
 subprocess.run(['javac','-encoding','UTF-8','-d',str(p),str(R/'port/android/app/src/main/java/com/halo/decomp/ModInstaller.java'),str(p/'PrepareCheck.java')],check=True)
 subprocess.run(['java','-cp',str(p),'com.halo.decomp.PrepareCheck',str(p/'game')],check=True)
for name in ['spv1','altheros']:
 text=(R/f'port/android/app/src/main/assets/campaigns/{name}.properties').read_text()
 assert f'mod.id={name}' in text and text.count('.sha256=')==13 and text.count('.size=')==13
 assert 'No game or mod assets included' in text
launcher=(R/'port/android/app/src/main/java/com/halo/decomp/LauncherActivity.java').read_text()
assert 'Prepare / verify mod files' in launcher and 'getAssets().open("campaigns/" + mod.id + ".properties")' in launcher
assert 'modImport.setVisibility(!installed ? View.VISIBLE : View.GONE);' in launcher
assert 'prepareMod(mod);\n                    mods.install' in launcher
print('PASS: Test67 both bundled recipes contain 13 source hashes; launcher prepares before install and allows both campaign folder imports')
