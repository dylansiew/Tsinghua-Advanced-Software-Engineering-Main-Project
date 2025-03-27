export interface Video {
  url: string;
  title: string;
}

export const TEST_VIDEOS = [
  { url: "test-url", title: "test-title" },
  { url: "test-url2", title: "test-title1" },
  { url: "test-url3", title: "test-title2" },
  { url: "test-url", title: "test-title" },
  { url: "test-url2", title: "test-title1" },
  { url: "test-url3", title: "test-title2" },
] as Video[];
