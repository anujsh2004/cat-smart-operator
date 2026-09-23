export type HttpMethod = "GET" | "POST" | "PATCH";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
