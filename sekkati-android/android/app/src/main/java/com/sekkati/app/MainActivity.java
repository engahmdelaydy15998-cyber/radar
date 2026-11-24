package com.sekkati.app;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    /** Set by the "أسجّل؟" drive notification: open and start recording. */
    static final String EXTRA_REC = "sekkati_rec";

    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(BubblePlugin.class);
        super.onCreate(savedInstanceState);
        // The WebView follows the phone's font-size setting by default, which blows up every button; keep the designed sizes.
        getBridge().getWebView().getSettings().setTextZoom(100);
        // Android 13+: without this the background-location notification can't show, and tracking stops in the background.
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
        }
        takeShare(getIntent());
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] res) {
        super.onRequestPermissionsResult(code, perms, res);
        if (code == DriveReceiver.REQ) DriveReceiver.register(this);
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        takeShare(intent);
    }

    /** "Share" from Google Maps (text with a maps.app.goo.gl link) or a tapped maps / geo: link → hand it to the web layer. */
    private void takeShare(Intent i) {
        if (i == null) return;
        if (i.getBooleanExtra(EXTRA_REC, false)) {
            i.removeExtra(EXTRA_REC);
            DriveReceiver.cancel(this);
            BubblePlugin.deliverShared("sekkati:rec");
            return;
        }
        if (Intent.ACTION_SEND.equals(i.getAction())) {
            String t = i.getStringExtra(Intent.EXTRA_TEXT);
            String s = i.getStringExtra(Intent.EXTRA_SUBJECT);
            BubblePlugin.deliverShared((s != null && t != null && !t.contains(s) ? s + "\n" : "") + (t == null ? "" : t));
        } else if (Intent.ACTION_VIEW.equals(i.getAction()) && i.getData() != null) {
            BubblePlugin.deliverShared(i.getData().toString());
        }
    }
}
