import { Viseme, WordOffset } from "@/types/avatar/conversation";
import { create } from "zustand";

// Convert base64 string to Blob
export const base64ToBlob = (base64: string, contentType: string): Blob => {
  // Remove any data URL prefix if present
  const base64Data = base64.replace(/^data:audio\/\w+;base64,/, '');
  
  try {
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length)
      .fill(null)
      .map((_, i) => byteCharacters.charCodeAt(i));
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: contentType });
  } catch (error) {
    console.error('Error converting base64 to Blob:', error);
    return new Blob([], { type: contentType });
  }
};

type AvatarSpeakState = {
  audio: HTMLAudioElement | null;
  content: string | null;
  viseme: Viseme[] | null;
  wordOffset: WordOffset[] | null; // You can specify this more strictly if you know the shape
  isPlaying: boolean;

  getPlaying: () => boolean;
  setAudio: (
    audioString: string,
    onAudioComplete?: () => void,
    speed?: number,
    stopAutoPlay?: boolean
  ) => void;
  togglePlayPause: () => void;
  pauseAudio: () => void;
  restartAudio: () => void;
  setViseme: (viseme: Viseme[]) => void;
  setContent: (content: string) => void;
  setWordOffset: (wordOffset: WordOffset[]) => void;
  reset: () => void;
};

export const useAvatarSpeak = create<AvatarSpeakState>((set, get) => ({
  audio: null,
  content: null,
  viseme: null,
  wordOffset: null,
  isPlaying: false,

  getPlaying: () => {
    const audio = get().audio;
    return audio !== null && !audio.paused;
  },

  setAudio: (
    audioString,
    onAudioComplete,
    speed = 1,
    stopAutoPlay = false
  ) => {
    const currentAudio = get().audio;
    if (currentAudio) {
      currentAudio.pause();
    }

    const audioBlob = base64ToBlob(audioString, "audio/mp3");
    const audioUrl = URL.createObjectURL(audioBlob);
    const newAudio = new Audio(audioUrl);

    newAudio.addEventListener("ended", () => {
      set({ isPlaying: false });
      if (typeof onAudioComplete === "function") {
        onAudioComplete();
      }
    });

    newAudio.playbackRate = speed;

    if (stopAutoPlay) return;

    newAudio
      .play()
      .then(() => {
        set({ isPlaying: true, audio: newAudio });
      })
      .catch((error) => {
        console.error("Error playing audio:", error);
      });
  },

  togglePlayPause: () => {
    const audio = get().audio;
    const isPlaying = get().isPlaying;

    if (audio) {
      if (audio.paused) {
        audio
          .play()
          .then(() => {
            set({ isPlaying: true });
          })
          .catch((error) => {
            console.error("Error playing audio:", error);
          });
      } else {
        audio.pause();
        set({ isPlaying: false });
      }
    }
  },

  pauseAudio: () => {
    const audio = get().audio;
    if (audio && !audio.paused) {
      audio.pause();
      set({ isPlaying: false });
    }
  },

  restartAudio: () => {
    const audio = get().audio;
    if (audio) {
      audio.currentTime = 0;
      audio
        .play()
        .then(() => {
          set({ isPlaying: true });
        })
        .catch((error) => {
          console.error("Error restarting audio:", error);
        });
    }
  },

  setViseme: (viseme) => set({ viseme }),
  setContent: (content) => set({ content }),
  setWordOffset: (wordOffset) => set({ wordOffset }),
  reset: () =>
    set({
      audio: null,
      content: null,
      viseme: null,
      wordOffset: null,
      isPlaying: false,
    }),
}));

export const visemeMap: Record<number, string> = {
  0: "viseme_sil",
  1: "viseme_aa",
  2: "viseme_aa",
  3: "viseme_O",
  4: "viseme_U",
  5: "viseme_CH",
  6: "viseme_RR",
  7: "viseme_U",
  8: "viseme_O",
  9: "viseme_U",
  10: "viseme_O",
  11: "viseme_aa",
  12: "viseme_CH",
  13: "viseme_RR",
  14: "viseme_nn",
  15: "viseme_SS",
  16: "viseme_CH",
  17: "viseme_TH",
  18: "viseme_FF",
  19: "viseme_TH",
  20: "viseme_kk",
  21: "viseme_PP",
};
