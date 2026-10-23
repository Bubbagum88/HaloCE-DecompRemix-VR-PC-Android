"""Exercise the production portable touch-layout preset codec with javac."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "port/android/app/src/main/java/com/halo/decomp"

CHECK = r'''package com.halo.decomp;
public final class TouchLayoutCodecCheck {
 static int checks;
 static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
 static void rejects(String text,String message){boolean rejected=false;try{TouchLayoutCodec.decode(text);}catch(IllegalArgumentException expected){rejected=true;}check(rejected,message);}
 static void same(float a,float b,String m){check(Float.floatToIntBits(a)==Float.floatToIntBits(b),m);}
 public static void main(String[] args){
  TouchLayout original=new TouchLayout();
  for(boolean visible:original.visible)check(visible,"new controls remain visible by default");
  original.scale=1.27f;original.opacity=.72f;original.sensitivityX=2.1f;original.sensitivityY=.83f;
  original.deadZone=.12f;original.swipe=false;original.lookAnywhere=true;original.floating=true;original.invert=true;
  original.color=0xff8be298;original.gyroMode=GyroPolicy.WHILE_TOUCHING;original.gyroX=1.75f;original.gyroY=2.25f;original.gyroInvert=true;
  for(int i=0;i<TouchLayout.COUNT;i++){original.x[i]=(i+1)/20f;original.y[i]=(20-i)/20f;original.size[i]=.7f+i*.04f;original.alpha[i]=.2f+i*.04f;original.visible[i]=(i%3)!=1;}
  String exported=TouchLayoutCodec.encode(original);
  check(exported.contains("format=halo-ce-touch-layout")&&exported.contains("version=1"),"preset has a versioned file identity");
  check(exported.contains("control.move.x=")&&exported.contains("control.touch_visibility.enabled="),"presets use stable control IDs");
  check(!exported.contains("controller_touch_mode=")&&!exported.contains("pad_response="),"controller preferences are excluded while dpad layout IDs remain portable");
  TouchLayout restored=TouchLayoutCodec.decode(exported);
  same(restored.scale,original.scale,"scale round-trips");same(restored.opacity,original.opacity,"opacity round-trips");
  same(restored.sensitivityX,original.sensitivityX,"horizontal response round-trips");same(restored.sensitivityY,original.sensitivityY,"vertical response round-trips");
  same(restored.deadZone,original.deadZone,"dead zone round-trips");check(!restored.swipe&&restored.lookAnywhere&&restored.floating&&restored.invert,"touch behavior round-trips");
  check(restored.color==original.color&&restored.gyroMode==original.gyroMode&&restored.gyroInvert,"color and gyro options round-trip");
  for(int i=0;i<TouchLayout.COUNT;i++){same(restored.x[i],original.x[i],TouchLayout.CONTROL_IDS[i]+" x");same(restored.y[i],original.y[i],TouchLayout.CONTROL_IDS[i]+" y");same(restored.size[i],original.size[i],TouchLayout.CONTROL_IDS[i]+" size");same(restored.alpha[i],original.alpha[i],TouchLayout.CONTROL_IDS[i]+" alpha");check(restored.visible[i]==original.visible[i],TouchLayout.CONTROL_IDS[i]+" visibility");}
  rejects(exported.replace("version=1","version=2"),"unsupported future version rejected");
  rejects(exported.replaceFirst("(?m)^control\\.move\\.x=.*\\n",""),"missing field rejected");
  rejects(exported.replace("scale=1.27","scale=NaN"),"non-finite field rejected");
  rejects(exported.replaceFirst("(?m)^control\\.move\\.x=.*$","control.move.x=1.5"),"out-of-range position rejected");
  rejects(exported+"unknown=1\\n","unknown fields rejected");
  rejects(exported.substring(0,exported.length()-8),"truncated file rejected");
  rejects("x".repeat(TouchLayoutCodec.MAX_BYTES+1),"oversized file rejected");
  rejects(exported.replace("format=halo-ce-touch-layout","format=not-a-touch-layout"),"wrong file type rejected");
  // Test73b: SPRINT, the last stable ID; a preset made before it (none of its fields) imports with SPRINT at its
  // defaults and its own controls as saved; one with only some of SPRINT's fields is incomplete
  check(TouchLayout.COUNT==20&&TouchLayout.CONTROL_IDS[TouchLayout.SPRINT].equals("sprint")&&TouchLayout.SPRINT==TouchLayout.COUNT-1,"SPRINT is the last stable ID");
  check(exported.contains("control.sprint.x=")&&exported.contains("control.sprint.enabled="),"a new preset has SPRINT");
  String older=exported.replaceAll("(?m)^control\\.sprint\\..*\\n","");
  check(!older.contains("control.sprint."),"a preset made before SPRINT");
  TouchLayout imported=TouchLayoutCodec.decode(older);
  same(imported.x[TouchLayout.SPRINT],TouchLayout.DEFAULT_X[TouchLayout.SPRINT],"SPRINT at its default x");
  same(imported.y[TouchLayout.SPRINT],TouchLayout.DEFAULT_Y[TouchLayout.SPRINT],"SPRINT at its default y");
  check(imported.visible[TouchLayout.SPRINT]&&imported.size[TouchLayout.SPRINT]==1f&&imported.alpha[TouchLayout.SPRINT]==1f,"SPRINT enabled at its default size");
  for(int i=0;i<TouchLayout.SPRINT;i++){same(imported.x[i],original.x[i],"older preset keeps "+TouchLayout.CONTROL_IDS[i]);check(imported.visible[i]==original.visible[i],"older preset keeps "+TouchLayout.CONTROL_IDS[i]+"'s visibility");}
  same(imported.scale,original.scale,"older preset keeps its options");
  rejects(exported.replaceFirst("(?m)^control\\.sprint\\.x=.*\\n",""),"a preset with only some of SPRINT's fields rejected");
  rejects(older.replaceFirst("(?m)^control\\.move\\.x=.*\\n",""),"a pre-SPRINT preset missing another field still rejected");
  System.out.println("Touch layout codec: "+checks+" checks passed (round-trip, defaults, stable IDs, validation, no gamepad settings)");
 }
}'''


def main():
    with tempfile.TemporaryDirectory(prefix="touch-layout-codec-") as directory:
        output = Path(directory)
        check = output / "com/halo/decomp/TouchLayoutCodecCheck.java"
        check.parent.mkdir(parents=True)
        check.write_text(CHECK, encoding="utf-8")
        sources = [JAVA / "TouchLayout.java", JAVA / "TouchLayoutCodec.java", JAVA / "GyroPolicy.java", check]
        subprocess.run(["javac", "-d", str(output), *map(str, sources)], check=True)
        subprocess.run(["java", "-cp", str(output), "com.halo.decomp.TouchLayoutCodecCheck"], check=True)


if __name__ == "__main__":
    main()
