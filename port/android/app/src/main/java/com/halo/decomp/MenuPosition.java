package com.halo.decomp;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;

/**
 * Test73 (the owner's): where the VR menus are shown, the main menu's too, chosen in the launcher before playing:
 * config.toml's [vr] menu_anchor, the game's MENU POSITION (VR SETTINGS): "head" (following the head, the default),
 * "world" (fixed in front of the player as a menu opens) or "follow" (fixed, brought back in front after looking
 * away). Plain Java (tools/test_test73_menu_position.py runs it).
 */
final class MenuPosition {
    static final String[] ANCHORS = { "head", "world", "follow" };

    private MenuPosition() { }

    /** the saved choice, "head" when there is none or it is not one of the three */
    static String read(File root) {
        String value = ConfigSettings.read(root, "vr", "menu_anchor", "\"head\"").replace("\"", "").trim();
        for (String anchor : ANCHORS)
            if (anchor.equals(value))
                return anchor;
        return "head";
    }

    static void save(File root, String anchor) throws IOException {
        if (!Arrays.asList(ANCHORS).contains(anchor))
            throw new IOException("Unknown menu position: " + anchor);
        ConfigSettings.write(root, "vr", Collections.singletonMap("menu_anchor", "\"" + anchor + "\""));
    }
}
