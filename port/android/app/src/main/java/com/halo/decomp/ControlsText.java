package com.halo.decomp;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Test73b: the launchers' CONTROLS (assets/controls/controllers.txt; the PC launcher's page_controls reads the same
 * file): a page for each controller, and what is shown under every page of its kind. A line "== LABEL | KIND | WHERE"
 * begins a page (KIND vr or flat; WHERE the launchers that list it: quest, phone, pc); a page labelled * is shown
 * under every page of its kind; lines beginning "#" are the file's notes. Pure: tested by
 * tools/test_test73b_controls.py.
 */
final class ControlsText {
    /** a controller's page: its button's label, whether it is a headset's, and its text (What's New's way) */
    static final class Page {
        final String label, text;
        final boolean vr;

        Page(String label, boolean vr, String text) {
            this.label = label;
            this.vr = vr;
            this.text = text;
        }
    }

    private final List<Page> pages = new ArrayList<>();
    private String commonVr = "", commonFlat = "";

    /** the file's pages for the launcher `where` (quest, phone or pc) */
    ControlsText(String file, String where) {
        String label = null, kind = null;
        boolean listed = false;
        StringBuilder body = new StringBuilder();
        for (String line : (file == null ? "" : file).split("\n", -1)) {
            line = line.replaceAll("[ \\r]+$", "");
            if (line.startsWith("#"))
                continue;
            if (line.startsWith("== ")) {
                add(label, kind, listed, body.toString());
                String[] fields = line.substring(3).split("\\|", -1);
                label = fields[0].trim();
                kind = fields.length > 1 ? fields[1].trim() : "";
                listed = false;
                for (String place : (fields.length > 2 ? fields[2].trim() : "").split(" +"))
                    listed |= place.equals(where);
                body.setLength(0);
                continue;
            }
            if (label != null)
                body.append(line).append('\n');
        }
        add(label, kind, listed, body.toString());
    }

    private void add(String label, String kind, boolean listed, String body) {
        if (label == null || !listed || !(kind.equals("vr") || kind.equals("flat")))
            return;
        String text = body.replaceAll("\\s+$", "");
        if (label.equals("*")) {
            if (kind.equals("vr"))
                commonVr = text;
            else
                commonFlat = text;
        } else if (!text.isEmpty()) {
            pages.add(new Page(label, kind.equals("vr"), text));
        }
    }

    List<Page> pages() {
        return pages;
    }

    /** a page's text and, after it, what every page of its kind shows */
    String text(int index) {
        if (index < 0 || index >= pages.size())
            return "";
        Page page = pages.get(index);
        String common = page.vr ? commonVr : commonFlat;
        return common.isEmpty() ? page.text : page.text + "\n\n" + common;
    }

    /** the page of this device's controller: on a headset the Steam Frame's (Lepton), a PICO's (its maker) or the
     * Quest's; else the touch screen's; the first if the file has not that page */
    static int first(List<Page> pages, boolean vr, boolean frame, String manufacturer) {
        String wanted = !vr ? "TOUCH SCREEN" : frame ? "STEAM FRAME"
            : manufacturer != null && manufacturer.toLowerCase(Locale.ROOT).contains("pico") ? "PICO" : "QUEST (TOUCH)";
        for (int index = 0; index < pages.size(); index++)
            if (pages.get(index).label.equals(wanted))
                return index;
        return 0;
    }
}
