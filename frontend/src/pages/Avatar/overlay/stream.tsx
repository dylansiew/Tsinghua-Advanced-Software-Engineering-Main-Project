import { useState } from 'react';

const TTSStreamPlayer = () => {
  const [text, setText] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);

  const handlePlay = async () => {
    setIsPlaying(true);

    const audioContext = new (window.AudioContext || window.webkitAudioContext)();

    const response = await fetch(`/speak?text=${encodeURIComponent(text)}`);
    const reader = response.body.getReader();
    let audioBuffer = new Uint8Array();

    const processChunk = async (chunk) => {
      // Append to existing buffer
      const newBuffer = new Uint8Array(audioBuffer.length + chunk.length);
      newBuffer.set(audioBuffer);
      newBuffer.set(chunk, audioBuffer.length);
      audioBuffer = newBuffer;

      try {
        const decoded = await audioContext.decodeAudioData(audioBuffer.buffer.slice(0));
        const source = audioContext.createBufferSource();
        source.buffer = decoded;
        source.connect(audioContext.destination);
        source.start();
        audioBuffer = new Uint8Array(); // reset buffer
      } catch (err) {
        // Not enough data to decode yet — wait for more
      }
    };

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      await processChunk(value);
    }

    setIsPlaying(false);
  };

  return (
    <div>
      <textarea
        rows="4"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter text to synthesize"
        style={{ width: '100%' }}
      />
      <button onClick={handlePlay} disabled={isPlaying}>
        {isPlaying ? 'Synthesizing...' : 'Play'}
      </button>
    </div>
  );
};

export default TTSStreamPlayer;
