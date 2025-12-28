/**
 * Axios API client with interceptors for the API Integration Assistant backend
 */

import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";
import { ApiError, ApiResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const API_TIMEOUT = 30000; // 30 seconds

/**
 * Create axios instance with default configuration
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Request interceptor
 * - Add timestamps for debugging
 * - Log requests in development
 */
apiClient.interceptors.request.use(
  (config) => {
    // Add request timestamp
    config.headers["X-Request-Time"] = new Date().toISOString();

    // Log in development
    if (process.env.NEXT_PUBLIC_ENABLE_DEBUG === "true") {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
      });
    }

    return config;
  },
  (error) => {
    console.error("[API Request Error]", error);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor
 * - Log responses in development
 * - Handle errors uniformly
 * - Transform responses
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Calculate request duration
    const requestTime = response.config.headers["X-Request-Time"];
    const duration = requestTime
      ? new Date().getTime() - new Date(requestTime as string).getTime()
      : 0;

    // Log in development
    if (process.env.NEXT_PUBLIC_ENABLE_DEBUG === "true") {
      console.log(
        `[API Response] ${response.config.method?.toUpperCase()} ${response.config.url} (${duration}ms)`,
        {
          status: response.status,
          data: response.data,
        }
      );
    }

    return response;
  },
  (error: AxiosError) => {
    const apiError = handleApiError(error);

    // Log in development
    if (process.env.NEXT_PUBLIC_ENABLE_DEBUG === "true") {
      console.error("[API Error]", {
        message: apiError.message,
        status: apiError.status,
        url: error.config?.url,
        details: apiError.details,
      });
    }

    return Promise.reject(apiError);
  }
);

/**
 * Handle API errors uniformly
 */
function handleApiError(error: AxiosError): ApiError {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data as any;

    return {
      message: data?.detail || data?.message || getDefaultErrorMessage(status),
      status,
      code: data?.code,
      details: data,
    };
  } else if (error.request) {
    // Request made but no response received
    return {
      message: "No response from server. Please check if the backend is running.",
      status: 0,
      code: "NETWORK_ERROR",
      details: error.message,
    };
  } else {
    // Error setting up request
    return {
      message: error.message || "An unexpected error occurred",
      status: 0,
      code: "REQUEST_SETUP_ERROR",
      details: error,
    };
  }
}

/**
 * Get default error message for HTTP status codes
 */
function getDefaultErrorMessage(status: number): string {
  const messages: Record<number, string> = {
    400: "Bad request. Please check your input.",
    401: "Unauthorized. Please log in.",
    403: "Forbidden. You don't have permission to access this resource.",
    404: "Resource not found.",
    408: "Request timeout. Please try again.",
    409: "Conflict. The resource already exists or conflicts with current state.",
    422: "Validation error. Please check your input.",
    429: "Too many requests. Please slow down.",
    500: "Internal server error. Please try again later.",
    502: "Bad gateway. The server is temporarily unavailable.",
    503: "Service unavailable. Please try again later.",
    504: "Gateway timeout. The request took too long.",
  };

  return messages[status] || `HTTP Error ${status}`;
}

/**
 * Generic request wrapper with error handling
 */
export async function apiRequest<T>(
  config: AxiosRequestConfig
): Promise<ApiResponse<T>> {
  try {
    const response = await apiClient.request<T>(config);
    return {
      data: response.data,
      status: response.status,
    };
  } catch (error) {
    if (isApiError(error)) {
      return {
        error: error.message,
        status: error.status,
      };
    }
    return {
      error: "An unexpected error occurred",
      status: 0,
    };
  }
}

/**
 * Type guard for ApiError
 */
function isApiError(error: any): error is ApiError {
  return (
    error &&
    typeof error.message === "string" &&
    typeof error.status === "number"
  );
}

// Export configured client
export default apiClient;
