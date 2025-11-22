/**
 * File upload and management API services
 */

import { apiClient } from '@/utils/api';

export interface FileInfo {
  file_id: string;
  filename: string;
  file_type: string;
  size: number;
  uploaded_at: string;
  text_extracted: boolean;
  text_length?: number;
}

export interface FileListResponse {
  files: FileInfo[];
  total: number;
}

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  file_type: string;
  size: number;
  message: string;
}

export interface FileTextResponse {
  file_id: string;
  filename: string;
  text: string;
  length: number;
}

/**
 * Upload a file
 */
export async function uploadFile(file: File): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post<FileUploadResponse>('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
}

/**
 * List all uploaded files
 */
export async function listFiles(): Promise<FileListResponse> {
  const response = await apiClient.get<FileListResponse>('/files/list');
  return response.data;
}

/**
 * Get file metadata
 */
export async function getFileInfo(fileId: string): Promise<FileInfo> {
  const response = await apiClient.get<FileInfo>(`/files/${fileId}`);
  return response.data;
}

/**
 * Get extracted text from file
 */
export async function getFileText(fileId: string): Promise<FileTextResponse> {
  const response = await apiClient.get<FileTextResponse>(`/files/${fileId}/text`);
  return response.data;
}

/**
 * Delete a file
 */
export async function deleteFile(fileId: string): Promise<void> {
  await apiClient.delete(`/files/${fileId}`);
}

