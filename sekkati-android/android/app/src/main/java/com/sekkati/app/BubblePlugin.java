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
import android.provider.Settings;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.WindowManager;
import android.widget.TextView;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * Small floating bubble drawn over other apps (e.g. Google Maps) so radar/toll alerts stay visible
 * while another app is in front. Tapping it brings سكّتي back; dragging moves it.
 */
@CapacitorPlugin(name = "Bubble")
public class BubblePlugin extends Plugin {
    private final Handler main = new Handler(Looper.getMainLooper());
    private WindowManager wm;
    private WindowManager.LayoutParams lp;
    private TextView bubble;

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

    @PluginMethod
    public void show(PluginCall call) {
        final String text = call.getString("text", "");
        final String level = call.getString("level", "info");
        main.post(() -> {
            if (!allowed()) return;
            ensure();
            bubble.setText(text);
            ((GradientDrawable) bubble.getBackground()).setColor(colorOf(level));
            bubble.setTextColor("warn".equals(level) ? Color.parseColor("#1a1a1a") : Color.WHITE);
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

    private int colorOf(String level) {
        if ("danger".equals(level)) return Color.parseColor("#E6D93025");
        if ("warn".equals(level)) return Color.parseColor("#F2E9C46A");
        return Color.parseColor("#E6202124");
    }

    private int dp(int v) {
        return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, app().getResources().getDisplayMetrics());
    }

    @SuppressLint("ClickableViewAccessibility")
    private void ensure() {
        if (bubble != null) return;
        wm = (WindowManager) app().getSystemService(Context.WINDOW_SERVICE);
        bubble = new TextView(app());
        bubble.setTextSize(TypedValue.COMPLEX_UNIT_SP, 17);
        bubble.setPadding(dp(16), dp(10), dp(16), dp(10));
        bubble.setMaxWidth(dp(260));
        GradientDrawable bg = new GradientDrawable();
        bg.setCornerRadius(dp(22));
        bubble.setBackground(bg);
        bubble.setElevation(dp(6));
        int type = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                : WindowManager.LayoutParams.TYPE_PHONE;
        lp = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT, type,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        lp.gravity = Gravity.TOP | Gravity.START;
        lp.x = dp(12);
        lp.y = dp(140);
        bubble.setOnTouchListener(new android.view.View.OnTouchListener() {
            private int sx, sy;
            private float tx, ty;
            private boolean moved;

            @Override
            public boolean onTouch(android.view.View v, MotionEvent e) {
                switch (e.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        sx = lp.x; sy = lp.y; tx = e.getRawX(); ty = e.getRawY(); moved = false;
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        int dx = (int) (e.getRawX() - tx), dy = (int) (e.getRawY() - ty);
                        if (Math.abs(dx) > dp(6) || Math.abs(dy) > dp(6)) moved = true;
                        lp.x = sx + dx; lp.y = sy + dy;
                        wm.updateViewLayout(bubble, lp);
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (!moved) openApp();
                        return true;
                }
                return false;
            }
        });
        wm.addView(bubble, lp);
    }

    private void openApp() {
        Intent i = app().getPackageManager().getLaunchIntentForPackage(app().getPackageName());
        if (i == null) return;
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        app().startActivity(i);
    }

    private void remove() {
        if (bubble != null && wm != null) {
            try { wm.removeView(bubble); } catch (Exception ignored) { }
        }
        bubble = null;
    }
}
