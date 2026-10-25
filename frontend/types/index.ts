export type Citation = {
  source_file: string;
  page_number: number;
  score?: number;
  excerpt?: string;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
};
