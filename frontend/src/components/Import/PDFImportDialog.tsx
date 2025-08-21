import React, { useState, useCallback } from 'react';
import {
  Upload,
  FileText,
  X,
  AlertCircle,
  CheckCircle,
  Loader2,
  Eye,
  Download,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import workflowApi from '../../services/workflowApi';
import { PDFAnalysisResult } from '../../types/workflow';

interface PDFImportDialogProps {
  unitId: string;
  unitName: string;
  onClose: () => void;
  onImportComplete?: () => void;
}

const PDFImportDialog: React.FC<PDFImportDialogProps> = ({
  unitId,
  unitName,
  onClose,
  onImportComplete,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] =
    useState<PDFAnalysisResult | null>(null);
  const [extractedText, setExtractedText] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [importSuccess, setImportSuccess] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
        setError(null);
      } else {
        setError('Please upload a PDF file');
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type === 'application/pdf') {
        setFile(selectedFile);
        setError(null);
      } else {
        setError('Please upload a PDF file');
      }
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    try {
      const result = await workflowApi.analyzePDF(file);
      setAnalysisResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze PDF');
    } finally {
      setLoading(false);
    }
  };

  const handleExtractText = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    try {
      const result = await workflowApi.extractPDFText(file, 'markdown');
      setExtractedText(result.text);
      setShowPreview(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to extract text');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!file || !analysisResult) return;

    setLoading(true);
    setError(null);
    try {
      const result = await workflowApi.createUnitStructureFromPDF(
        unitId,
        file,
        true
      );
      if (result.status === 'success') {
        setImportSuccess(true);
        if (onImportComplete) {
          window.setTimeout(() => {
            onImportComplete();
          }, 2000);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import PDF');
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
      <div className='bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden'>
        {/* Header */}
        <div className='px-6 py-4 border-b flex justify-between items-center'>
          <div>
            <h2 className='text-2xl font-bold text-gray-900'>
              Import PDF Content
            </h2>
            <p className='text-gray-600 mt-1'>
              Import unit materials for {unitName}
            </p>
          </div>
          <button
            onClick={onClose}
            className='text-gray-500 hover:text-gray-700'
          >
            <X className='w-6 h-6' />
          </button>
        </div>

        {/* Content */}
        <div
          className='px-6 py-4 overflow-y-auto'
          style={{ maxHeight: 'calc(90vh - 200px)' }}
        >
          {importSuccess ? (
            <div className='py-12 text-center'>
              <CheckCircle className='w-16 h-16 text-green-500 mx-auto mb-4' />
              <h3 className='text-xl font-semibold text-gray-900 mb-2'>
                Import Successful!
              </h3>
              <p className='text-gray-600'>
                Unit structure has been created from the PDF
              </p>
            </div>
          ) : (
            <>
              {/* File Upload */}
              {!file && (
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center ${
                    dragActive
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <Upload className='w-12 h-12 text-gray-400 mx-auto mb-4' />
                  <p className='text-lg font-medium text-gray-700 mb-2'>
                    Drop your PDF here or click to browse
                  </p>
                  <p className='text-sm text-gray-500 mb-4'>
                    Supports unit outlines, syllabi, lecture notes, and unit
                    materials
                  </p>
                  <label className='inline-block'>
                    <input
                      type='file'
                      accept='.pdf'
                      onChange={handleFileChange}
                      className='hidden'
                    />
                    <span className='px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 cursor-pointer transition-colors'>
                      Choose File
                    </span>
                  </label>
                </div>
              )}

              {/* File Selected */}
              {file && !analysisResult && (
                <div className='border rounded-lg p-4 mb-4'>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center'>
                      <FileText className='w-8 h-8 text-blue-500 mr-3' />
                      <div>
                        <p className='font-medium text-gray-900'>{file.name}</p>
                        <p className='text-sm text-gray-500'>
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setFile(null);
                        setAnalysisResult(null);
                        setExtractedText(null);
                      }}
                      className='text-red-500 hover:text-red-700'
                    >
                      <X className='w-5 h-5' />
                    </button>
                  </div>

                  <div className='mt-4 flex space-x-3'>
                    <button
                      onClick={handleAnalyze}
                      disabled={loading}
                      className='px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center'
                    >
                      {loading ? (
                        <Loader2 className='w-4 h-4 mr-2 animate-spin' />
                      ) : (
                        <Eye className='w-4 h-4 mr-2' />
                      )}
                      Analyze PDF
                    </button>
                    <button
                      onClick={handleExtractText}
                      disabled={loading}
                      className='px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 flex items-center'
                    >
                      <FileText className='w-4 h-4 mr-2' />
                      Extract Text
                    </button>
                  </div>
                </div>
              )}

              {/* Analysis Results */}
              {analysisResult && (
                <div className='space-y-4'>
                  <div className='border rounded-lg p-4'>
                    <h3 className='font-semibold text-gray-900 mb-3'>
                      Document Analysis
                    </h3>
                    <div className='grid grid-cols-2 gap-4 text-sm'>
                      <div>
                        <span className='text-gray-500'>Document Type:</span>
                        <span className='ml-2 font-medium'>
                          {analysisResult.document_type.replace('_', ' ')}
                        </span>
                      </div>
                      <div>
                        <span className='text-gray-500'>Pages:</span>
                        <span className='ml-2 font-medium'>
                          {analysisResult.metadata.page_count}
                        </span>
                      </div>
                      <div>
                        <span className='text-gray-500'>Word Count:</span>
                        <span className='ml-2 font-medium'>
                          {analysisResult.metadata.word_count.toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className='text-gray-500'>Has TOC:</span>
                        <span className='ml-2 font-medium'>
                          {analysisResult.metadata.has_toc ? 'Yes' : 'No'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className='border rounded-lg p-4'>
                    <h3 className='font-semibold text-gray-900 mb-3'>
                      Extracted Content
                    </h3>
                    <div className='grid grid-cols-2 gap-4 text-sm'>
                      <div>
                        <span className='text-gray-500'>Sections:</span>
                        <span className='ml-2 font-medium'>
                          {analysisResult.extracted_content.sections_count}
                        </span>
                      </div>
                      <div>
                        <span className='text-gray-500'>
                          Learning Outcomes:
                        </span>
                        <span className='ml-2 font-medium'>
                          {
                            analysisResult.extracted_content
                              .learning_outcomes_count
                          }
                        </span>
                      </div>
                      <div>
                        <span className='text-gray-500'>Assessments:</span>
                        <span className='ml-2 font-medium'>
                          {analysisResult.extracted_content.assessments_count}
                        </span>
                      </div>
                      <div>
                        <span className='text-gray-500'>Weekly Content:</span>
                        <span className='ml-2 font-medium'>
                          {
                            analysisResult.extracted_content
                              .weekly_content_count
                          }
                        </span>
                      </div>
                    </div>
                  </div>

                  {analysisResult.sections.length > 0 && (
                    <div className='border rounded-lg p-4'>
                      <div
                        className='flex justify-between items-center cursor-pointer'
                        onClick={() => setShowPreview(!showPreview)}
                      >
                        <h3 className='font-semibold text-gray-900'>
                          Document Sections
                        </h3>
                        {showPreview ? (
                          <ChevronUp className='w-5 h-5 text-gray-500' />
                        ) : (
                          <ChevronDown className='w-5 h-5 text-gray-500' />
                        )}
                      </div>
                      {showPreview && (
                        <div className='mt-3 space-y-2'>
                          {analysisResult.sections.map((section, index) => (
                            <div
                              key={index}
                              className='flex justify-between text-sm py-1'
                            >
                              <span
                                className='text-gray-700'
                                style={{
                                  paddingLeft: `${section.level * 20}px`,
                                }}
                              >
                                {section.title}
                              </span>
                              <span className='text-gray-500'>
                                p. {section.page_start}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Text Preview */}
              {extractedText && showPreview && (
                <div className='mt-4 border rounded-lg p-4'>
                  <h3 className='font-semibold text-gray-900 mb-3'>
                    Extracted Text Preview
                  </h3>
                  <div className='bg-gray-50 rounded p-4 max-h-64 overflow-y-auto'>
                    <pre className='text-sm text-gray-700 whitespace-pre-wrap'>
                      {extractedText.substring(0, 2000)}
                      {extractedText.length > 2000 && '...'}
                    </pre>
                  </div>
                </div>
              )}

              {/* Error Display */}
              {error && (
                <div className='mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start'>
                  <AlertCircle className='w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5' />
                  <span className='text-red-700'>{error}</span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className='px-6 py-4 border-t flex justify-between items-center'>
          <button
            onClick={onClose}
            className='px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors'
          >
            Cancel
          </button>

          {analysisResult && !importSuccess && (
            <button
              onClick={handleImport}
              disabled={loading}
              className='px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center'
            >
              {loading ? (
                <Loader2 className='w-4 h-4 mr-2 animate-spin' />
              ) : (
                <Download className='w-4 h-4 mr-2' />
              )}
              Import to Unit
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFImportDialog;
