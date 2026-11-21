package com.sekkati.app;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.os.Bundle;
import android.speech.RecognizerIntent;

import java.util.ArrayList;

/**
 * Transparent, task-less activity that shows the phone's voice-input dialog on top of whatever app is
 * in front (e.g. Google Maps) and hands the recognised text back to the web layer via BubblePlugin.
 */
public class VoiceActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        i.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ar-EG");
        i.putExtra(RecognizerIntent.EXTRA_PROMPT, "قول: هنا رادار، كارتة، لجنة، زحمة، مقفول...");
        i.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);
        try {
            startActivityForResult(i, 1);
        } catch (ActivityNotFoundException e) {
            BubblePlugin.deliverVoice(null, "no-recognizer");
            finish();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        String text = null;
        if (resultCode == RESULT_OK && data != null) {
            ArrayList<String> r = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (r != null && !r.isEmpty()) text = r.get(0);
        }
        BubblePlugin.deliverVoice(text, text == null ? "no-speech" : null);
        finish();
        overridePendingTransition(0, 0);
    }
}
