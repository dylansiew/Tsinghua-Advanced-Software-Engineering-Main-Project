export enum ConversationMessageType {
  QUERY = "query",
  AUDIO_RESPONSE = "audio_response",
}

export interface ConversationMessage {
  type: ConversationMessageType;
  data: any;
}

export interface Viseme {
  stopTime: number;
  readyPlayerMeViseme: string;
}

export interface WordOffset {
  offset_duration: number;
  text_offset: number;
  word_length: number;
}

export interface AudioMessage {
  base64_audio: string;
  viseme: Viseme[];
  word_boundary: WordOffset[];
}
