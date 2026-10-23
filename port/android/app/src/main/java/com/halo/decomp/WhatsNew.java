package com.halo.decomp;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.net.Uri;
import android.text.SpannableStringBuilder;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.text.style.LeadingMarginSpan;
import android.text.style.RelativeSizeSpan;
import android.text.style.StyleSpan;
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

    /*
     * Test73 (the owner: "make sure the new features details are more clean (the pop up that shows new features in
     * the launcher is the one i mean)"): the notes shown as they are written (whats_new.txt; the PC launcher's
     * news_layout alike): the first line the title, a line in capitals a heading, "• " a point whose lines wrap
     * after its bullet, a blank line a small gap, anything else plain text.
     */
    static final int GAP = 0, TITLE = 1, HEADING = 2, POINT = 3, TEXT = 4;
    /** the headings' and bullets' colour: the menus' Halo blue */
    static final int ACCENT = 0xFF2896FF;

    /** A line's part in the notes (pure: tested). */
    static int kind(String line, boolean first) {
        int length = line.length();
        while (length > 0 && (line.charAt(length - 1) == ' ' || line.charAt(length - 1) == '\r'))
            length--;
        if (length == 0)
            return GAP;
        if (first)
            return TITLE;
        if (length >= 2 && line.charAt(0) == '\u2022' && line.charAt(1) == ' ')
            return POINT;
        for (int index = 0; index < length; index++) {
            char c = line.charAt(index);
            if (c >= 'a' && c <= 'z')
                return TEXT;
        }
        return HEADING;
    }

    /** The notes styled: the title bold and larger, headings bold in the accent, points indented by bullet. */
    static CharSequence styled(String notes, int bulletWidth) {
        SpannableStringBuilder out = new SpannableStringBuilder();
        String[] lines = notes.split("\n", -1);
        boolean first = true;
        for (int index = 0; index < lines.length; index++) {
            String line = lines[index];
            int kind = kind(line, first);
            int start = out.length();
            if (kind != GAP)
                first = false;
            else if (index == lines.length - 1)
                break;
            out.append(kind == GAP ? "" : line.replaceAll("[ \\r]+$", "")).append('\n');
            int end = out.length();
            switch (kind) {
                case GAP:
                    out.setSpan(new RelativeSizeSpan(0.5f), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                    break;
                case TITLE:
                    out.setSpan(new StyleSpan(Typeface.BOLD), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                    out.setSpan(new RelativeSizeSpan(1.15f), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                    break;
                case HEADING:
                    out.setSpan(new StyleSpan(Typeface.BOLD), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                    out.setSpan(new ForegroundColorSpan(ACCENT), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                    break;
                case POINT:
                    out.setSpan(new ForegroundColorSpan(ACCENT), start, start + 1, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                    out.setSpan(new LeadingMarginSpan.Standard(0, bulletWidth), start, end, Spanned.SPAN_PARAGRAPH);
                    break;
                default:
                    break;
            }
        }
        return out;
    }

    static void show(Activity activity) {
        TextView text = new TextView(activity);
        text.setTextSize(16);
        text.setText(styled(text(activity), (int) Math.ceil(text.getPaint().measureText("\u2022 "))));
        text.setLineSpacing(0, 1.1f);
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
