// Drafter Bridge Client Module
// This module handles communication between the client and server

interface FileData {
  filename: string;
  content: string;
  type: string;
  size: number;
  __file_upload__: boolean;
}

interface RequestData {
  [key: string]: any;
}

/**
 * Makes a request to the server with form data
 * Handles file uploads by converting them to base64
 */
export function makeRequest(formData: FormData): Promise<any> {
  const data: RequestData = {};
  const filePromises: Promise<void>[] = [];

  for (const [k, v] of formData.entries()) {
    if (v instanceof File) {
      // OLD IMPLEMENTATION - convert ArrayBuffer to base64
      // This is memory-inefficient and may fail on large files
      const promise = v.arrayBuffer().then((buffer) => {
        const bytes = new Uint8Array(buffer);
        const binary = Array.from(bytes).map((b) => String.fromCharCode(b)).join('');
        const base64 = btoa(binary);
        const fileData: FileData = {
          filename: v.name,
          content: base64,
          type: v.type,
          size: v.size,
          __file_upload__: true
        };
        data[k] = k in data ? ([] as any[]).concat(data[k] as any, fileData) : fileData;
      });
      filePromises.push(promise);
    } else {
      // Handle non-file form data
      data[k] = k in data ? ([] as any[]).concat(data[k] as any, v) : v;
    }
  }

  // Wait for all file processing to complete
  return Promise.all(filePromises).then(() => {
    // Build Python dictionary representation
    const pyDict = buildPyDict(data);
    return Request(pyDict);
  });
}

/**
 * Builds a Python dictionary representation from request data
 */
function buildPyDict(data: RequestData): any {
  // Implementation would convert JS object to Python dict format
  return data;
}

/**
 * Makes the actual request to the server
 */
function Request(data: any): Promise<any> {
  // Implementation would make HTTP request
  return Promise.resolve(data);
}

// Module exports
const drafter_bridge_client_module = {
  makeRequest
};

export default drafter_bridge_client_module;
