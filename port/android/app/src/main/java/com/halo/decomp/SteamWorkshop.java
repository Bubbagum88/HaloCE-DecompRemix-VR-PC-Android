package com.halo.decomp;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.Closeable;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

import in.dragonbra.javasteam.depotdownloader.DepotDownloader;
import in.dragonbra.javasteam.depotdownloader.IDownloadListener;
import in.dragonbra.javasteam.depotdownloader.data.DownloadItem;
import in.dragonbra.javasteam.depotdownloader.data.PubFileItem;
import in.dragonbra.javasteam.enums.EResult;
import in.dragonbra.javasteam.steam.authentication.AuthPollResult;
import in.dragonbra.javasteam.steam.authentication.AuthSessionDetails;
import in.dragonbra.javasteam.steam.authentication.IAuthenticator;
import in.dragonbra.javasteam.steam.handlers.steamapps.License;
import in.dragonbra.javasteam.steam.handlers.steamapps.callback.LicenseListCallback;
import in.dragonbra.javasteam.steam.handlers.steamuser.LogOnDetails;
import in.dragonbra.javasteam.steam.handlers.steamuser.SteamUser;
import in.dragonbra.javasteam.steam.handlers.steamuser.callback.LoggedOffCallback;
import in.dragonbra.javasteam.steam.handlers.steamuser.callback.LoggedOnCallback;
import in.dragonbra.javasteam.steam.steamclient.SteamClient;
import in.dragonbra.javasteam.steam.steamclient.callbackmgr.CallbackManager;
import in.dragonbra.javasteam.steam.steamclient.callbacks.ConnectedCallback;
import in.dragonbra.javasteam.steam.steamclient.callbacks.DisconnectedCallback;
import in.dragonbra.javasteam.steam.steamclient.configuration.SteamConfiguration;
import okhttp3.OkHttpClient;

/**
 * Test68: the Steam Workshop for Halo 1 MCC maps (WorkshopActivity).
 *
 * Browsing and an item's details are Steam's public web pages and Web API
 * (ISteamRemoteStorage GetPublishedFileDetails / GetCollectionDetails, no key,
 * no sign-in). Halo: The Master Chief Collection is a paid game, so Steam
 * hands its Workshop files only to a signed-in account that owns it: the
 * download signs in to the player's own Steam account (JavaSteam, MIT: the
 * Java port of SteamKit2), as Steam does on a new device: their account name
 * and password typed once, approved in the Steam app on their phone or with a
 * Steam Guard code. Only Steam's refresh token is kept (app-private
 * preferences), never the password; Sign out forgets it.
 */
final class SteamWorkshop implements Closeable {
    static final int MCC_APP_ID = 976730;
    private static final String PREFERENCES = "steam-workshop";

    /** What the download needs from the screen, called from a worker thread. */
    interface Ui {
        void status(String text);
        /** a Steam Guard code typed by the player (blocking; null: cancelled) */
        String code(String prompt);
    }

    /** One Workshop item's public details. */
    static final class Item {
        final long id;
        final int appId;
        final String title;
        final long timeUpdated, fileSize;
        final List<String> tags;
        final int result;

        Item(long id, int appId, String title, long timeUpdated, long fileSize, List<String> tags, int result) {
            this.id = id;
            this.appId = appId;
            this.title = title;
            this.timeUpdated = timeUpdated;
            this.fileSize = fileSize;
            this.tags = tags;
            this.result = result;
        }

        boolean halo1() {
            for (String tag : tags)
                if (tag.startsWith("Halo1"))
                    return true;
            return false;
        }
    }

    /**
     * One connection to Steam: its client, its callbacks pumped by its own
     * thread, and what it has answered. A new connection never shares these,
     * so a late callback of an old one cannot touch the new sign-in.
     */
    private static final class Session {
        final SteamClient client;
        final CallbackManager manager;
        final SteamUser user;
        final CompletableFuture<Void> connected = new CompletableFuture<>();
        final CompletableFuture<EResult> loggedOn = new CompletableFuture<>();
        final CompletableFuture<List<License>> licenses = new CompletableFuture<>();
        volatile boolean running = true;

        Session(SteamConfiguration configuration) {
            client = new SteamClient(configuration);
            manager = new CallbackManager(client);
            user = client.getHandler(SteamUser.class);
        }
    }

    private final SharedPreferences preferences;
    private volatile Session session;

