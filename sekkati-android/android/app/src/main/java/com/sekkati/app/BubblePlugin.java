package com.sekkati.app;

import android.annotation.SuppressLint;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.Settings;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * Floating control over other apps (e.g. Google Maps), like a screen-recorder bubble:
 * a draggable app-icon head, an alert pill next to it, and a row of quick buttons that opens on tap.
 * Button taps are sent to the web layer as "action" events ({id}).
 */
@CapacitorPlugin(name = "Bubble")
public class BubblePlugin extends Plugin {
    private static final String[][] BUTTONS = {
            {"voice", "🎤\nقول"}, {"radar", "📷\nرادار"}, {"toll", "💳\nكارتة"}, {"checkpoint", "🚓\nلجنة"},
            {"mute", "🔊\nصوت"}, {"stop", "■\nإنهاء"}, {"open", "↗\nسكّتي"}};

    private final Handler main = new Handler(Looper.getMainLooper());
    private WindowManager wm;
    private WindowManager.LayoutParams lp;
    private LinearLayout root, menu;
    private ImageView head;
    private TextView pill, muteBtn;
    private boolean muted;

    private static BubblePlugin self;
    private static int lastX = -1, lastY = -1;

    @Override
    public void load() { self = this; }

    /** Called by VoiceActivity with the recognised text (or null plus a reason). */
    static void deliverVoice(String text, String error) {
        if (self == null) return;
        JSObject d = new JSObject();
        d.put("text", text == null ? "" : text);
        if (error != null) d.put("error", error);
        self.notifyListeners("voice", d);
    }

    /** Opens the voice-input dialog over the current screen (works on top of Google Maps). */
    @PluginMethod
    public void voice(PluginCall call) {
        startVoice();
        call.resolve();
    }

    private void startVoice() {
        Intent i = new Intent(app(), VoiceActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_NO_ANIMATION);
        app().startActivity(i);
    }

    private Context app() { return getContext().getApplicationContext(); }

    private boolean allowed() {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.M || Settings.canDrawOverlays(app());
    }

    @PluginMethod
    public void canDraw(PluginCall call) {
        JSObject r = new JSObject();
        r.put("value", allowed());
        call.resolve(r);
    }

