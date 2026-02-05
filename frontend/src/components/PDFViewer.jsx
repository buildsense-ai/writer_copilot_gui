// PDF 溯源查看器 - 支持页面跳转和高亮
import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { PDFIcon, SearchIcon } from './Icons';

// 设置 PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PDFViewer({
  fileUrl,
  initialPage = 1,
  highlightText = null,
  onClose
}) {
  const [numPages, setNumPages] = useState(null);
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [searchTerm, setSearchTerm] = useState('');
  const [scale, setScale] = useState(1.2);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const goToPage = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= numPages) {
      setCurrentPage(pageNumber);
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#1e1e1e]">
      {/* PDF 工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#252526] border-b border-[#3e3e42]">
        <div className="flex items-center gap-3">
          <PDFIcon className="w-4 h-4 text-[#f9826c]" />
          <span className="text-sm text-[#cccccc]">PDF Viewer</span>
        </div>

        <div className="flex items-center gap-2">
          {/* 页码导航 */}
          <button
            onClick={() => goToPage(currentPage - 1)}
            disabled={currentPage <= 1}
            className="px-2 py-1 text-xs bg-[#37373d] text-[#cccccc] rounded disabled:opacity-30 hover:bg-[#3e3e42] transition-colors"
          >
            ←
          </button>
          <span className="text-xs text-[#858585]">
            {currentPage} / {numPages || '?'}
          </span>
          <button
            onClick={() => goToPage(currentPage + 1)}
            disabled={currentPage >= numPages}
            className="px-2 py-1 text-xs bg-[#37373d] text-[#cccccc] rounded disabled:opacity-30 hover:bg-[#3e3e42] transition-colors"
          >
            →
          </button>

          {/* 缩放控制 */}
          <div className="flex items-center gap-1 ml-4">
            <button
              onClick={() => setScale(s => Math.max(0.5, s - 0.1))}
              className="px-2 py-1 text-xs bg-[#37373d] text-[#cccccc] rounded hover:bg-[#3e3e42] transition-colors"
            >
              -
            </button>
            <span className="text-xs text-[#858585] w-12 text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={() => setScale(s => Math.min(2.0, s + 0.1))}
              className="px-2 py-1 text-xs bg-[#37373d] text-[#cccccc] rounded hover:bg-[#3e3e42] transition-colors"
            >
              +
            </button>
          </div>

          <button
            onClick={onClose}
            className="ml-4 px-3 py-1 text-xs bg-[#37373d] text-[#cccccc] rounded hover:bg-[#3e3e42] transition-colors"
          >
            Close
          </button>
        </div>
      </div>

      {/* 搜索栏 */}
      {highlightText && (
        <div className="px-4 py-2 bg-[#2d2d30] border-b border-[#3e3e42] flex items-center gap-2">
          <SearchIcon className="w-3 h-3 text-[#858585]" />
          <span className="text-xs text-[#858585]">
            Highlighting: <span className="text-[#f9826c]">{highlightText}</span>
          </span>
        </div>
      )}

      {/* PDF 内容 */}
      <div className="flex-1 overflow-auto bg-[#2d2d30] flex justify-center py-6">
        <div className="shadow-2xl">
          <Document
            file={fileUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={
              <div className="flex items-center justify-center p-12">
                <div className="text-[#858585]">Loading PDF...</div>
              </div>
            }
            error={
              <div className="flex items-center justify-center p-12">
                <div className="text-red-400">Failed to load PDF</div>
              </div>
            }
          >
            <Page
              pageNumber={currentPage}
              scale={scale}
              renderTextLayer={true}
              renderAnnotationLayer={true}
              className="border border-[#3e3e42]"
            />
          </Document>
        </div>
      </div>

      {/* 缩略图导航 (可选) */}
      {numPages && numPages > 1 && (
        <div className="h-24 bg-[#252526] border-t border-[#3e3e42] overflow-x-auto">
          <div className="flex gap-2 p-2 h-full">
            {Array.from({ length: Math.min(numPages, 20) }, (_, i) => i + 1).map(pageNum => (
              <button
                key={pageNum}
                onClick={() => goToPage(pageNum)}
                className={`flex-shrink-0 text-xs px-2 rounded transition-colors ${
                  pageNum === currentPage
                    ? 'bg-[#007acc] text-white'
                    : 'bg-[#37373d] text-[#858585] hover:bg-[#3e3e42]'
                }`}
              >
                {pageNum}
              </button>
            ))}
            {numPages > 20 && (
              <span className="text-xs text-[#858585] flex items-center px-2">
                ... {numPages} pages
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
