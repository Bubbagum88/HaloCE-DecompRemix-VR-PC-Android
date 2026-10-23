package com.halo.decomp;

import android.app.Activity;
import android.os.Build;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;

/**
 * Test73b (the owner: "a controls section, one where you can click, it'll give you the actual proper mappings. For
 * each controller type ... with the different options enabled, what can change certain mappings ... You can select
 * like what controller type you're using"): the launcher's CONTROLS. A page for each controller this app plays with
 * (ControlsText, assets/controls/controllers.txt, which the PC launcher shows too), drawn as What's New is; its
 * CONTROLLER button chooses another, this device's shown first.
 */
final class ControlsGuide {
    private ControlsGuide() {
    }

    /** this app in the file's words: the VR app (Quest, PICO, Steam Frame) or the phone's */
    static String where() {
        return BuildConfig.APPLICATION_ID.endsWith(".vr") ? "quest" : "phone";
    }

    static String file(Activity activity) {
        try (InputStream in = activity.getAssets().open("controls/controllers.txt")) {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) > 0)
                bytes.write(buffer, 0, read);
            return bytes.toString(StandardCharsets.UTF_8.name());
        } catch (IOException exception) {
            return "";
        }
    }

    static void show(Activity activity) {
        ControlsText controls = new ControlsText(file(activity), where());
        List<ControlsText.Page> pages = controls.pages();
        if (pages.isEmpty()) {
            LauncherHelp.page(activity, "Controls", "The controls could not be read. The Field guide's controls pages "
                + "have them too.");
            return;
        }
        String[] labels = new String[pages.size()];
        for (int index = 0; index < labels.length; index++)
            labels[index] = pages.get(index).label;
        int[] chosen = { ControlsText.first(pages, where().equals("quest"), Lepton.running(), Build.MANUFACTURER) };
        int pad = (int) (20 * activity.getResources().getDisplayMetrics().density);

        LinearLayout box = new LinearLayout(activity);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(pad, pad / 2, pad, pad);
        Button pick = new Button(activity);
        LauncherTheme.button(pick);
        box.addView(pick);
        TextView text = new TextView(activity);
        text.setTextSize(16);
        text.setLineSpacing(0, 1.1f);
        text.setTextIsSelectable(true);
        text.setPadding(0, pad / 2, 0, 0);
        box.addView(text);
        ScrollView scroll = new ScrollView(activity);
        scroll.addView(box);
        Runnable shown = () -> {
            pick.setText("Controller: " + labels[chosen[0]] + "  (change)");
            text.setText(WhatsNew.styled(controls.text(chosen[0]), (int) Math.ceil(text.getPaint().measureText("• "))));
            scroll.scrollTo(0, 0);
        };
        pick.setOnClickListener(v -> new GamepadNavigation.Builder(activity).setTitle("Your controller")
            .setSingleChoiceItems(labels, chosen[0], (dialog, which) -> {
                chosen[0] = which;
                shown.run();
                dialog.dismiss();
            })
            .setNegativeButton("Cancel", null).show());
        shown.run();
        new GamepadNavigation.Builder(activity).setTitle("Controls").setView(scroll).setPositiveButton("Close", null).show();
    }
}
