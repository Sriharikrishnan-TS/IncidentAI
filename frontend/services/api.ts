/**
 * Base API Service
 *
 * Provides a unified interface for all API calls with:
 * - Mock API simulation (for development)
 * - Future backend integration support
 * - Error handling
 * - Request/response interceptors
 */

// API Configuration
const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8080",
  timeout: 30000,
  useMock: process.env.NEXT_PUBLIC_USE_MOCK !== "false", // Default to mock
};

// Simulate network delay for mock responses
const simulateDelay = (ms: number = 800) =>
  new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Generic API Error
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public data?: any,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * API Request Options
 */
interface ApiRequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
}

/**
 * Base API Client
 */
class ApiClient {
  private baseURL: string;
  private timeout: number;
  private useMock: boolean;

  constructor() {
    this.baseURL = API_CONFIG.baseURL;
    this.timeout = API_CONFIG.timeout;
    this.useMock = API_CONFIG.useMock;
  }

  /**
   * Make an API request
   */
  async request<T>(
    endpoint: string,
    options: ApiRequestOptions = {},
  ): Promise<T> {
    const {
      method = "GET",
      headers = {},
      body,
      timeout = this.timeout,
    } = options;

    // If using mock, return immediately (actual mock data handled by services)
    if (this.useMock) {
      await simulateDelay();
      throw new Error("Mock mode: Service layer should handle mock responses");
    }

    const url = `${this.baseURL}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.message ||
            `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData,
        );
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof ApiError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === "AbortError") {
          throw new ApiError("Request timeout", 408);
        }
        throw new ApiError(error.message);
      }

      throw new ApiError("Unknown error occurred");
    }
  }

  /**
   * GET request
   */
  async get<T>(
    endpoint: string,
    options?: Omit<ApiRequestOptions, "method" | "body">,
  ): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  }

  /**
   * POST request
   */
  async post<T>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequestOptions, "method" | "body">,
  ): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "POST", body });
  }

  /**
   * PUT request
   */
  async put<T>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequestOptions, "method" | "body">,
  ): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "PUT", body });
  }

  /**
   * DELETE request
   */
  async delete<T>(
    endpoint: string,
    options?: Omit<ApiRequestOptions, "method" | "body">,
  ): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  }

  /**
   * PATCH request
   */
  async patch<T>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequestOptions, "method" | "body">,
  ): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "PATCH", body });
  }

  /**
   * Check if using mock mode
   */
  isMockMode(): boolean {
    return this.useMock;
  }

  /**
   * Set mock mode
   */
  setMockMode(useMock: boolean): void {
    this.useMock = useMock;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export configuration
export { API_CONFIG };

// Made with Bob
