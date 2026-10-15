package com.halo.decomp;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * Test71: a mod's archive downloaded in the launcher's own browser, from a
 * host that refuses anything but a browser (moddb.com: its pages and
 * mirrors answer other clients 403). The page that starts the download is
 * opened here; when the host hands the browser the file, the launcher takes
 * the download over with the browser's own session (its cookies and user
 * agent), resuming a partial one, and keeps it only when it is exactly the
 * host's file (its size and MD5). The owner: every mod installs from the
 * launcher (ModInstaller.Mod.webArchive).
 */
public class ModDownloadActivity extends Activity {
    static final String EXTRA_START = "start";
    static final String EXTRA_PAGE = "page";
    static final String EXTRA_NAME = "name";
    static final String EXTRA_SIZE = "size";
    static final String EXTRA_MD5 = "md5";
    static final String EXTRA_TARGET = "target";

    private final Handler handler = new Handler(Looper.getMainLooper());
    private WebView web;
    private TextView status;
    private ProgressBar progress;
    private String name, md5;
    private long size;
    private File target;
    private volatile boolean downloading, cancelled;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        Intent intent = getIntent();
        name = intent.getStringExtra(EXTRA_NAME);
        md5 = intent.getStringExtra(EXTRA_MD5);
        size = intent.getLongExtra(EXTRA_SIZE, -1);
        String targetPath = intent.getStringExtra(EXTRA_TARGET);
        String start = intent.getStringExtra(EXTRA_START), page = intent.getStringExtra(EXTRA_PAGE);
        if (name == null || md5 == null || size <= 0 || targetPath == null || start == null) {
            finish();
            return;
        }
        target = new File(targetPath);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(12, 16, 20));
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        root.addView(bar);
        button(bar, "Start the download again").setOnClickListener(v -> { if (!downloading) web.loadUrl(start); });
        if (page != null)
            button(bar, "The mod's page").setOnClickListener(v -> { if (!downloading) web.loadUrl(page); });
        button(bar, "Cancel").setOnClickListener(v -> { cancelled = true; setResult(RESULT_CANCELED); finish(); });
        status = new TextView(this);
        status.setTextColor(Color.rgb(200, 205, 210));
        status.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        int pad = (int) (10 * getResources().getDisplayMetrics().density);
        status.setPadding(pad, pad / 2, pad, pad / 2);
        status.setText("Opening " + Uri.parse(start).getHost() + " to download " + name + " ("
            + ModInstaller.megabytes(size) + "). If the page asks, tap its Download button.");
        root.addView(status);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(1000);
        root.addView(progress, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, pad));

        web = new WebView(this);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, true);
        // (pages and the host's mirror redirects stay in this browser)
        web.setWebViewClient(new WebViewClient());
        web.setDownloadListener((url, agent, disposition, mime, length) -> {
            if (downloading)
                return;
            if (length > 0 && length != size) {
                status.setText("The host offered a file of " + ModInstaller.megabytes(length) + ", not the "
                    + ModInstaller.megabytes(size) + " " + name + ": not taken. Use Start the download again.");
                return;
            }
            downloading = true;
            String cookies = CookieManager.getInstance().getCookie(url);
            new Thread(() -> download(url, agent, cookies, web.getUrl()), "mod-web-download").start();
        });
        root.addView(web, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        setContentView(root);
        web.loadUrl(start);
    }

    private Button button(LinearLayout bar, String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setAllCaps(false);
        bar.addView(button);
        return button;
    }

    private void report(String text, int permille) {
        handler.post(() -> {
            status.setText(text);
            if (permille >= 0)
                progress.setProgress(permille);
        });
    }

    /** The file, with the browser's session; resumed from a partial one. */
    private void download(String url, String agent, String cookies, String referer) {
        File partial = new File(target.getPath() + ".part");
        try {
            File directory = target.getParentFile();
            if (directory != null && !directory.isDirectory() && !directory.mkdirs())
                throw new IOException("cannot make " + directory);
            long have = partial.isFile() ? partial.length() : 0;
            if (have > size) {
                partial.delete();
                have = 0;
            }
            HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
            connection.setInstanceFollowRedirects(true);
            connection.setConnectTimeout(30000);
            connection.setReadTimeout(60000);
            if (agent != null) connection.setRequestProperty("User-Agent", agent);
            if (cookies != null) connection.setRequestProperty("Cookie", cookies);
            if (referer != null) connection.setRequestProperty("Referer", referer);
            if (have > 0) connection.setRequestProperty("Range", "bytes=" + have + "-");
            int code = connection.getResponseCode();
            if (code == 200) have = 0;
            else if (code != 206) throw new IOException("the host answered " + code
                + (code == 403 ? " (it refused the launcher's download; import your own copy instead)" : ""));
            try (InputStream in = connection.getInputStream();
                 OutputStream out = new FileOutputStream(partial, have > 0)) {
                byte[] buffer = new byte[1 << 16];
                long written = have, reported = 0;
                int read;
                while (!cancelled && (read = in.read(buffer)) > 0) {
                    out.write(buffer, 0, read);
                    written += read;
                    if (written > size) throw new IOException("the download is larger than " + name);
                    if (written - reported > (4 << 20)) {
                        reported = written;
                        report("Downloading " + name + ": " + (written >> 20) + " of " + (size >> 20) + " MB",
                            (int) (written * 1000 / size));
                    }
                }
            } finally {
                connection.disconnect();
            }
            if (cancelled)
                return;
            report("Checking " + name + " (its size and MD5)...", 1000);
            if (!ModInstaller.archiveMatches(partial, size, md5)) {
                long length = partial.length();
                if (length >= size) partial.delete();
                throw new IOException(name + " is not the host's file (" + length + " bytes; size or MD5 differ)"
                    + (length < size ? "; the download stopped early: start it again to resume" : ""));
            }
            if (!partial.renameTo(target))
                throw new IOException("cannot keep " + target);
            handler.post(() -> {
                setResult(RESULT_OK, new Intent().putExtra(EXTRA_TARGET, target.getAbsolutePath()));
                finish();
            });
        } catch (Exception exception) {
            downloading = false;
            report("Download failed: " + exception.getMessage(), -1);
        }
    }

    @Override
    protected void onDestroy() {
        cancelled = true;
        if (web != null) web.destroy();
        super.onDestroy();
    }
}
