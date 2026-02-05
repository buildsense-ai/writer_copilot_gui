// SVG 图标组件库 - VSCode 风格
import React from 'react';

export const FileIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M13.5 1h-11C1.67 1 1 1.67 1 2.5v11c0 .83.67 1.5 1.5 1.5h11c.83 0 1.5-.67 1.5-1.5v-11c0-.83-.67-1.5-1.5-1.5zM13 13H3V3h10v10z"/>
  </svg>
);

export const FolderIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M14.5 3H7.71l-.85-.85L6.51 2h-5l-.5.5v11l.5.5h13l.5-.5v-10L14.5 3zm-.51 8.49V13h-12V7h4.49l.35-.15.86-.86H14v1.5l-.01 4zm0-6.49h-6.5l-.35.15-.86.86H2v-3h4.29l.85.85.36.15H14l-.01.99z"/>
  </svg>
);

export const DocumentIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M13.85 1H6.15l-.5.5v3h.71V2h7.15v11h-2.51v.71h2.85l.5-.5v-12l-.5-.5z"/>
    <path d="M8.5 4H3.36l-.5.5v10l.5.5h8l.5-.5V7.7L8.5 4zm2.5 10H4V5h4v4h3v5zm0-6h-2V6l2 2z"/>
  </svg>
);

export const SearchIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M15.7 13.3l-3.81-3.83A5.93 5.93 0 0 0 13 6c0-3.31-2.69-6-6-6S1 2.69 1 6s2.69 6 6 6c1.3 0 2.48-.41 3.47-1.11l3.83 3.81c.19.2.45.3.7.3.25 0 .52-.09.7-.3a.996.996 0 0 0 0-1.41v.01zM7 10.7c-2.59 0-4.7-2.11-4.7-4.7 0-2.59 2.11-4.7 4.7-4.7 2.59 0 4.7 2.11 4.7 4.7 0 2.59-2.11 4.7-4.7 4.7z"/>
  </svg>
);

export const BrainIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M8 1C4.5 1 2 3.6 2 6.5c0 1.3.5 2.5 1.3 3.4L2 14.5l4.5-1.3c.5.1 1 .2 1.5.2 3.5 0 6-2.6 6-5.5S11.5 1 8 1zm0 10c-.4 0-.8 0-1.2-.1l-2.3.7.7-2.3C4.5 8.5 4 7.5 4 6.5 4 4.6 5.8 3 8 3s4 1.6 4 3.5S10.2 10 8 10z"/>
    <circle cx="6" cy="6.5" r=".8"/>
    <circle cx="8" cy="6.5" r=".8"/>
    <circle cx="10" cy="6.5" r=".8"/>
  </svg>
);

export const TerminalIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M13.655 3.56L8.918.75a1.785 1.785 0 0 0-1.82 0L2.363 3.56a1.889 1.889 0 0 0-.921 1.628v5.624a1.889 1.889 0 0 0 .913 1.627l4.736 2.812a1.785 1.785 0 0 0 1.82 0l4.736-2.812a1.889 1.889 0 0 0 .913-1.627V5.188a1.889 1.889 0 0 0-.904-1.627zm-6.724 8.258l-.242-.242.708-.708.242.242-.708.708zm.5-1.5l-.242-.242 1.85-1.85.242.242-1.85 1.85zm1.35-1.35l-.242-.242.337-.337.242.242-.337.337zm2.77-.589l-3.426 3.426-.707-.707 3.426-3.426.707.707z"/>
  </svg>
);

export const PDFIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M14 1H6.5L5 2.5v11l.5.5H14l.5-.5V1.5L14 1zm-.5 12.5h-7v-11h3V6h4v6.5zM11 2.5V6h3.5L11 2.5z"/>
    <path d="M7 7h1v1H7V7zm2 0h3v1H9V7zM7 9h1v1H7V9zm2 0h3v1H9V9zm-2 2h1v1H7v-1zm2 0h3v1H9v-1z"/>
  </svg>
);

export const SparklesIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M8 1L6 6 1 8l5 2 2 5 2-5 5-2-5-2-2-5zm0 3.83L8.75 7l2.17.75L8.75 8.25 8 11.17 7.25 8.25 5.08 7.75l2.17-.75L8 4.83z"/>
    <path d="M3 3l-.5 1.5L1 5l1.5.5L3 7l.5-1.5L5 5 3.5 4.5 3 3zm10 8l-.5 1.5L11 13l1.5.5.5 1.5.5-1.5L15 13l-1.5-.5-.5-1.5z"/>
  </svg>
);

export const EditIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M13.23 1h-1.46L3.52 9.25l-.16.22L1 13.59 2.41 15l4.12-2.36.22-.16L15 4.23V2.77L13.23 1zM2.41 13.59l1.51-3 1.45 1.45-2.96 1.55zm3.83-2.06L4.47 9.76l8-8 1.77 1.77-8 8z"/>
  </svg>
);

export const CodeIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M4.708 5.578L2.061 8.224l2.647 2.646-.708.708-3-3V7.87l3-3 .708.708zm7-.708L11 5.578l2.647 2.646L11 10.87l.708.708 3-3V7.87l-3-3zM4.908 13l.894.448 5-10L9.908 3l-5 10z"/>
  </svg>
);

export const UploadIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M7 2l-1.146 1.146-.707-.707L8 0l2.853 2.439-.707.707L9 2v4H7V2z"/>
    <path d="M14 14V6h-2v8H4V6H2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2z"/>
  </svg>
);

export const LoadingIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M8 1v2a5 5 0 0 1 0 10v2a7 7 0 0 0 0-14z" opacity="0.4"/>
    <path d="M8 1v2a5 5 0 0 0 0 10v2a7 7 0 0 1 0-14z">
      <animateTransform
        attributeName="transform"
        type="rotate"
        from="0 8 8"
        to="360 8 8"
        dur="1s"
        repeatCount="indefinite"
      />
    </path>
  </svg>
);

export const CheckIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 16 16" fill="currentColor">
    <path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"/>
  </svg>
);

export const MemoryIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z"/>
    <path d="M12 12l.01-.01M8 12l.01-.01M16 12l.01-.01"/>
    <path d="M12 8v.01M12 16v.01"/>
  </svg>
);