    @PluginMethod
    public void requestDraw(PluginCall call) {
        if (!allowed()) {
            Intent i = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + app().getPackageName()));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            app().startActivity(i);
        }
        call.resolve();
    }

    /** Opens Android's text-to-speech settings so the user can pick Google's engine / download a better Arabic voice. */
    /** True when Android won't put the app to sleep for battery saving (background GPS keeps going). */
    @PluginMethod
    public void batteryOk(PluginCall call) {
        JSObject r = new JSObject();
        boolean ok = true;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            PowerManager pm = (PowerManager) app().getSystemService(Context.POWER_SERVICE);
            ok = pm == null || pm.isIgnoringBatteryOptimizations(app().getPackageName());
        }
        r.put("value", ok);
        call.resolve(r);
    }

    /** Asks the user to exempt the app from battery optimisation; falls back to the settings list. */
    @SuppressLint("BatteryLife")
    @PluginMethod
    public void requestBattery(PluginCall call) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            try {
                Intent i = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:" + app().getPackageName()));
                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                app().startActivity(i);
            } catch (Exception e) {
                try {
                    Intent i = new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS);
                    i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    app().startActivity(i);
                } catch (Exception ignored) { }
            }
        }
        call.resolve();
    }

    @PluginMethod
    public void openTtsSettings(PluginCall call) {
        Intent i = new Intent("com.android.settings.TTS_SETTINGS");
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try { app().startActivity(i); } catch (Exception e) {
            Intent s = new Intent(Settings.ACTION_SETTINGS);
            s.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            app().startActivity(s);
        }
        call.resolve();
    }

    @PluginMethod
    public void show(PluginCall call) {
        final String text = call.getString("text", "");
        final String level = call.getString("level", "info");
        final boolean m = Boolean.TRUE.equals(call.getBoolean("muted", false));
        main.post(() -> {
            if (!allowed()) return;
            ensure();
            boolean alert = "warn".equals(level) || "danger".equals(level);
            pill.setVisibility(alert && !text.isEmpty() ? View.VISIBLE : View.GONE);
            pill.setText(text);
            ((GradientDrawable) pill.getBackground()).setColor("danger".equals(level) ? Color.parseColor("#F2E5394F") : Color.parseColor("#F2F5C451"));
            pill.setTextColor("danger".equals(level) ? Color.WHITE : Color.parseColor("#1a1a1a"));
            ((GradientDrawable) head.getBackground()).setStroke(dp(3), Color.parseColor("danger".equals(level) ? "#FF5A6E" : alert ? "#F5C451" : "#5FD3A0"));
            setMuted(m);
        });
        call.resolve();
    }

    @PluginMethod
    public void hide(PluginCall call) {
        main.post(this::remove);
        call.resolve();
    }

    @Override
    protected void handleOnDestroy() {
        main.post(this::remove);
    }

    private int dp(int v) {
        return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, app().getResources().getDisplayMetrics());
    }

    private GradientDrawable round(int color, float radiusDp) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp((int) radiusDp));
        return g;
    }

    private void setMuted(boolean m) {
        muted = m;
        if (muteBtn != null) muteBtn.setText(m ? "🔇\nصامت" : "🔊\nصوت");
    }

    private void emit(String id) {
        JSObject d = new JSObject();
        d.put("id", id);
        notifyListeners("action", d);
    }

    @SuppressLint("ClickableViewAccessibility")
    private void ensure() {
        if (root != null) return;
        wm = (WindowManager) app().getSystemService(Context.WINDOW_SERVICE);
        root = new LinearLayout(app());
        root.setOrientation(LinearLayout.VERTICAL);

        LinearLayout top = new LinearLayout(app());
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);
        head = new ImageView(app());
        head.setImageResource(app().getApplicationInfo().icon);
        GradientDrawable ring = new GradientDrawable();
        ring.setShape(GradientDrawable.OVAL);
        ring.setColor(Color.parseColor("#050506"));
        ring.setStroke(dp(3), Color.parseColor("#5FD3A0"));
        head.setBackground(ring);
        head.setPadding(dp(4), dp(4), dp(4), dp(4));
        head.setElevation(dp(6));
        top.addView(head, new LinearLayout.LayoutParams(dp(52), dp(52)));
        pill = new TextView(app());
        pill.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        pill.setPadding(dp(12), dp(8), dp(12), dp(8));
        pill.setMaxWidth(dp(230));
        pill.setBackground(round(Color.parseColor("#F2F5C451"), 18));
        pill.setElevation(dp(6));
        pill.setVisibility(View.GONE);
        LinearLayout.LayoutParams pl = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        pl.setMarginStart(dp(8));
        top.addView(pill, pl);
        root.addView(top);

        menu = new LinearLayout(app());
        menu.setOrientation(LinearLayout.HORIZONTAL);
        menu.setPadding(dp(5), dp(5), dp(5), dp(5));
        menu.setBackground(round(Color.parseColor("#F2121214"), 22));
        menu.setElevation(dp(8));
        menu.setVisibility(View.GONE);
        for (String[] b : BUTTONS) {
            TextView t = new TextView(app());
            t.setText(b[1]);
            t.setGravity(Gravity.CENTER);
            t.setTextColor(Color.WHITE);
            t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
            t.setLineSpacing(0, 1.05f);
            t.setBackground(round(Color.parseColor("#2A2A2E"), 14));
            LinearLayout.LayoutParams bl = new LinearLayout.LayoutParams(dp(44), dp(54));
            bl.setMargins(dp(2), 0, dp(2), 0);
            final String id = b[0];
            t.setOnClickListener(v -> {
                if ("open".equals(id)) openApp();
                else if ("voice".equals(id)) startVoice();
                else if ("mute".equals(id)) setMuted(!muted);
                emit(id);
                if (!"mute".equals(id)) menu.setVisibility(View.GONE);
            });
            if ("mute".equals(id)) muteBtn = t;
            menu.addView(t, bl);
        }
        LinearLayout.LayoutParams ml = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        ml.topMargin = dp(8);
        root.addView(menu, ml);

        int type = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                : WindowManager.LayoutParams.TYPE_PHONE;
        lp = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT, type,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        lp.gravity = Gravity.TOP | Gravity.START;
        lp.x = lastX >= 0 ? lastX : dp(10);   // بيرجع مكان ما السواق ساب الفقاعة
        lp.y = lastY >= 0 ? lastY : dp(150);
        head.setOnTouchListener(new View.OnTouchListener() {
            private int sx, sy;
            private float tx, ty;
            private boolean moved;

            @Override
            public boolean onTouch(View v, MotionEvent e) {
                switch (e.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        sx = lp.x; sy = lp.y; tx = e.getRawX(); ty = e.getRawY(); moved = false;
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        int dx = (int) (e.getRawX() - tx), dy = (int) (e.getRawY() - ty);
                        if (Math.abs(dx) > dp(6) || Math.abs(dy) > dp(6)) moved = true;
                        lp.x = sx + dx; lp.y = sy + dy;
                        wm.updateViewLayout(root, lp);
                        return true;
                    case MotionEvent.ACTION_UP:
                        lastX = lp.x; lastY = lp.y;
                        if (!moved) menu.setVisibility(menu.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE);
                        return true;
                }
                return false;
            }
        });
        wm.addView(root, lp);
    }

    private void openApp() {
        Intent i = app().getPackageManager().getLaunchIntentForPackage(app().getPackageName());
        if (i == null) return;
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        app().startActivity(i);
    }

    private void remove() {
        if (root != null && wm != null) {
            try { wm.removeView(root); } catch (Exception ignored) { }
        }
        root = null; menu = null; head = null; pill = null; muteBtn = null;
    }
}
