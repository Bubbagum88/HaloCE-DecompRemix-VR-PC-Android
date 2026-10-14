package com.halo.decomp;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.CompletableFuture;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Test67: Steam Workshop for Halo 1 MCC maps, inside the launcher (the owner:
 * "similar implementation to the Qualyx quest port", "when your on the
 * workshop page for a mod, it lets you click another button that downloads it
 * directly in the launcher", "options to delete them, disable and enable them").
 *
 * The Workshop's own pages (steamcommunity.com, filtered to Halo 1 maps) in a
 * browser; on an item's or a collection's page, DOWNLOAD TO HALO fetches it
 * with the player's Steam account (SteamWorkshop) and installs its Halo 1 MCC
 * maps as a package (MccMaps). INSTALLED lists every package with its size:
 * enable / disable, delete, check for an update, open its Workshop page.
 * Halo 1 MCC maps play solo in this build.
 */
public class WorkshopActivity extends Activity {
    static final String EXTRA_GAME_ROOT = "game_root";
    static final String EXTRA_MANAGE = "manage";
    static final String HOME = "https://steamcommunity.com/workshop/browse/?appid=976730"
        + "&requiredtags%5B%5D=Halo1Campaign&requiredtags%5B%5D=Halo1Multiplayer"
        + "&requiredtags%5B%5D=Halo1CampaignMultiplayer&matching_any_tag=1&browsesort=trend";
    private static final Pattern ITEM = Pattern.compile("steamcommunity\\.com/(?:sharedfiles|workshop)/filedetails/?\\?(?:.*&)?id=(\\d+)");
    private static final int HALO_BLUE = Color.rgb(88, 160, 220);

    private final Handler handler = new Handler(Looper.getMainLooper());
    private File gameRoot;
    private MccMaps maps;
    private SteamWorkshop steam;
    private WebView web;
    private ScrollView managerView;
    private LinearLayout managerList;
    private TextView status;
    private ProgressBar progress;
    private Button download, account, installed;
    private long pageItem;
    private volatile boolean busy;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        String root = getIntent().getStringExtra(EXTRA_GAME_ROOT);
        gameRoot = root != null ? new File(root) : null;
        if (gameRoot == null) {
            finish();
            return;
        }
        maps = new MccMaps(gameRoot);
        steam = new SteamWorkshop(this);

        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(Color.rgb(12, 16, 20));

        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        HorizontalScrollView barScroll = new HorizontalScrollView(this);
        barScroll.addView(bar);
        page.addView(barScroll);
        button(bar, "Back").setOnClickListener(v -> back());
        button(bar, "Halo CE Workshop").setOnClickListener(v -> showBrowser(HOME));
        download = button(bar, "Download to Halo");
        download.setOnClickListener(v -> downloadClicked());
        installed = button(bar, "Installed maps");
        installed.setOnClickListener(v -> showManager());
        account = button(bar, "");
        account.setOnClickListener(v -> accountClicked());
        button(bar, "Close").setOnClickListener(v -> finish());

        status = new TextView(this);
        status.setTextColor(Color.rgb(200, 205, 210));
        status.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        status.setPadding(dp(10), dp(2), dp(10), dp(2));
        page.addView(status);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(1000);
        progress.setVisibility(View.GONE);
        page.addView(progress, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(6)));

        web = new WebView(this);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                // (the Workshop and Steam's own pages; nothing else opens here)
                return !steamHost(request.getUrl());
            }

            @Override
            public void doUpdateVisitedHistory(WebView view, String url, boolean isReload) {
                pageChanged(url);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                pageChanged(url);
            }
        });
        page.addView(web, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        managerView = new ScrollView(this);
        managerList = new LinearLayout(this);
        managerList.setOrientation(LinearLayout.VERTICAL);
        managerList.setPadding(dp(16), dp(8), dp(16), dp(16));
        managerView.addView(managerList);
        managerView.setVisibility(View.GONE);
        page.addView(managerView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        setContentView(page);
        refreshAccount();
        pageChanged(null);
        if (getIntent().getBooleanExtra(EXTRA_MANAGE, false))
            showManager();
        else
            showBrowser(HOME);
        status("Browse Halo 1 maps made for MCC; on a map's page, tap DOWNLOAD TO HALO. Downloads need your "
            + "Steam account that owns Halo: The Master Chief Collection. MCC maps play solo in this build.");
    }

    @Override
    protected void onDestroy() {
        if (steam != null)
            new Thread(steam::close, "steam-close").start();
        if (web != null)
            web.destroy();
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        back();
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private Button button(LinearLayout parent, String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setAllCaps(true);
        LauncherTheme.button(button);
        LinearLayout.LayoutParams layout = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        layout.setMargins(dp(4), dp(4), dp(4), dp(4));
        parent.addView(button, layout);
        return button;
    }

    private void status(String text) {
        handler.post(() -> status.setText(text));
    }

    private void progress(float fraction) {
        handler.post(() -> {
            if (fraction < 0) {
                progress.setIndeterminate(true);
                progress.setVisibility(View.VISIBLE);
            } else if (fraction >= 1f) {
                progress.setVisibility(View.GONE);
            } else {
                progress.setIndeterminate(false);
                progress.setProgress((int) (fraction * 1000));
                progress.setVisibility(View.VISIBLE);
            }
        });
    }

    private void setBusy(boolean value) {
        busy = value;
        handler.post(() -> {
            download.setEnabled(!value && pageItem != 0);
            account.setEnabled(!value);
            if (!value)
                progress.setVisibility(View.GONE);
        });
    }

    private void back() {
        if (managerView.getVisibility() == View.VISIBLE) {
            showBrowser(null);
        } else if (web.canGoBack()) {
            web.goBack();
        } else {
            finish();
        }
    }

    private void showBrowser(String url) {
        managerView.setVisibility(View.GONE);
        web.setVisibility(View.VISIBLE);
        if (url != null)
            web.loadUrl(url);
    }

    private void pageChanged(String url) {
        Matcher match = url != null ? ITEM.matcher(url) : null;
        pageItem = match != null && match.find() ? parse(match.group(1)) : 0;
        handler.post(() -> {
            download.setEnabled(!busy && pageItem != 0);
            download.setText(pageItem != 0 ? "Download to Halo" : "Download (open a map)");
        });
    }

    /** Steam's own sites over https (a site of the same ending, such as notsteamcommunity.com, is not one) */
    static boolean steamHost(Uri url) {
        String host = url.getHost();
        if (host == null || !"https".equals(url.getScheme()))
            return false;
        for (String steam : new String[] {"steamcommunity.com", "steampowered.com", "steamstatic.com", "steamusercontent.com"})
            if (host.equals(steam) || host.endsWith("." + steam))
                return true;
        return false;
    }

    private static long parse(String text) {
        try {
            return Long.parseLong(text);
        } catch (NumberFormatException exception) {
            return 0;
        }
    }

    // ---------- Steam account

    private void refreshAccount() {
        handler.post(() -> {
            String saved = steam.savedAccount();
            account.setText(saved != null ? "Steam: " + saved + " (sign out)" : "Steam sign-in");
        });
    }

    private void accountClicked() {
        if (busy)
            return;
        if (steam.savedAccount() != null) {
            new AlertDialog.Builder(this)
                .setTitle("Sign out of Steam?")
                .setMessage("The launcher forgets this device's Steam sign-in. Installed maps stay.")
                .setPositiveButton("Sign out", (dialog, which) -> new Thread(() -> {
                    steam.signOut();
                    refreshAccount();
                    status("Signed out of Steam.");
                }, "steam-sign-out").start())
                .setNegativeButton("Cancel", null)
                .show();
        } else {
            askCredentials(null);
        }
    }

    /**
     * the account name and password, typed by the player; then (worker) the
     * sign-in and next. Called when nothing is busy: the sign-in makes it busy,
     * and next (a download) ends it.
     */
    private void askCredentials(Runnable next) {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(dp(20), dp(8), dp(20), dp(8));
        TextView note = new TextView(this);
        note.setText("Sign in with your own Steam account (it must own Halo: The Master Chief Collection). Steam "
            + "then asks you to approve it in the Steam app on your phone, or for a Steam Guard code. The launcher "
            + "keeps only Steam's sign-in token on this device, never your password.");
        form.addView(note);
        EditText name = new EditText(this);
        name.setHint("Steam account name");
        name.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD);
        form.addView(name);
        EditText password = new EditText(this);
        password.setHint("Password");
        password.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        form.addView(password);
        new AlertDialog.Builder(this)
            .setTitle("Steam sign-in")
            .setView(form)
            .setPositiveButton("Sign in", (dialog, which) -> {
                String account = name.getText().toString().trim();
                String secret = password.getText().toString();
                password.setText("");
                if (account.isEmpty() || secret.isEmpty() || busy)
                    return;
                setBusy(true);
                new Thread(() -> {
                    try {
                        steam.signIn(account, secret, ui());
                        refreshAccount();
                        if (next != null)
                            next.run();
                        else
                            setBusy(false);
                    } catch (Exception exception) {
                        status("Steam sign-in failed: " + message(exception));
                        setBusy(false);
                    }
                }, "steam-sign-in").start();
            })
            .setNegativeButton("Cancel", null)
            .show();
    }

    private SteamWorkshop.Ui ui() {
        return new SteamWorkshop.Ui() {
            @Override
            public void status(String text) {
                WorkshopActivity.this.status(text);
            }

            @Override
            public String code(String prompt) {
                CompletableFuture<String> answer = new CompletableFuture<>();
                handler.post(() -> {
                    EditText code = new EditText(WorkshopActivity.this);
                    code.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);
                    new AlertDialog.Builder(WorkshopActivity.this)
                        .setTitle("Steam Guard")
                        .setMessage(prompt)
                        .setView(code)
                        .setCancelable(false)
                        .setPositiveButton("OK", (dialog, which) -> answer.complete(code.getText().toString().trim()))
                        .setNegativeButton("Cancel", (dialog, which) -> answer.complete(null))
                        .show();
                });
                try {
                    return answer.get();
                } catch (Exception exception) {
                    return null;
                }
            }
        };
    }

    private static String message(Throwable error) {
        while (error.getCause() != null && (error.getMessage() == null || error instanceof java.util.concurrent.ExecutionException))
            error = error.getCause();
        return error.getMessage() != null ? error.getMessage() : error.getClass().getSimpleName();
    }

    // ---------- downloading

    private void downloadClicked() {
        long id = pageItem;
        if (busy || id == 0)
            return;
        setBusy(true);
        new Thread(() -> {
            try {
                List<Long> items = SteamWorkshop.collection(id);
                boolean isCollection = !items.isEmpty();
                if (!isCollection)
                    items.add(id);
                status(isCollection ? "A collection of " + items.size() + " items." : "Reading the item...");
                if (!steam.signedIn() && !steam.signInSaved(ui())) {
                    status("Sign in to Steam to download.");
                    setBusy(false);
                    handler.post(() -> askCredentials(() -> downloadAll(items)));
                    return;
                }
                downloadAll(items);
            } catch (Exception exception) {
                status("Download failed: " + message(exception));
                setBusy(false);
            }
        }, "workshop-download").start();
    }

    /** (worker) each item downloaded and installed in turn; a summary at the end */
    private void downloadAll(List<Long> items) {
        List<String> done = new ArrayList<>(), refused = new ArrayList<>();
        for (long item : items) {
            try {
                done.add(downloadOne(item));
            } catch (Exception exception) {
                refused.add(message(exception));
                RunLog.line("Workshop: item " + item + " not installed: " + message(exception));
            }
        }
        StringBuilder summary = new StringBuilder();
        if (!done.isEmpty())
            summary.append("Installed: ").append(String.join("; ", done)).append(". ");
        if (!refused.isEmpty())
            summary.append("Not installed: ").append(String.join("; ", refused)).append(". ");
        summary.append("In the game: New Game or Multiplayer, map kind MCC SINGLEPLAYER / MCC MULTIPLAYER.");
        status(summary.toString());
        setBusy(false);
        handler.post(() -> {
            if (managerView.getVisibility() == View.VISIBLE)
                fillManager();
        });
    }

    /** (worker) one item: its details, a download into the cache, its Halo 1 maps installed */
    private String downloadOne(long id) throws Exception {
        SteamWorkshop.Item item = SteamWorkshop.details(id);
        if (item.result != 1)
            throw new java.io.IOException("item " + id + " is not available (Steam result " + item.result + ")");
        if (item.appId != SteamWorkshop.MCC_APP_ID)
            throw new java.io.IOException("\"" + item.title + "\" is not an MCC Workshop item");
        File cache = new File(getCacheDir(), "workshop/" + id);
        MccMapsDelete.tree(cache);
        status("Downloading \"" + item.title + "\" (" + megabytes(item.fileSize) + ")...");
        progress(0f);
        steam.download(id, cache, (fraction, text) -> {
            if (fraction >= 0)
                progress(fraction);
            if (text != null && !text.isEmpty())
                status("Downloading \"" + item.title + "\": " + text);
        });
        status("Installing \"" + item.title + "\"...");
        try {
            MccMaps.Installed installed = maps.installWorkshop(cache, id, item.title, item.timeUpdated);
            return "\"" + item.title + "\" (" + installed.levels + " maps"
                + (installed.skipped.isEmpty() ? "" : ", " + installed.skipped.size() + " files skipped") + ")";
        } finally {
            MccMapsDelete.tree(cache);
        }
    }

    private static String megabytes(long bytes) {
        return bytes > 0 ? String.format(Locale.ROOT, "%.1f MB", bytes / 1048576.0) : "size unknown";
    }

    // ---------- the installed maps

    private void showManager() {
        web.setVisibility(View.GONE);
        managerView.setVisibility(View.VISIBLE);
        fillManager();
    }

    private void fillManager() {
        managerList.removeAllViews();
        TextView title = new TextView(this);
        title.setText("INSTALLED MCC MAPS");
        title.setTextColor(HALO_BLUE);
        title.setTextSize(TypedValue.COMPLEX_UNIT_SP, 18);
        managerList.addView(title);
        TextView summary = new TextView(this);
        summary.setTextColor(Color.rgb(170, 178, 186));
        summary.setText(maps.summary() + " Disabled maps stay installed but are not listed in the game. Deleting "
            + "a map keeps your saves; a checkpoint on a deleted map continues once the map is back.");
        managerList.addView(summary);
        List<MccMaps.Package> packages = maps.packages();
        if (packages.isEmpty()) {
            TextView none = new TextView(this);
            none.setTextColor(Color.rgb(200, 205, 210));
            none.setText("None yet: download maps from the Workshop, or import a folder in the launcher.");
            managerList.addView(none);
        }
        for (MccMaps.Package item : packages) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.VERTICAL);
            row.setPadding(0, dp(10), 0, dp(4));
            TextView name = new TextView(this);
            name.setTextColor(item.enabled ? Color.WHITE : Color.rgb(140, 145, 150));
            name.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
            name.setText(item.title + (item.enabled ? "" : "  (disabled)"));
            row.addView(name);
            TextView detail = new TextView(this);
            detail.setTextColor(Color.rgb(170, 178, 186));
            detail.setText(item.levels + " maps, " + megabytes(item.bytes) + " — folder " + item.name
                + (item.workshopId != 0 ? " — Workshop " + item.workshopId : " — imported"));
            row.addView(detail);
            LinearLayout actions = new LinearLayout(this);
            actions.setOrientation(LinearLayout.HORIZONTAL);
            HorizontalScrollView actionScroll = new HorizontalScrollView(this);
            actionScroll.addView(actions);
            row.addView(actionScroll);
            button(actions, item.enabled ? "Disable" : "Enable").setOnClickListener(v -> {
                try {
                    maps.setEnabled(item, !item.enabled);
                    status((item.enabled ? "Disabled " : "Enabled ") + item.title + ".");
                } catch (Exception exception) {
                    status(message(exception));
                }
                fillManager();
            });
            button(actions, "Delete").setOnClickListener(v -> new AlertDialog.Builder(this)
                .setTitle("Delete " + item.title + "?")
                .setMessage("Deletes its maps and resource files (" + megabytes(item.bytes) + "). Your saves are kept.")
                .setPositiveButton("Delete", (dialog, which) -> {
                    try {
                        maps.delete(item);
                        status("Deleted " + item.title + ".");
                    } catch (Exception exception) {
                        status(message(exception));
                    }
                    fillManager();
                })
                .setNegativeButton("Keep", null)
                .show());
            if (item.workshopId != 0) {
                button(actions, "Check for update").setOnClickListener(v -> checkUpdate(item));
                button(actions, "Workshop page").setOnClickListener(v ->
                    showBrowser("https://steamcommunity.com/sharedfiles/filedetails/?id=" + item.workshopId));
            }
            managerList.addView(row);
        }
    }

    private void checkUpdate(MccMaps.Package item) {
        if (busy)
            return;
        setBusy(true);
        new Thread(() -> {
            try {
                SteamWorkshop.Item latest = SteamWorkshop.details(item.workshopId);
                if (latest.timeUpdated <= item.workshopUpdated) {
                    status(item.title + " is up to date.");
                    setBusy(false);
                    return;
                }
                status(item.title + " has an update: downloading it...");
                List<Long> one = new ArrayList<>();
                one.add(item.workshopId);
                if (!steam.signedIn() && !steam.signInSaved(ui())) {
                    status("Sign in to Steam to download the update.");
                    setBusy(false);
                    handler.post(() -> askCredentials(() -> downloadAll(one)));
                    return;
                }
                downloadAll(one);
            } catch (Exception exception) {
                status("Update check failed: " + message(exception));
                setBusy(false);
            }
        }, "workshop-update").start();
    }

    /** a folder tree deleted (the download cache) */
    static final class MccMapsDelete {
        static void tree(File file) {
            File[] inner = file.listFiles();
            if (inner != null)
                for (File each : inner)
                    tree(each);
            file.delete();
        }
    }
}
