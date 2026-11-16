// Shows the scorer two things on the test pages:
//   A. where the listener is in the list, under the test name in the header:
//      "List 1 · Sentence 3 of 20 · 10 dB SNR"
//   B. how many words of the current audio are scored, under All / None:
//      "5 of 7 words scored · 4 correct"
// Display only. It reads the audio file name the page is already playing and
// the radio buttons already on the page; it does not change what is sent.
// Load it after record.js.
(function () {
  "use strict";

  const state = { levels: null, trial: null };

  // "audio/azbio_mandarin/AzBio_Mandarin_10DBSNR_List1_Sentence-03.wav"
  //   -> {list: 1, unit: "Sentence", item: 3, condition: "10 dB SNR"}
  // Also: CNC_List1_Word1_Goose.wav, WIN_T6L1_Word1_Cool.wav,
  // List01Sentence01.wav, AzBio_Quiet_List1_Sentence-1.wav.
  function parseAudioName(url) {
    if (!url) return null;
    const name = decodeURIComponent(
        String(url).split(/[?#]/)[0].split("/").pop());
    const list = name.match(/List0*(\d+)/i) || name.match(/L0*(\d+)_/);
    const item = name.match(/(Sentence|Word)-?0*(\d+)/i);
    if (!list && !item) return null;
    const snr = name.match(/(-?\d+)\s*dB\s*SNR/i);
    return {
      list: list ? Number(list[1]) : null,
      unit: item ? item[1][0].toUpperCase() + item[1].slice(1).toLowerCase()
                 : null,
      item: item ? Number(item[2]) : null,
      condition: snr ? `${snr[1]} dB SNR`
                     : (/quiet/i.test(name) ? "Quiet" : null),
    };
  }

  function progressText(trial, levels) {
    if (!trial) return "";
    const parts = [];
    if (trial.list !== null) parts.push(`List ${trial.list}`);
    if (trial.item !== null) {
      parts.push(`${trial.unit} ${trial.item}` + (levels ? ` of ${levels}` : ""));
    }
    if (trial.condition) parts.push(trial.condition);
    return parts.join(" · ");
  }

  function element(id, parentSelector, tag) {
    let el = document.getElementById(id);
    if (el) return el;
    const parent = document.querySelector(parentSelector);
    if (!parent) return null;
    el = parent.appendChild(document.createElement(tag));
    el.id = id;
    el.setAttribute("aria-live", "polite");
    return el;
  }

  // A. ------------------------------------------------------------------
  function showProgress() {
    const el = element("trial-progress", "#project", "div");
    if (!el) return;
    el.textContent = progressText(state.trial, state.levels);
    el.classList.toggle("hidden", el.textContent === "");
  }

  function trialStarted(url) {
    state.trial = parseAudioName(url);
    showProgress();
  }

  // B. ------------------------------------------------------------------
  function counts() {
    const groups = Array.from(document.querySelectorAll(".options-case > div"));
    let scored = 0, correct = 0;
    for (const g of groups) {
      const on = g.querySelector(".annotation-on");
      const off = g.querySelector(".annotation-off");
      if (on && on.checked) { scored += 1; correct += 1; }
      else if (off && off.checked) scored += 1;
    }
    return { total: groups.length, scored, correct };
  }

  function showCount() {
    const el = element("scored-count", "#result-options", "div");
    if (!el) return;
    const { total, scored, correct } = counts();
    el.classList.toggle("hidden", total === 0);
    el.classList.toggle("complete", total > 0 && scored === total);
    const text = `${scored} of ${total} words scored` +
        (scored > 0 ? ` · ${correct} correct` : "");
    // only write when it changes: the observer below would see the write
    if (el.textContent !== text) el.textContent = text;
  }

  // Run after the page's own handlers (All / None set .checked directly,
  // which fires no change event).
  function later() { setTimeout(showCount, 0); }

  // Hooks into the page's classes from audio.js / record.js ----------------
  function hook() {
    if (typeof AudioPrefetch === "function") {
      const debug = AudioPrefetch.prototype.playback_debug;
      AudioPrefetch.prototype.playback_debug = function (url) {
        const res = debug.apply(this, arguments);
        trialStarted(this.get_real_url(url));
        return res;
      };
    }
    // `Audio` here is record.js's class, not the browser's Audio element.
    if (typeof Audio === "function" && Audio.prototype &&
        typeof Audio.prototype.load === "function" &&
        typeof AudioPrefetch === "function" &&
        Audio.prototype instanceof AudioPrefetch) {
      const load = Audio.prototype.load;
      Audio.prototype.load = function (data) {
        if (data && Number.isInteger(data.levels)) {
          state.levels = data.levels;
          showProgress();
        }
        return load.apply(this, arguments);
      };
    }
  }

  hook();

  window.addEventListener("load", () => {
    document.addEventListener("change", later, true);
    document.addEventListener("click", later);
    const aux = document.getElementById("aux-data");
    if (aux) {
      new MutationObserver(later).observe(aux, { childList: true, subtree: true });
    }
    showProgress();
    showCount();
  }, { passive: true });

  window.ScoringStatus = {
    parseAudioName, progressText, counts, trialStarted, showCount, state,
  };
})();
