/**
 * AudioPlayer — Lecteur WebAudio séquentiel (capsules + montants verbalisés)
 * avec crossfade de 25 ms et cache d'AudioBuffers en mémoire.
 */

export const AUDIO_CROSSFADE_SEC = 0.025;

export interface AudioSequenceItem {
  clip_id: string;
  audio_url: string;
  label: string;
  duration_estimate_ms: number;
}

export interface AudioSequenceResponse {
  target_lang: string;
  full_transcript: string;
  total_duration_estimate_ms: number;
  items: AudioSequenceItem[];
}

export class AudioPlayer {
  private ctx: AudioContext | null = null;
  private bufferCache = new Map<string, AudioBuffer>();
  private currentSources: AudioBufferSourceNode[] = [];
  private active = false;

  private getAudioContext(): AudioContext {
    if (!this.ctx || this.ctx.state === "closed") {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === "suspended") {
      void this.ctx.resume();
    }
    return this.ctx;
  }

  stop(): void {
    this.active = false;
    for (const src of this.currentSources) {
      try {
        src.stop();
        src.disconnect();
      } catch {
        // Ignored
      }
    }
    this.currentSources = [];
  }

  isPlaying(): boolean {
    return this.active;
  }

  async fetchBuffer(url: string): Promise<AudioBuffer | null> {
    const ctx = this.getAudioContext();
    if (this.bufferCache.has(url)) {
      return this.bufferCache.get(url)!;
    }
    try {
      const fullUrl = url.startsWith("http") ? url : `http://localhost:8000${url}`;
      const res = await fetch(fullUrl);
      if (!res.ok) return null;
      const arrayBuf = await res.arrayBuffer();
      const audioBuf = await ctx.decodeAudioData(arrayBuf);
      this.bufferCache.set(url, audioBuf);
      return audioBuf;
    } catch {
      return null;
    }
  }

  async playSequence(items: AudioSequenceItem[]): Promise<void> {
    this.stop();
    if (!items || items.length === 0) return;

    this.active = true;
    const ctx = this.getAudioContext();

    // Preload all buffers concurrently
    const buffers = await Promise.all(items.map((it) => this.fetchBuffer(it.audio_url)));
    if (!this.active) return;

    let startTime = ctx.currentTime + 0.05;

    for (const buf of buffers) {
      if (!buf || !this.active) continue;

      const source = ctx.createBufferSource();
      source.buffer = buf;

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(1.0, startTime);
      // Subtle 25ms crossfade fade-out
      const endTime = startTime + buf.duration;
      gain.gain.setValueAtTime(1.0, Math.max(startTime, endTime - AUDIO_CROSSFADE_SEC));
      gain.gain.linearRampToValueAtTime(0.01, endTime);

      source.connect(gain);
      gain.connect(ctx.destination);

      source.start(startTime);
      this.currentSources.push(source);

      // Overlap by 25ms for natural human speech flow
      startTime = Math.max(ctx.currentTime, endTime - AUDIO_CROSSFADE_SEC);
    }

    const totalDurationSec = startTime - ctx.currentTime;
    window.setTimeout(() => {
      if (this.active) {
        this.active = false;
        this.currentSources = [];
      }
    }, Math.max(200, totalDurationSec * 1000 + 100));
  }
}
