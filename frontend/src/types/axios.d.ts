declare module 'axios' {
  export interface AxiosRequestConfig {
    onUploadProgress?: (progressEvent: {
      loaded: number;
      total?: number;
      [key: string]: any;
    }) => void;
    onDownloadProgress?: (progressEvent: {
      loaded: number;
      total?: number;
      [key: string]: any;
    }) => void;
  }
}

export {};