    SteamWorkshop(Context context) {
        preferences = context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE);
    }

    /** the account signed in before (its refresh token kept), or null */
    String savedAccount() {
        String account = preferences.getString("account", null);
        return account != null && preferences.getString("token", null) != null ? account : null;
    }

    /** Forgets the refresh token and disconnects. */
    synchronized void signOut() {
        preferences.edit().remove("token").apply();
        disconnect();
    }

    // ---------- the public Web API

    private static String post(String api, String form) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) new URL("https://api.steampowered.com/" + api).openConnection();
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(30000);
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);
        connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        try (OutputStream out = connection.getOutputStream()) {
            out.write(form.getBytes(StandardCharsets.UTF_8));
        }
        if (connection.getResponseCode() != 200)
            throw new IOException("Steam answered " + connection.getResponseCode());
        try (InputStream in = connection.getInputStream()) {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int n;
            while ((n = in.read(buffer)) > 0) {
                bytes.write(buffer, 0, n);
                if (bytes.size() > 4 << 20)
                    throw new IOException("Steam's answer is too large");
            }
            return bytes.toString("UTF-8");
        } finally {
            connection.disconnect();
        }
    }

    /** An item's public details (title, app, last update, tags). */
    static Item details(long id) throws IOException {
        try {
            JSONObject response = new JSONObject(post("ISteamRemoteStorage/GetPublishedFileDetails/v1/",
                "itemcount=1&publishedfileids%5B0%5D=" + id)).getJSONObject("response");
            JSONObject file = response.getJSONArray("publishedfiledetails").getJSONObject(0);
            List<String> tags = new ArrayList<>();
            JSONArray tagArray = file.optJSONArray("tags");
            if (tagArray != null)
                for (int index = 0; index < tagArray.length(); index++)
                    tags.add(tagArray.getJSONObject(index).optString("tag"));
            return new Item(id, file.optInt("consumer_app_id"), file.optString("title", "Workshop item " + id),
                file.optLong("time_updated"), file.optLong("file_size"), tags, file.optInt("result"));
        } catch (org.json.JSONException exception) {
            throw new IOException("Steam's details of item " + id + " could not be read");
        }
    }

    /** a collection's items (none: not a collection) */
    static List<Long> collection(long id) throws IOException {
        List<Long> children = new ArrayList<>();
        try {
            JSONObject response = new JSONObject(post("ISteamRemoteStorage/GetCollectionDetails/v1/",
                "collectioncount=1&publishedfileids%5B0%5D=" + id)).getJSONObject("response");
            JSONArray details = response.optJSONArray("collectiondetails");
            JSONObject collection = details != null && details.length() > 0 ? details.getJSONObject(0) : null;
            JSONArray list = collection != null ? collection.optJSONArray("children") : null;
            if (list != null)
                for (int index = 0; index < list.length() && children.size() < 200; index++)
                    children.add(list.getJSONObject(index).optLong("publishedfileid"));
        } catch (org.json.JSONException exception) {
            throw new IOException("Steam's collection " + id + " could not be read");
        }
        return children;
    }

    // ---------- signing in (JavaSteam)

    /** the connection, made when there is none */
    private synchronized Session connect() throws Exception {
        Session current = session;
        if (current != null && current.running)
            return current;
        SteamConfiguration configuration = SteamConfiguration.create(builder -> builder.withHttpClient(
            new OkHttpClient.Builder()
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build()));
        Session made = new Session(configuration);
        made.manager.subscribe(ConnectedCallback.class, callback -> made.connected.complete(null));
        made.manager.subscribe(DisconnectedCallback.class, callback -> {
            IOException lost = new IOException("disconnected from Steam");
            made.connected.completeExceptionally(lost);
            made.loggedOn.completeExceptionally(lost);
            made.licenses.completeExceptionally(lost);
            made.running = false;
        });
        made.manager.subscribe(LoggedOnCallback.class, callback -> made.loggedOn.complete(callback.getResult()));
        made.manager.subscribe(LoggedOffCallback.class, callback ->
            made.loggedOn.completeExceptionally(new IOException("signed out of Steam: " + callback.getResult())));
        made.manager.subscribe(LicenseListCallback.class, callback -> {
            if (callback.getResult() == EResult.OK)
                made.licenses.complete(callback.getLicenseList());
            else
                made.licenses.completeExceptionally(new IOException("Steam did not list the account's games"));
        });
        session = made;
        new Thread(() -> {
            while (made.running)
                made.manager.runWaitCallbacks(500L);
        }, "steam-callbacks").start();
        made.client.connect();
        try {
            made.connected.get(30, TimeUnit.SECONDS);
        } catch (Exception exception) {
            disconnect();
            throw exception;
        }
        return made;
    }

    private synchronized void disconnect() {
        Session current = session;
        session = null;
        if (current != null) {
            current.running = false;
            current.client.disconnect();
        }
    }

    @Override
    public void close() {
        disconnect();
    }

    boolean signedIn() {
        Session current = session;
        return current != null && current.running && current.loggedOn.isDone() &&
            !current.loggedOn.isCompletedExceptionally() && current.loggedOn.getNow(EResult.Fail) == EResult.OK;
    }

    private static void logOn(Session session, String account, String token) throws Exception {
        LogOnDetails details = new LogOnDetails();
        details.setUsername(account);
        details.setAccessToken(token);
        details.setShouldRememberPassword(true);
        details.setLoginID(0x48434551); /* "QECH": beside the player's own Steam client */
        session.user.logOn(details);
        EResult result = session.loggedOn.get(45, TimeUnit.SECONDS);
        if (result != EResult.OK)
            throw new IOException("Steam refused the sign-in (" + result + ")");
    }

    /** Signs in with the refresh token kept from before; false when there is none or Steam refuses it. */
    synchronized boolean signInSaved(Ui ui) {
        String account = preferences.getString("account", null), token = preferences.getString("token", null);
        if (account == null || token == null)
            return false;
        try {
            ui.status("Signing in to Steam as " + account + "...");
            Session current = connect();
            if (!signedIn())
                logOn(current, account, token);
            return true;
        } catch (Exception exception) {
            preferences.edit().remove("token").apply();
            disconnect();
            ui.status("The saved Steam sign-in has expired: sign in again.");
            return false;
        }
    }

    /**
     * Signs in with the account name and password the player typed, approved
     * as Steam asks: in the Steam app (the phone's prompt) or with a Steam
     * Guard code. The password is used for this sign-in only, never kept.
     */
    synchronized void signIn(String account, String password, Ui ui) throws Exception {
        ui.status("Connecting to Steam...");
        disconnect();
        Session current = connect();
        AuthSessionDetails details = new AuthSessionDetails();
        details.username = account;
        details.password = password;
        details.deviceFriendlyName = "HaloCE Quest launcher";
        details.persistentSession = true;
        details.authenticator = new IAuthenticator() {
            @Override
            public CompletableFuture<String> getDeviceCode(boolean previousCodeWasIncorrect) {
                String code = ui.code((previousCodeWasIncorrect ? "That code was not right. " : "")
                    + "Steam Guard code from the Steam app:");
                return code != null ? CompletableFuture.completedFuture(code)
                    : failed(new IOException("sign-in cancelled"));
            }

            @Override
            public CompletableFuture<String> getEmailCode(String email, boolean previousCodeWasIncorrect) {
                String code = ui.code((previousCodeWasIncorrect ? "That code was not right. " : "")
                    + "Steam Guard code sent to " + (email != null ? email : "your email") + ":");
                return code != null ? CompletableFuture.completedFuture(code)
                    : failed(new IOException("sign-in cancelled"));
            }

            @Override
            public CompletableFuture<Boolean> acceptDeviceConfirmation() {
                ui.status("Approve the sign-in in the Steam app on your phone (Steam Guard)...");
                return CompletableFuture.completedFuture(true);
            }
        };
        ui.status("Signing in to Steam as " + account + "...");
        AuthPollResult result = current.client.getAuthentication().beginAuthSessionViaCredentials(details).get()
            .pollingWaitForResult().get();
        preferences.edit().putString("account", result.getAccountName())
            .putString("token", result.getRefreshToken()).apply();
        logOn(current, result.getAccountName(), result.getRefreshToken());
        ui.status("Signed in to Steam as " + result.getAccountName() + ".");
    }

    private static <T> CompletableFuture<T> failed(Throwable error) {
        CompletableFuture<T> future = new CompletableFuture<>();
        future.completeExceptionally(error);
        return future;
    }

    // ---------- downloading

    /** Progress of one download, 0 to 1. */
    interface Progress {
        void progress(float fraction, String text);
    }

    /**
     * Downloads a Workshop item's files (signed in) into folder. Steam lets an
     * account that owns Halo: The Master Chief Collection download its items.
     */
    void download(long id, File folder, Progress progress) throws Exception {
        Session current = session;
        if (current == null || !signedIn())
            throw new IOException("not signed in to Steam");
        List<License> owned = current.licenses.get(60, TimeUnit.SECONDS);
        final Throwable[] failure = new Throwable[1];
        try (DepotDownloader downloader = new DepotDownloader(current.client, owned, false)) {
            downloader.addListener(new IDownloadListener() {
                @Override public void onItemAdded(DownloadItem item) {}
                @Override public void onDownloadStarted(DownloadItem item) { progress.progress(0f, "Downloading..."); }
                @Override public void onDownloadCompleted(DownloadItem item) { progress.progress(1f, "Downloaded."); }
                @Override public void onDownloadFailed(DownloadItem item, Throwable error) { failure[0] = error; }
                @Override public void onStatusUpdate(String message) { progress.progress(-1f, message); }
                @Override public void onFileCompleted(int depotId, String fileName, float depotPercentComplete) {
                    progress.progress(depotPercentComplete / 100f, fileName);
                }
                @Override public void onChunkCompleted(int depotId, float depotPercentComplete, long compressedBytes,
                        long uncompressedBytes) {
                    progress.progress(depotPercentComplete / 100f, null);
                }
                @Override public void onDepotCompleted(int depotId, long compressedBytes, long uncompressedBytes) {}
            });
            downloader.add(new PubFileItem(MCC_APP_ID, id, false, folder.getAbsolutePath(), false, false));
            downloader.finishAdding();
            downloader.awaitCompletion();
        }
        if (failure[0] != null)
            throw new IOException("Steam's download failed: " + failure[0].getMessage()
                + " (the signed-in account must own Halo: The Master Chief Collection)");
    }

    static String form(String value) {
        try {
            return URLEncoder.encode(value, "UTF-8");
        } catch (java.io.UnsupportedEncodingException exception) {
            return value;
        }
    }
}
