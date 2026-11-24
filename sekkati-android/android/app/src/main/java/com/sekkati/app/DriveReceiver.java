package com.sekkati.app;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;

import com.google.android.gms.location.ActivityRecognition;
import com.google.android.gms.location.ActivityTransition;
import com.google.android.gms.location.ActivityTransitionEvent;
import com.google.android.gms.location.ActivityTransitionRequest;
import com.google.android.gms.location.ActivityTransitionResult;
import com.google.android.gms.location.DetectedActivity;

import java.util.ArrayList;
import java.util.List;

/**
 * "أسجّل؟" as soon as the phone starts driving: Google Play's Activity Recognition (very light on battery) tells us
 * IN_VEHICLE ENTER, and we post a notification with a "سجّل" button that opens Sekkati and starts recording.
 * Also re-registers after a reboot or an app update, since Android drops the registration then.
 */
public class DriveReceiver extends BroadcastReceiver {
    static final int REQ = 7;
    private static final String ACTION = "com.sekkati.app.DRIVE";
    private static final String CHANNEL = "drive";
    private static final int NOTE_ID = 4711;
    private static final long COOLDOWN_MS = 20 * 60 * 1000L;

    static SharedPreferences prefs(Context c) { return c.getSharedPreferences("sekkati_drive", Context.MODE_PRIVATE); }

    static boolean permitted(Context c) {
        return Build.VERSION.SDK_INT < 29
                || c.checkSelfPermission(Manifest.permission.ACTIVITY_RECOGNITION) == PackageManager.PERMISSION_GRANTED;
    }

    private static PendingIntent pending(Context c) {
        Intent i = new Intent(c, DriveReceiver.class).setAction(ACTION);
        int f = PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= 31 ? PendingIntent.FLAG_MUTABLE : 0);
        return PendingIntent.getBroadcast(c, 0, i, f);
    }

    static void register(Context c) {
        if (!permitted(c) || !prefs(c).getBoolean("ask", true)) return;
        List<ActivityTransition> t = new ArrayList<>();
        t.add(new ActivityTransition.Builder().setActivityType(DetectedActivity.IN_VEHICLE)
                .setActivityTransition(ActivityTransition.ACTIVITY_TRANSITION_ENTER).build());
        t.add(new ActivityTransition.Builder().setActivityType(DetectedActivity.IN_VEHICLE)
                .setActivityTransition(ActivityTransition.ACTIVITY_TRANSITION_EXIT).build());
        try {
            ActivityRecognition.getClient(c).requestActivityTransitionUpdates(new ActivityTransitionRequest(t), pending(c));
        } catch (SecurityException ignored) { }
    }

    static void unregister(Context c) {
        try { ActivityRecognition.getClient(c).removeActivityTransitionUpdates(pending(c)); } catch (SecurityException ignored) { }
        cancel(c);
    }

    static void cancel(Context c) {
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm != null) nm.cancel(NOTE_ID);
    }

    @Override
    public void onReceive(Context c, Intent intent) {
        String a = intent.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(a) || Intent.ACTION_MY_PACKAGE_REPLACED.equals(a)) { register(c); return; }
        if (!ACTION.equals(a) || !ActivityTransitionResult.hasResult(intent)) return;
        ActivityTransitionResult r = ActivityTransitionResult.extractResult(intent);
        if (r == null) return;
        for (ActivityTransitionEvent e : r.getTransitionEvents()) {
            if (e.getActivityType() != DetectedActivity.IN_VEHICLE) continue;
            if (e.getTransitionType() == ActivityTransition.ACTIVITY_TRANSITION_EXIT) cancel(c);
            else ask(c);
        }
    }

    private void ask(Context c) {
        SharedPreferences p = prefs(c);
        long now = System.currentTimeMillis();
        if (!p.getBoolean("ask", true) || p.getBoolean("rec", false) || now - p.getLong("last", 0) < COOLDOWN_MS) return;
        p.edit().putLong("last", now).apply();
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm == null) return;
        if (Build.VERSION.SDK_INT >= 26 && nm.getNotificationChannel(CHANNEL) == null) {
            NotificationChannel ch = new NotificationChannel(CHANNEL, "أسجّل الطريق؟", NotificationManager.IMPORTANCE_HIGH);
            ch.setDescription("بيسألك أول ما تبدأ تسوق");
            nm.createNotificationChannel(ch);
        }
        Intent open = new Intent(c, MainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP)
                .putExtra(MainActivity.EXTRA_REC, true);
        PendingIntent pi = PendingIntent.getActivity(c, 1, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(c, CHANNEL) : new Notification.Builder(c);
        b.setSmallIcon(c.getApplicationInfo().icon)
                .setContentTitle("بتسوق؟ أسجّل الطريق؟")
                .setContentText("دوس سجّل، وسكّتي هيسجّل وينبّهك قبل الرادارات")
                .setContentIntent(pi)
                .setAutoCancel(true)
                .setCategory(Notification.CATEGORY_NAVIGATION)
                .setPriority(Notification.PRIORITY_HIGH)
                .addAction(new Notification.Action.Builder(null, "سجّل", pi).build());
        try { nm.notify(NOTE_ID, b.build()); } catch (SecurityException ignored) { }
    }
}
