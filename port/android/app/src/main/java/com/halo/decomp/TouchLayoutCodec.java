package com.halo.decomp;

import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Properties;
import java.util.Set;

/** Versioned, allowlisted touch-layout file format; gamepad preferences are never included. */
final class TouchLayoutCodec {
    static final String FORMAT="halo-ce-touch-layout";
    static final int VERSION=1;
    static final int MAX_BYTES=64*1024;

    private TouchLayoutCodec() {}

    static String encode(TouchLayout layout) {
        if(layout==null)throw new IllegalArgumentException("missing touch layout");
        layout.sanitize();
        Properties p=new Properties();
        p.setProperty("format",FORMAT);p.setProperty("version",Integer.toString(VERSION));
        p.setProperty("scale",Float.toString(layout.scale));p.setProperty("opacity",Float.toString(layout.opacity));
        p.setProperty("sensitivityX",Float.toString(layout.sensitivityX));p.setProperty("sensitivityY",Float.toString(layout.sensitivityY));
        p.setProperty("deadZone",Float.toString(layout.deadZone));p.setProperty("swipe",Boolean.toString(layout.swipe));
        p.setProperty("lookAnywhere",Boolean.toString(layout.lookAnywhere));p.setProperty("floating",Boolean.toString(layout.floating));
        p.setProperty("invert",Boolean.toString(layout.invert));p.setProperty("color",String.format(java.util.Locale.ROOT,"%08x",layout.color));
        p.setProperty("gyroMode",Integer.toString(layout.gyroMode));p.setProperty("gyroX",Float.toString(layout.gyroX));
        p.setProperty("gyroY",Float.toString(layout.gyroY));p.setProperty("gyroInvert",Boolean.toString(layout.gyroInvert));
        for(int i=0;i<TouchLayout.COUNT;i++) {
            String prefix="control."+TouchLayout.CONTROL_IDS[i]+".";
            p.setProperty(prefix+"x",Float.toString(layout.x[i]));p.setProperty(prefix+"y",Float.toString(layout.y[i]));
            p.setProperty(prefix+"size",Float.toString(layout.size[i]));p.setProperty(prefix+"alpha",Float.toString(layout.alpha[i]));
            p.setProperty(prefix+"enabled",Boolean.toString(layout.visible[i]));
        }
        try {
            StringWriter writer=new StringWriter();p.store(writer,"Halo CE Android touch layout; import through HUD > Options");
            String result=writer.toString();checkSize(result);return result;
        } catch(IOException impossible) { throw new IllegalStateException(impossible); }
    }

    static TouchLayout decode(String contents) {
        checkSize(contents);
        Properties p=new Properties();
        try { p.load(new StringReader(contents)); }
        catch(Exception malformed) { throw new IllegalArgumentException("malformed layout file",malformed); }
        if(!FORMAT.equals(required(p,"format")))throw new IllegalArgumentException("not a Halo CE touch layout");
        if(!Integer.toString(VERSION).equals(required(p,"version")))throw new IllegalArgumentException("unsupported layout version");

        Set<String> allowed=new HashSet<>();
        for(String key:new String[]{"format","version","scale","opacity","sensitivityX","sensitivityY","deadZone","swipe","lookAnywhere","floating","invert","color","gyroMode","gyroX","gyroY","gyroInvert"})allowed.add(key);
        for(String id:TouchLayout.CONTROL_IDS)for(String field:new String[]{"x","y","size","alpha","enabled"})allowed.add("control."+id+"."+field);
        for(String key:p.stringPropertyNames())if(!allowed.contains(key))throw new IllegalArgumentException("unknown layout field: "+key);
        // (Test73b: a preset made before SPRINT has none of its fields, and SPRINT keeps its defaults; one with
        // only some of them is incomplete)
        String sprint="control."+TouchLayout.CONTROL_IDS[TouchLayout.SPRINT]+".";
        int sprintFields=0;
        for(String field:new String[]{"x","y","size","alpha","enabled"})if(p.containsKey(sprint+field))sprintFields++;
        if(sprintFields!=0&&sprintFields!=5)throw new IllegalArgumentException("layout file is incomplete");
        if(p.size()!=allowed.size()-(sprintFields==0?5:0))throw new IllegalArgumentException("layout file is incomplete");

        TouchLayout result=new TouchLayout();
        result.scale=number(p,"scale",.65f,1.5f);result.opacity=number(p,"opacity",.15f,1f);
        result.sensitivityX=number(p,"sensitivityX",.25f,3f);result.sensitivityY=number(p,"sensitivityY",.25f,3f);
        result.deadZone=number(p,"deadZone",0f,.30f);result.swipe=bool(p,"swipe");
        result.lookAnywhere=bool(p,"lookAnywhere");result.floating=bool(p,"floating");result.invert=bool(p,"invert");
        String color=required(p,"color");
        if(!color.matches("[0-9a-fA-F]{8}"))throw new IllegalArgumentException("invalid control color");
        try { result.color=(int)Long.parseLong(color,16); } catch(NumberFormatException bad) { throw new IllegalArgumentException("invalid control color",bad); }
        String mode=required(p,"gyroMode");
        try { result.gyroMode=Integer.parseInt(mode); } catch(NumberFormatException bad) { throw new IllegalArgumentException("invalid gyro mode",bad); }
        if(result.gyroMode<0||result.gyroMode>=GyroPolicy.MODES.length)throw new IllegalArgumentException("invalid gyro mode");
        result.gyroX=number(p,"gyroX",.25f,4f);result.gyroY=number(p,"gyroY",.25f,4f);result.gyroInvert=bool(p,"gyroInvert");
        for(int i=0;i<TouchLayout.COUNT;i++) {
            if(i==TouchLayout.SPRINT&&sprintFields==0)continue;
            String prefix="control."+TouchLayout.CONTROL_IDS[i]+".";
            result.x[i]=number(p,prefix+"x",0f,1f);result.y[i]=number(p,prefix+"y",0f,1f);
            result.size[i]=number(p,prefix+"size",.65f,1.6f);result.alpha[i]=number(p,prefix+"alpha",.15f,1f);
            result.visible[i]=bool(p,prefix+"enabled");
        }
        result.sanitize();
        return result;
    }

    private static void checkSize(String contents) {
        if(contents==null||contents.getBytes(StandardCharsets.UTF_8).length>MAX_BYTES)
            throw new IllegalArgumentException("layout file is missing or exceeds 64 KiB");
    }
    private static String required(Properties p,String key) {
        String value=p.getProperty(key);
        if(value==null)throw new IllegalArgumentException("missing layout field: "+key);
        return value.trim();
    }
    private static float number(Properties p,String key,float minimum,float maximum) {
        final float value;
        try { value=Float.parseFloat(required(p,key)); }
        catch(NumberFormatException bad) { throw new IllegalArgumentException("invalid number: "+key,bad); }
        if(!Float.isFinite(value)||value<minimum||value>maximum)throw new IllegalArgumentException("out-of-range number: "+key);
        return value;
    }
    private static boolean bool(Properties p,String key) {
        String value=required(p,key);
        if("true".equalsIgnoreCase(value))return true;
        if("false".equalsIgnoreCase(value))return false;
        throw new IllegalArgumentException("invalid boolean: "+key);
    }
}
