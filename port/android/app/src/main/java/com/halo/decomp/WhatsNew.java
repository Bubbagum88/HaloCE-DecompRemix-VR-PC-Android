package com.halo.decomp;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/**
 * Test70: the launcher's What's New: a short summary of this build's
 * changes (assets/whats_new.txt, written with each candidate), shown once
 * after the app's version changes and again whenever the player asks for it
 * (the launcher's "What's new in this version"). Its "Full release notes"
 * button opens the project's GitHub releases page in the device's browser
 * (the Quest's Browser on a headset).
 */
final class WhatsNew {
    static final String RELEASE_NOTES_URL = "https://github.com/" + UpdatePolicy.REPOSITORY + "/releases";
    private static final String PREFS = "whats-new";
    private static final String SEEN = "seen_version_code";

    private WhatsNew() {
    }

    /** Whether this version's notes are still to be shown (pure: tested). */
    static boolean due(int seenCode, int versionCode) {
        return seenCode != versionCode;
    }

    /** Shows the notes when the app's version is not the one last shown. */
    static void maybeShow(Activity activity) {
        SharedPreferences prefs = activity.getSharedPreferences(PREFS, Activity.MODE_PRIVATE);
        if (!due(prefs.getInt(SEEN, -1), BuildConfig.VERSION_CODE))
            return;
        // remembered at once: a crash or a closed launcher does not show it every launch
        prefs.edit().putInt(SEEN, BuildConfig.VERSION_CODE).apply();
        show(activity);
    }

    static String text(Activity activity) {
        try (InputStream in = activity.getAssets().open("whats_new.txt")) {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) > 0)
                bytes.write(buffer, 0, read);
            return bytes.toString(StandardCharsets.UTF_8.name());
        } catch (IOException exception) {
            return "This version's notes could not be read. See the full release notes on GitHub.";
        }
    }

    static void show(Activity activity) {
        TextView text = new TextView(activity);
        text.setText(text(activity));
        text.setTextSize(16);
        text.setTextIsSelectable(true);
        int pad = (int) (20 * activity.getResources().getDisplayMetrics().density);
        text.setPadding(pad, pad, pad, pad);
        ScrollView scroll = new ScrollView(activity);
        scroll.addView(text);
        AlertDialog dialog = new GamepadNavigation.Builder(activity)
            .setTitle("What's new in " + BuildConfig.VERSION_NAME)
            .setView(scroll)
            .setPositiveButton("Close", null)
            .setNeutralButton("View full release notes on GitHub", null)
            .create();
        dialog.setOnShowListener(d -> dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v -> {
            try {
                activity.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(RELEASE_NOTES_URL))
                    .addCategory(Intent.CATEGORY_BROWSABLE));
            } catch (ActivityNotFoundException exception) {
                // (no browser: the address, to type in on another device)
                text.append("\n\nNo browser is available here. The full release notes are at " + RELEASE_NOTES_URL);
            }
        }));
        dialog.show();
    }
}
