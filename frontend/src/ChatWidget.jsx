// frontend/src/ChatWidget.jsx
import React, { useState, useRef, useEffect } from 'react';
import './ChatWidget.css';

const API_BASE = 'http://localhost:8001/api/v1';

const VENDOR_CHIPS = [
    'EMD refund process',
    'Bid submission deadline',
    'Vendor registration',
    'निविदा में संशोधन'
];

const OFFICER_CHIPS = [
    'GFR 2017 Rules',
    'CVC compliance',
    'Tender publication',
    'Bid evaluation'
];

// ** bold ** → <strong> renderer
function parseBold(text = '') {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={i}>{part.slice(2, -2)}</strong>;
        }
        return part;
    });
}

function parseInlineMarkdown(text = '', sourceRefs = [], ruleCitations = [], onPdfLinkClick = null) {
    if (!text) return '';
    const parts = text.split(/(\*\*.*?\*\*|__.*?__|`.*?`|\[Page\s*\d+(?:-\d+)?\]|(?:📥\s*)?\[.*?\]\(.*?\))/g);
    return parts.map((part, i) => {
        if ((part.startsWith('**') && part.endsWith('**')) || (part.startsWith('__') && part.endsWith('__'))) {
            return <strong key={i}>{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('`') && part.endsWith('`')) {
            return <code key={i} style={{ background: '#f1f5f9', padding: '2px 4px', borderRadius: '4px', fontSize: '90%', fontFamily: 'monospace', color: '#0f172a' }}>{part.slice(1, -1)}</code>;
        }
        
        // Link parser (e.g. [Download Official GeM Financial Sanction Note (PDF)](/api/v1/...))
        const linkMatch = part.match(/(?:📥\s*)?\[(.*?)\]\((.*?)\)/);
        if (linkMatch) {
            const label = linkMatch[1];
            const url = linkMatch[2];
            const fullUrl = url.startsWith('/') ? `${API_BASE.replace('/api/v1', '')}${url}` : url;
            return (
                <a
                    key={i}
                    href={fullUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    download
                    style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px',
                        background: 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)',
                        color: '#ffffff',
                        padding: '8px 16px',
                        borderRadius: '8px',
                        fontWeight: '700',
                        fontSize: '13px',
                        textDecoration: 'none',
                        boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
                        margin: '8px 0',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease'
                    }}
                    className="gem-pdf-download-btn"
                >
                    📥 {label}
                </a>
            );
        }

        const pageMatch = part.match(/^\[Page\s*(\d+)(?:-(\d+))?\]$/i);
        if (pageMatch && sourceRefs && sourceRefs.length > 0 && onPdfLinkClick) {
            const firstRef = sourceRefs[0];
            if (firstRef && firstRef.file !== 'Learned satisfied Q&As') {
                const docBaseUrl = `${API_BASE.replace('/api/v1', '')}/docs/${firstRef.category}/${firstRef.file}`;
                const highlightTerm = ruleCitations && ruleCitations.length > 0 ? ruleCitations[0] : '';
                const pageNum = parseInt(pageMatch[1], 10);
                
                return (
                    <a
                        key={i}
                        href="#"
                        onClick={(e) => {
                            e.preventDefault();
                            onPdfLinkClick(docBaseUrl, pageNum, highlightTerm);
                        }}
                        style={{
                            color: '#3b82f6',
                            textDecoration: 'none',
                            fontWeight: '600',
                            background: '#eff6ff',
                            padding: '1px 4px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            border: '1px solid #bfdbfe',
                            margin: '0 2px',
                            display: 'inline-block',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease'
                        }}
                        className="cg-inline-citation"
                    >
                        {part}
                    </a>
                );
            }
        }
        return part;
    });
}

function parseMarkdownToReact(text = '', sourceRefs = [], ruleCitations = [], onPdfLinkClick = null) {
    if (!text) return null;

    const lines = text.split('\n');
    const elements = [];
    let currentList = null;

    const flushList = (key) => {
        if (currentList) {
            if (currentList.type === 'ul') {
                elements.push(
                    <ul key={key} style={{ paddingLeft: '20px', margin: '8px 0', listStyleType: 'disc' }}>
                        {currentList.items.map((item, index) => (
                            <li key={index} style={{ marginBottom: '6px' }}>{parseInlineMarkdown(item, sourceRefs, ruleCitations, onPdfLinkClick)}</li>
                        ))}
                    </ul>
                );
            } else {
                elements.push(
                    <ol key={key} style={{ paddingLeft: '20px', margin: '8px 0' }}>
                        {currentList.items.map((item, index) => (
                            <li key={index} value={item.value} style={{ marginBottom: '6px' }}>{parseInlineMarkdown(item.text, sourceRefs, ruleCitations, onPdfLinkClick)}</li>
                        ))}
                    </ol>
                );
            }
            currentList = null;
        }
    };

    let elementKey = 0;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmedLine = line.trim();

        // 1. Check for Markdown Table (| col1 | col2 |)
        if (trimmedLine.startsWith('|') && trimmedLine.endsWith('|')) {
            flushList(`list-${elementKey++}`);
            const tableLines = [trimmedLine];
            while (i + 1 < lines.length && lines[i + 1].trim().startsWith('|') && lines[i + 1].trim().endsWith('|')) {
                i++;
                tableLines.push(lines[i].trim());
            }

            if (tableLines.length >= 2) {
                const parseRow = (rowStr) => rowStr.split('|').slice(1, -1).map(c => c.trim());
                const headerCells = parseRow(tableLines[0]);
                const bodyStartIdx = (tableLines.length > 1 && tableLines[1].includes('---')) ? 2 : 1;
                const bodyRows = tableLines.slice(bodyStartIdx).map(parseRow);

                elements.push(
                    <div key={`table-wrapper-${elementKey++}`} className="cg-table-wrapper" style={{ overflowX: 'auto', margin: '14px 0', borderRadius: '8px', border: '1px solid #cbd5e1', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left', background: '#ffffff' }}>
                            <thead>
                                <tr style={{ background: '#1e3a8a', color: '#ffffff' }}>
                                    {headerCells.map((cell, cIdx) => (
                                        <th key={cIdx} style={{ padding: '9px 12px', border: '1px solid #334155', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                                            {parseInlineMarkdown(cell, sourceRefs, ruleCitations, onPdfLinkClick)}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {bodyRows.map((row, rIdx) => (
                                    <tr key={rIdx} style={{ background: rIdx % 2 === 0 ? '#ffffff' : '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                                        {row.map((cell, cIdx) => (
                                            <td key={cIdx} style={{ padding: '8px 12px', border: '1px solid #e2e8f0', color: '#1e293b' }}>
                                                {parseInlineMarkdown(cell, sourceRefs, ruleCitations, onPdfLinkClick)}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                );
                continue;
            }
        }

        // 2. Check for horizontal rule
        if (trimmedLine === '---' || trimmedLine === '***' || trimmedLine === '___') {
            flushList(`list-${elementKey++}`);
            elements.push(<hr key={`hr-${elementKey++}`} style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '14px 0' }} />);
            continue;
        }

        // 2. Check for headers
        const headerMatch = line.match(/^(#{1,6})\s+(.*)$/);
        if (headerMatch) {
            flushList(`list-${elementKey++}`);
            const level = headerMatch[1].length;
            const titleText = headerMatch[2];
            const headerStyle = {
                margin: '14px 0 8px 0',
                fontWeight: '700',
                color: '#1e293b',
                lineHeight: '1.3'
            };
            if (level === 1) {
                elements.push(<h2 key={`h-${elementKey++}`} style={{ ...headerStyle, fontSize: '18px', borderBottom: '1px solid #e2e8f0', paddingBottom: '4px' }}>{parseInlineMarkdown(titleText, sourceRefs, ruleCitations, onPdfLinkClick)}</h2>);
            } else if (level === 2) {
                elements.push(<h3 key={`h-${elementKey++}`} style={{ ...headerStyle, fontSize: '16px' }}>{parseInlineMarkdown(titleText, sourceRefs, ruleCitations, onPdfLinkClick)}</h3>);
            } else {
                elements.push(<h4 key={`h-${elementKey++}`} style={{ ...headerStyle, fontSize: '14px' }}>{parseInlineMarkdown(titleText, sourceRefs, ruleCitations, onPdfLinkClick)}</h4>);
            }
            continue;
        }

        // 3. Check for Blockquote
        if (trimmedLine.startsWith('>')) {
            flushList(`list-${elementKey++}`);
            const quoteText = trimmedLine.replace(/^>\s*/, '');
            elements.push(
                <blockquote key={`quote-${elementKey++}`} style={{
                    margin: '10px 0',
                    padding: '8px 12px',
                    background: '#f8fafc',
                    borderLeft: '4px solid #cbd5e1',
                    borderRadius: '4px',
                    fontSize: '13px',
                    color: '#475569',
                    fontStyle: 'italic'
                }}>
                    {parseInlineMarkdown(quoteText, sourceRefs, ruleCitations, onPdfLinkClick)}
                </blockquote>
            );
            continue;
        }

        // 4. Check for bullet list item
        const bulletMatch = line.match(/^(\s*)[-*+]\s+(.*)$/);
        if (bulletMatch) {
            if (currentList && currentList.type !== 'ul') {
                flushList(`list-${elementKey++}`);
            }
            if (!currentList) {
                currentList = { type: 'ul', items: [] };
            }
            currentList.items.push(bulletMatch[2]);
            continue;
        }

        // 5. Check for numbered list item
        const numberMatch = line.match(/^(\s*)(\d+)\.\s+(.*)$/);
        if (numberMatch) {
            if (currentList && currentList.type !== 'ol') {
                flushList(`list-${elementKey++}`);
            }
            if (!currentList) {
                currentList = { type: 'ol', items: [] };
            }
            currentList.items.push({ text: numberMatch[3], value: parseInt(numberMatch[2], 10) });
            continue;
        }

        // 6. Empty line
        if (trimmedLine === '') {
            continue;
        }

        // 7. Regular paragraph text
        flushList(`list-${elementKey++}`);
        elements.push(
            <p key={`p-${elementKey++}`} style={{ margin: '0 0 8px 0', lineHeight: '1.5' }}>
                {parseInlineMarkdown(line, sourceRefs, ruleCitations, onPdfLinkClick)}
            </p>
        );
    }

    flushList(`list-${elementKey++}`);
    return elements;
}

const ChatWidget = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [role, setRole] = useState(null);          // null = not selected
    const [sessionId, setSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [detectedLang, setDetectedLang] = useState('en');
    const [responseTime, setResponseTime] = useState(null);
    const [isAdminOpen, setIsAdminOpen] = useState(false);
    const [adminTab, setAdminTab] = useState('dashboard');
    const [adminAnalytics, setAdminAnalytics] = useState(null);
    const [adminSearch, setAdminSearch] = useState('');
    const [adminRoleFilter, setAdminRoleFilter] = useState('all');
    const [adminFeedbackFilter, setAdminFeedbackFilter] = useState('all');
    const [adminConfig, setAdminConfig] = useState(null);
    const [activeSessions, setActiveSessions] = useState([]);
    const [documents, setDocuments] = useState([]);
    const [faqQuery, setFaqQuery] = useState('');
    const [faqAnswer, setFaqAnswer] = useState('');
    const [blPattern, setBlPattern] = useState('');
    const [blResponse, setBlResponse] = useState('');
    const [glossaryTerm, setGlossaryTerm] = useState('');
    const [corrections, setCorrections] = useState({});
    const messagesContainerRef = useRef(null);

    // PDF.js State Variables
    const [showPdf, setShowPdf] = useState(false);
    const [pdfUrl, setPdfUrl] = useState('');
    const [pdfTitle, setPdfTitle] = useState('Document Viewer');
    const [pdfPage, setPdfPage] = useState(1);
    const [pdfPageCount, setPdfPageCount] = useState(1);
    const [pdfScale, setPdfScale] = useState('fit');
    const [pdfSearchText, setPdfSearchText] = useState('');

    const pdfCanvasRef = useRef(null);
    const pdfDocRef = useRef(null);
    const pdfPageRenderingRef = useRef(false);
    const pdfPendingPageRef = useRef(null);
    const pdfContainerRef = useRef(null);
    const lastUserQueryRef = useRef('');

    // Load PDF.js dynamically
    useEffect(() => {
        if (window.pdfjsLib) return;
        
        const isLocalFile = window.location.protocol === 'file:';
        const localPath = isLocalFile ? 'http://localhost:8001/static/pdf.min.js' : '/static/pdf.min.js';
        const backupCdn = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js';

        const script = document.createElement('script');
        script.src = localPath;
        script.async = true;
        
        const initializeWorker = () => {
            if (!window.pdfjsLib) return;
            try {
                const workerUrl = isLocalFile ? 'http://localhost:8001/static/pdf.worker.min.js' : '/static/pdf.worker.min.js';
                const code = `
                    try {
                        importScripts('${workerUrl}');
                    } catch (e) {
                        try {
                            importScripts('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js');
                        } catch (err) {
                            console.error('Failed to load PDF worker in Blob:', err);
                        }
                    }
                `;
                const blob = new Blob([code], { type: 'application/javascript' });
                window.pdfjsLib.GlobalWorkerOptions.workerSrc = URL.createObjectURL(blob);
                console.log("React widget: PDF.js Web Worker configured via Blob URL:", window.pdfjsLib.GlobalWorkerOptions.workerSrc);
            } catch (e) {
                console.warn("React widget: Failed to set worker via Blob URL, falling back to CDN:", e);
                window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
            }
        };

        script.onload = () => {
            initializeWorker();
        };

        script.onerror = () => {
            console.log("React widget: Local pdf.min.js failed to load. Falling back to CDN.");
            const cdnScript = document.createElement('script');
            cdnScript.src = backupCdn;
            cdnScript.async = true;
            cdnScript.onload = () => {
                initializeWorker();
            };
            document.body.appendChild(cdnScript);
        };

        document.body.appendChild(script);
    }, []);

    const scrollToBottom = (force = false) => {
        const container = messagesContainerRef.current;
        if (!container) return;
        const threshold = 100; // pixels from bottom
        const isNearBottom = (container.scrollHeight - container.clientHeight - container.scrollTop) < threshold;
        if (isNearBottom || force) {
            container.scrollTop = container.scrollHeight;
        }
    };

    // Auto-scroll on new messages
    useEffect(() => {
        if (messages.length === 0) return;
        const lastMsg = messages[messages.length - 1];
        if (lastMsg.role === 'user') {
            scrollToBottom(true);
        } else {
            scrollToBottom(false);
        }
    }, [messages]);

    useEffect(() => {
        if (isLoading) {
            scrollToBottom(true);
        }
    }, [isLoading]);

    useEffect(() => {
        if (isOpen) {
            setTimeout(() => scrollToBottom(true), 50);
        }
    }, [isOpen]);

    const extractHighlightTerm = (query) => {
        if (!query) return '';
        const ruleMatch = query.match(/rule\s*\d+([a-z\(\)\d]*)/i);
        if (ruleMatch) return ruleMatch[0];
        
        const terms = [
            'short term tender', 'emd exemption', 'cvc', 'gfr', 'registration',
            'bid evaluation', 'limited tender', 'corrigendum', 'blacklist'
        ];
        for (const term of terms) {
            if (query.toLowerCase().includes(term)) {
                return term;
            }
        }
        return '';
    };

    const openPdfViewer = (url, targetPageNum, termToHighlight) => {
        console.log("React: openPdfViewer called with:", url, targetPageNum, termToHighlight);
        
        setShowPdf(true);
        setPdfUrl(url);
        
        const filename = url.substring(url.lastIndexOf('/') + 1);
        setPdfTitle(`Document: ${decodeURIComponent(filename)}`);
        const targetPage = parseInt(targetPageNum, 10) || 1;
        setPdfPage(targetPage);
        const searchWord = termToHighlight || '';
        setPdfSearchText(searchWord);
        
        // Wait for ref rendering
        setTimeout(() => {
            loadPdf(url, targetPage, searchWord);
        }, 100);
    };

    const loadPdf = (url, pageNumVal, highlightVal) => {
        if (!window.pdfjsLib) {
            console.error("PDF.js library is not loaded yet.");
            return;
        }
        
        const canvas = pdfCanvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#1e293b';
        ctx.font = '16px sans-serif';
        ctx.fillText('Loading PDF document...', 20, 40);
        
        const cacheBustUrl = url.includes('?') ? `${url}&t=${Date.now()}` : `${url}?t=${Date.now()}`;
        window.pdfjsLib.getDocument(cacheBustUrl).promise.then(pdf => {
            pdfDocRef.current = pdf;
            setPdfPageCount(pdf.numPages);
            renderPdfPage(pageNumVal, highlightVal);
        }).catch(err => {
            console.error("Error loading PDF in React:", err);
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#ef4444';
            ctx.fillText('Error loading PDF: ' + err.message, 20, 40);
        });
    };

    const renderPdfPage = (num, highlightVal = pdfSearchText) => {
        const pdf = pdfDocRef.current;
        if (!pdf) return;
        
        pdfPageRenderingRef.current = true;
        setPdfPage(num);
        
        pdf.getPage(num).then(page => {
            const canvas = pdfCanvasRef.current;
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            
            const container = pdfContainerRef.current;
            const containerWidth = container ? container.clientWidth - 32 : 500;
            const unscaledViewport = page.getViewport({ scale: 1 });
            
            let pageScale = pdfScale;
            if (pdfScale === 'fit' || !pdfScale) {
                pageScale = containerWidth / unscaledViewport.width;
                if (pageScale > 2.0) pageScale = 2.0;
                if (pageScale < 0.5) pageScale = 0.5;
            }
            
            const viewport = page.getViewport({ scale: pageScale });
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            const renderContext = {
                canvasContext: ctx,
                viewport: viewport
            };
            
            page.render(renderContext).promise.then(() => {
                pdfPageRenderingRef.current = false;
                if (pdfPendingPageRef.current !== null) {
                    renderPdfPage(pdfPendingPageRef.current, highlightVal);
                    pdfPendingPageRef.current = null;
                } else {
                    if (highlightVal && highlightVal.trim()) {
                        drawReactHighlights(page, viewport, highlightVal);
                    }
                }
            });
        });
    };

    const queueRenderPdfPage = (num, highlightVal = pdfSearchText) => {
        if (pdfPageRenderingRef.current) {
            pdfPendingPageRef.current = num;
        } else {
            renderPdfPage(num, highlightVal);
        }
    };

    const drawReactHighlights = (page, viewport, term) => {
        page.getTextContent().then(textContent => {
            const canvas = pdfCanvasRef.current;
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const searchLower = term.toLowerCase();
            
            textContent.items.forEach(item => {
                const str = item.str;
                if (!str) return;
                
                const index = str.toLowerCase().indexOf(searchLower);
                if (index !== -1) {
                    const tx = item.transform;
                    const itemWidth = item.width;
                    const itemHeight = item.height || Math.abs(tx[3] || 12);
                    
                    const matchLen = term.length;
                    const totalLen = str.length;
                    
                    let matchWidth = itemWidth;
                    let matchXOffset = 0;
                    
                    if (totalLen > 0) {
                        const charWidth = itemWidth / totalLen;
                        matchXOffset = charWidth * index;
                        matchWidth = charWidth * matchLen;
                    }
                    
                    const pdfRect = [
                        tx[4] + matchXOffset,
                        tx[5],
                        tx[4] + matchXOffset + matchWidth,
                        tx[5] + itemHeight
                    ];
                    
                    const canvasRect = viewport.convertToViewportRectangle(pdfRect);
                    
                    const rectLeft = canvasRect[0];
                    const rectTop = canvasRect[1];
                    const rectWidth = canvasRect[2] - canvasRect[0];
                    const rectHeight = canvasRect[3] - canvasRect[1];
                    
                    ctx.fillStyle = 'rgba(255, 235, 59, 0.4)';
                    ctx.strokeStyle = 'rgba(245, 127, 23, 0.6)';
                    ctx.lineWidth = 1;
                    ctx.fillRect(rectLeft - 2, rectTop - 1, rectWidth + 4, rectHeight + 2);
                    ctx.strokeRect(rectLeft - 2, rectTop - 1, rectWidth + 4, rectHeight + 2);
                }
            });
        });
    };

    const handlePrevPage = () => {
        if (pdfPage <= 1) return;
        queueRenderPdfPage(pdfPage - 1);
    };

    const handleNextPage = () => {
        const pdf = pdfDocRef.current;
        if (!pdf || pdfPage >= pdf.numPages) return;
        queueRenderPdfPage(pdfPage + 1);
    };

    const handleZoomIn = () => {
        let nextScale = pdfScale === 'fit' ? 1.0 : pdfScale + 0.2;
        if (nextScale > 3.0) nextScale = 3.0;
        setPdfScale(nextScale);
    };

    const handleZoomOut = () => {
        let nextScale = pdfScale === 'fit' ? 1.0 : pdfScale - 0.2;
        if (nextScale < 0.5) nextScale = 0.5;
        setPdfScale(nextScale);
    };

    const handleZoomFit = () => {
        setPdfScale('fit');
    };

    // Re-render page when scale state changes
    useEffect(() => {
        if (pdfDocRef.current) {
            renderPdfPage(pdfPage);
        }
    }, [pdfScale]);

    const handlePdfSearchChange = (val) => {
        setPdfSearchText(val);
        if (pdfDocRef.current) {
            renderPdfPage(pdfPage, val);
        }
    };

    const handleGoToPageFromInput = (val) => {
        const pdf = pdfDocRef.current;
        if (!pdf) return;
        let page = parseInt(val, 10);
        if (isNaN(page)) return;
        if (page < 1) page = 1;
        if (page > pdf.numPages) page = pdf.numPages;
        queueRenderPdfPage(page);
    };

    const closePdfViewer = () => {
        setShowPdf(false);
        pdfDocRef.current = null;
    };

    // ── Start session for a role ──────────────────────
    const startSession = async (selectedRole) => {
        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE}/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: selectedRole }),
            });
            const data = await res.json();
            setSessionId(data.session_id);
            setRole(selectedRole);

            const label = selectedRole === 'vendor' ? 'Vendor / Contractor' : 'Government Officer';
            const welcome = selectedRole === 'vendor'
                ? `You are now chatting as a ${label}.\n\nI can help you with:\n- Tender registration and DSC setup\n- EMD and bid submission\n- Portal navigation\n- Short-term tender rules\n\nAsk me anything in English or Hindi.`
                : `You are now chatting as a ${label}.\n\nI can help you with:\n- GFR 2017 procurement rules\n- CVC guidelines and compliance\n- Tender publication and corrigendum\n- Bid evaluation norms\n\nAsk me anything in English or Hindi.`;

            setMessages([{ role: 'assistant', content: welcome }]);
        } catch {
            setMessages([{ role: 'assistant', content: 'Could not connect to the server. Please ensure the backend is running on port 8001.' }]);
        } finally {
            setIsLoading(false);
        }
    };

    // ── Change role ───────────────────────────────────
    const changeRole = () => {
        setRole(null);
        setSessionId(null);
        setMessages([]);
        setIsAdminOpen(false);
    };

    // ── Clear chat ────────────────────────────────────
    const clearChat = () => {
        setMessages([{
            role: 'assistant',
            content: role === 'vendor'
                ? 'Chat cleared. Ask me anything about vendor portal usage.'
                : 'Chat cleared. Ask me anything about procurement rules.',
        }]);
    };

    // ── Save chat ─────────────────────────────────────
    const saveChat = () => {
        let txt = 'CG e-Procurement Assistant – Chat Transcript\n';
        txt += '='.repeat(50) + '\n\n';
        messages.forEach(m => {
            txt += `[${m.role === 'user' ? 'User' : 'Assistant'}]\n${m.content}\n\n`;
        });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([txt], { type: 'text/plain;charset=utf-8' }));
        a.download = `cg_chat_${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
        URL.revokeObjectURL(a.href);
    };

    // ── Admin diagnostics & config functions ───────────
    const fetchAnalytics = async () => {
        try {
            const res = await fetch(`${API_BASE}/admin/analytics`);
            if (res.ok) {
                const data = await res.json();
                setAdminAnalytics(data);
            }
        } catch (err) {
            console.error('Error fetching admin analytics:', err);
        }
    };

    const openAdminPanel = () => {
        setAdminSearch('');
        setAdminRoleFilter('all');
        setAdminFeedbackFilter('all');
        setIsAdminOpen(true);
        setAdminTab('dashboard');
        fetchAnalytics();
    };

    const switchAdminTab = (tabName) => {
        setAdminTab(tabName);
        if (tabName === 'dashboard') {
            fetchAnalytics();
        } else if (tabName === 'sessions') {
            fetchActiveSessions();
        } else if (tabName === 'engine') {
            fetchAdminConfig();
        } else if (tabName === 'governance') {
            fetchGovernanceDocs();
        } else if (tabName === 'overrides') {
            fetchAdminConfig();
        } else if (tabName === 'hallucination') {
            fetchAnalytics();
            fetchAdminConfig();
        }
    };

    const fetchActiveSessions = async () => {
        try {
            const res = await fetch(`${API_BASE}/admin/sessions`);
            if (res.ok) {
                const data = await res.json();
                setActiveSessions(data);
            }
        } catch (err) {
            console.error('Error fetching active sessions:', err);
        }
    };

    const killSession = async (sessId) => {
        if (!window.confirm('Are you sure you want to terminate this session?')) return;
        try {
            const res = await fetch(`${API_BASE}/admin/sessions/${sessId}`, { method: 'DELETE' });
            if (res.ok) {
                fetchActiveSessions();
            }
        } catch (err) {
            console.error('Error terminating session:', err);
        }
    };

    const fetchAdminConfig = async () => {
        try {
            const res = await fetch(`${API_BASE}/admin/config`);
            if (res.ok) {
                const data = await res.json();
                setAdminConfig(data);
            }
        } catch (err) {
            console.error('Error fetching admin config:', err);
        }
    };

    const fetchGovernanceDocs = async () => {
        try {
            let currentConfig = adminConfig;
            if (!currentConfig) {
                const resConfig = await fetch(`${API_BASE}/admin/config`);
                if (resConfig.ok) {
                    currentConfig = await resConfig.json();
                    setAdminConfig(currentConfig);
                }
            }
            const resDocs = await fetch(`${API_BASE}/admin/documents`);
            if (resDocs.ok) {
                const data = await resDocs.json();
                setDocuments(data);
            }
        } catch (err) {
            console.error('Error fetching governance docs:', err);
        }
    };

    const saveAdminConfig = async (updatedConfig = adminConfig) => {
        try {
            const res = await fetch(`${API_BASE}/admin/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedConfig),
            });
            if (res.ok) {
                setAdminConfig(updatedConfig);
                return true;
            }
        } catch (err) {
            console.error('Error saving admin config:', err);
        }
        return false;
    };

    const updateConfigParam = (section, key, val) => {
        setAdminConfig(prev => {
            if (!prev) return prev;
            if (section) {
                return {
                    ...prev,
                    [section]: {
                        ...prev[section],
                        [key]: val
                    }
                };
            }
            return {
                ...prev,
                [key]: val
            };
        });
    };

    const toggleDocumentActive = (docName, active) => {
        setAdminConfig(prev => {
            if (!prev) return prev;
            const deactivated = prev.deactivated_documents || [];
            let nextDeactivated;
            if (active) {
                nextDeactivated = deactivated.filter(d => d !== docName);
            } else {
                nextDeactivated = [...deactivated, docName];
            }
            return {
                ...prev,
                deactivated_documents: nextDeactivated
            };
        });
    };

    const saveEngineSettings = async () => {
        const success = await saveAdminConfig();
        if (success) {
            alert('Engine parameters and prompts saved successfully!');
        } else {
            alert('Failed to save engine settings.');
        }
    };

    const saveDocumentSettings = async () => {
        const success = await saveAdminConfig();
        if (success) {
            alert('Document governance checklist saved successfully!');
        } else {
            alert('Failed to save document settings.');
        }
    };

    const addFaqOverride = async () => {
        if (!faqQuery.trim() || !faqAnswer.trim() || !adminConfig) return;
        const updated = {
            ...adminConfig,
            qa_overrides: [
                ...(adminConfig.qa_overrides || []),
                { query: faqQuery.trim(), answer: faqAnswer.trim() }
            ]
        };
        const success = await saveAdminConfig(updated);
        if (success) {
            setFaqQuery('');
            setFaqAnswer('');
        }
    };

    const deleteFaqOverride = async (idx) => {
        if (!adminConfig) return;
        const nextOverrides = [...(adminConfig.qa_overrides || [])];
        nextOverrides.splice(idx, 1);
        const updated = {
            ...adminConfig,
            qa_overrides: nextOverrides
        };
        await saveAdminConfig(updated);
    };

    const addBlacklistRule = async () => {
        if (!blPattern.trim() || !blResponse.trim() || !adminConfig) return;
        const updated = {
            ...adminConfig,
            blacklist_rules: [
                ...(adminConfig.blacklist_rules || []),
                { pattern: blPattern.trim(), response: blResponse.trim() }
            ]
        };
        const success = await saveAdminConfig(updated);
        if (success) {
            setBlPattern('');
            setBlResponse('');
        }
    };

    const deleteBlacklistRule = async (idx) => {
        if (!adminConfig) return;
        const nextRules = [...(adminConfig.blacklist_rules || [])];
        nextRules.splice(idx, 1);
        const updated = {
            ...adminConfig,
            blacklist_rules: nextRules
        };
        await saveAdminConfig(updated);
    };

    const addGlossaryTerm = async () => {
        if (!glossaryTerm.trim() || !adminConfig) return;
        const term = glossaryTerm.trim();
        const existing = adminConfig.protected_terms || [];
        if (existing.includes(term)) return;
        const updated = {
            ...adminConfig,
            protected_terms: [...existing, term]
        };
        const success = await saveAdminConfig(updated);
        if (success) {
            setGlossaryTerm('');
        }
    };

    const deleteGlossaryTerm = async (idx) => {
        if (!adminConfig) return;
        const nextTerms = [...(adminConfig.protected_terms || [])];
        nextTerms.splice(idx, 1);
        const updated = {
            ...adminConfig,
            protected_terms: nextTerms
        };
        await saveAdminConfig(updated);
    };

    const applyHallucinationCorrection = async (queryText) => {
        const correction = corrections[queryText]?.trim();
        if (!correction || !adminConfig) return;

        const nextCorrections = (adminConfig.hallucination_corrections || []).filter(
            hc => hc.query.toLowerCase() !== queryText.toLowerCase()
        );

        const updated = {
            ...adminConfig,
            hallucination_corrections: [
                ...nextCorrections,
                { query: queryText, answer: correction }
            ]
        };

        const success = await saveAdminConfig(updated);
        if (success) {
            alert('Correction applied and saved as override!');
            setCorrections(prev => {
                const next = { ...prev };
                delete next[queryText];
                return next;
            });
        }
    };

    const deleteHallucinationCorrection = async (queryText) => {
        if (!adminConfig) return;
        if (!window.confirm(`Are you sure you want to delete the correction/override for: "${queryText}"?`)) return;

        const nextCorrections = (adminConfig.hallucination_corrections || []).filter(
            hc => hc.query.toLowerCase() !== queryText.toLowerCase()
        );
        const nextOverrides = (adminConfig.qa_overrides || []).filter(
            qa => qa.query.toLowerCase() !== queryText.toLowerCase()
        );

        const updated = {
            ...adminConfig,
            hallucination_corrections: nextCorrections,
            qa_overrides: nextOverrides
        };

        const success = await saveAdminConfig(updated);
        if (success) {
            alert('Correction deleted successfully!');
            setCorrections(prev => {
                const next = { ...prev };
                delete next[queryText];
                return next;
            });
        }
    };

    const exportPdf = () => {
        window.open(`${API_BASE}/admin/export_pdf`, '_blank');
    };

    const submitFeedback = async (logId, feedbackVal, messageIndex) => {
        if (!logId) return;
        try {
            const res = await fetch(`${API_BASE}/chat/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ log_id: logId, feedback: feedbackVal }),
            });
            if (res.ok) {
                setMessages(prev => {
                    const next = [...prev];
                    next[messageIndex] = {
                        ...next[messageIndex],
                        userFeedback: feedbackVal
                    };
                    return next;
                });
            }
        } catch (err) {
            console.error('Error submitting feedback:', err);
        }
    };

    // ── Send message ──────────────────────────────────
    const sendMessage = async (textOverride) => {
        const queryText = (typeof textOverride === 'string' ? textOverride : input).trim();
        if (!queryText || isLoading || !sessionId) return;
        const q = queryText;

        if (q.toUpperCase() === 'I WANT TO KNOW...') {
            setInput('');
            openAdminPanel();
            return;
        }

        lastUserQueryRef.current = q;
        setMessages(prev => [...prev, { role: 'user', content: q }]);
        setInput('');
        setIsLoading(true);
        setResponseTime(null);

        const startTime = performance.now();

        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q, session_id: sessionId }),
            });
            if (!res.ok) throw new Error('HTTP ' + res.status);

            const reader = res.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            // Add initial empty assistant message bubble
            setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [], ruleCitations: [] }]);
            setIsLoading(false);

            let currentText = '';
            let sources = [];
            let ruleCitations = [];

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // keep partial line

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed.startsWith('data: ')) continue;

                    try {
                        const parsed = JSON.parse(trimmed.slice(6));
                        if (parsed.type === 'start') {
                            sources = parsed.sources || [];
                            const sourceRefs = parsed.source_refs || [];
                            ruleCitations = parsed.rule_citations || [];
                            setDetectedLang(parsed.detected_language || 'en');
                            setMessages(prev => {
                                const next = [...prev];
                                const last = next[next.length - 1];
                                next[next.length - 1] = {
                                    ...last,
                                    sources: sources,
                                    sourceRefs: sourceRefs,
                                    ruleCitations: ruleCitations,
                                    logId: parsed.log_id || null
                                };
                                return next;
                            });
                        } else if (parsed.type === 'token') {
                            currentText += parsed.text;
                            setMessages(prev => {
                                const next = [...prev];
                                const last = next[next.length - 1];
                                next[next.length - 1] = {
                                    ...last,
                                    content: currentText
                                };
                                return next;
                            });
                        } else if (parsed.type === 'replace') {
                            currentText = parsed.text;
                            setMessages(prev => {
                                const next = [...prev];
                                const last = next[next.length - 1];
                                next[next.length - 1] = {
                                    ...last,
                                    content: currentText
                                };
                                return next;
                            });
                        }
                    } catch (e) {
                        console.error('Error parsing SSE chunk:', e);
                    }
                }
            }

            const duration = ((performance.now() - startTime) / 1000).toFixed(2);
            setResponseTime(duration);

            setMessages(prev => {
                const next = [...prev];
                const last = next[next.length - 1];
                next[next.length - 1] = {
                    ...last,
                    duration: duration
                };
                return next;
            });

        } catch (err) {
            console.error('Fetch error:', err);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, there was an error connecting to the server. Please check that the backend is running.',
            }]);
            setIsLoading(false);
        }
    };

    const onKey = (e) => { if (e.key === 'Enter') sendMessage(); };

    // ── Render ────────────────────────────────────────
    const filteredQueries = (adminAnalytics?.queries || []).filter(q => {
        const matchesSearch = !adminSearch || (q.query || '').toLowerCase().includes(adminSearch.toLowerCase());
        const matchesRole = adminRoleFilter === 'all' || q.role === adminRoleFilter;
        const matchesFeedback = adminFeedbackFilter === 'all' || q.feedback === adminFeedbackFilter;
        return matchesSearch && matchesRole && matchesFeedback;
    });
    const unsatisfiedQueries = (adminAnalytics?.queries || []).filter(q => q.feedback === 'unsatisfied');

    return (
        <div className={`cg-chat-container ${showPdf ? 'with-pdf' : ''}`}>
            {/* Launcher */}
            {!isOpen && (
                <button className="cg-chat-toggle" onClick={() => setIsOpen(true)} title="Open CG e-Procurement Assistant">
                    <svg viewBox="0 0 24 24" width="28" height="28" fill="white">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
                    </svg>
                </button>
            )}

            {/* Chat window */}
            {isOpen && (
                <div className={`cg-chat-window ${showPdf ? 'with-pdf' : ''}`}>
                    <div className="cg-chat-main-panel">

                    {/* Header */}
                    <div className="cg-chat-header">
                        <div>
                            <h3>🤖 CG e-Procurement Assistant</h3>
                            {role && (
                                <div style={{ fontSize: 11, opacity: 0.8, marginTop: 2 }}>
                                    Chatting as {role === 'vendor' ? 'Vendor / Contractor' : 'Government Officer'}
                                </div>
                            )}
                        </div>
                        <div style={{ display: 'flex', gap: 6 }}>
                            {role && (
                                <button className="cg-close-btn" onClick={clearChat} title="Clear chat" style={{ fontSize: 16 }}>
                                    &#x1F5D1;
                                </button>
                            )}
                            {role && (
                                <button className="cg-close-btn" onClick={saveChat} title="Save chat" style={{ fontSize: 16 }}>
                                    &#x1F4BE;
                                </button>
                            )}
                            <button className="cg-close-btn" onClick={() => setIsOpen(false)} title="Close">&#x2715;</button>
                        </div>
                    </div>

                    {/* Role selector — shown when no role is selected */}
                    {!role && (
                        <div className="cg-role-selector" style={{ flexDirection: 'column', padding: 20, gap: 14, flex: 1, justifyContent: 'center', alignItems: 'center', background: '#fdfaf2' }}>
                            <div style={{ fontSize: 18, fontWeight: 700, color: '#222', textAlign: 'center' }}>
                                Select Your Role
                            </div>
                            <div style={{ fontSize: 13, color: '#666', textAlign: 'center', marginBottom: 6 }}>
                                Choose your role to get personalised assistance
                            </div>
                            <button
                                className="cg-role-btn"
                                style={{ width: '100%', maxWidth: 300, padding: '14px 16px', background: 'white', border: '2px solid #e0e0e0', borderLeft: '5px solid #628ec8', borderRadius: 12, cursor: 'pointer', textAlign: 'left', fontSize: 14 }}
                                onClick={() => startSession('vendor')}
                                disabled={isLoading}
                            >
                                <div style={{ fontWeight: 700, color: '#222', marginBottom: 4 }}>Vendor / Contractor</div>
                                <div style={{ fontSize: 12, color: '#777' }}>Registration, bids, EMD, DSC, tender participation</div>
                            </button>
                            <button
                                className="cg-role-btn"
                                style={{ width: '100%', maxWidth: 300, padding: '14px 16px', background: 'white', border: '2px solid #e0e0e0', borderLeft: '5px solid #4a74aa', borderRadius: 12, cursor: 'pointer', textAlign: 'left', fontSize: 14 }}
                                onClick={() => startSession('government_officer')}
                                disabled={isLoading}
                            >
                                <div style={{ fontWeight: 700, color: '#222', marginBottom: 4 }}>Government Officer</div>
                                <div style={{ fontSize: 12, color: '#777' }}>GFR rules, procurement compliance, CVC guidelines</div>
                            </button>
                        </div>
                    )}

                    {/* Chat area — shown after role is selected */}
                    {role && (
                        <>
                            {/* Role badge */}
                            <div className="cg-role-selector" style={{ justifyContent: 'space-between', alignItems: 'center', padding: '10px 15px', background: '#f8f9fa', borderBottom: '1px solid #eee' }}>
                                <span style={{ fontSize: 13, fontWeight: 600, color: '#333' }}>
                                    Role: <span style={{ color: '#628ec8' }}>{role === 'vendor' ? 'Vendor / Contractor' : 'Government Officer'}</span>
                                </span>
                                <button
                                    className="cg-role-btn"
                                    style={{ padding: '4px 12px', fontSize: 12, background: 'none', color: '#628ec8', border: '1px solid #628ec8', borderRadius: 20, cursor: 'pointer' }}
                                    onClick={changeRole}
                                >
                                    Change Role
                                </button>
                            </div>

                            {/* Messages */}
                            <div className="cg-messages-area" ref={messagesContainerRef}>
                                {messages.map((msg, idx) => (
                                    <div key={idx} className={`cg-message ${msg.role}`}>
                                        <div className="cg-message-bubble">
                                            {parseMarkdownToReact(msg.content, msg.sourceRefs, msg.ruleCitations, openPdfViewer)}
                                            
                                              {msg.role === 'assistant' && ((msg.sourceRefs && msg.sourceRefs.length > 0) || (msg.sources && msg.sources.length > 0)) && (
                                                <div className="cg-sources-box" style={{ marginTop: '10px' }}>
                                                    <strong style={{ display: 'block', marginBottom: '4px' }}>
                                                        {msg.sources && msg.sources.includes('Admin Override') && !(msg.sourceRefs && msg.sourceRefs.length > 0) ? 'Response Source:' : 'Reference Documents:'}
                                                    </strong>
                                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                                        {msg.sourceRefs && msg.sourceRefs.length > 0 ? (
                                                            msg.sourceRefs.map((refItem, rIdx) => {
                                                                const docBaseUrl = `${API_BASE.replace('/api/v1', '')}/docs/${refItem.category}/${refItem.file}`;
                                                                const docUrl = refItem.url.startsWith('http') ? refItem.url : `${API_BASE.replace('/api/v1', '')}${refItem.url}`;
                                                                const highlightTerm = msg.ruleCitations && msg.ruleCitations.length > 0 ? msg.ruleCitations[0] : extractHighlightTerm(lastUserQueryRef.current);
                                                                const firstPage = refItem.pages && refItem.pages.length > 0 ? refItem.pages[0] : 1;
                                                                
                                                                return (
                                                                    <div key={rIdx} className="cg-source-chip" style={{
                                                                        display: 'flex',
                                                                        alignItems: 'center',
                                                                        gap: '6px',
                                                                        background: '#eaf5ed',
                                                                        border: '1px solid #c2e5cb',
                                                                        borderRadius: '12px',
                                                                        padding: '4px 10px',
                                                                        fontSize: '11px',
                                                                        color: '#628ec8',
                                                                        fontWeight: '500'
                                                                    }}>
                                                                        <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                                                                            {refItem.file === 'Learned satisfied Q&As' ? (
                                                                                <span style={{ fontWeight: '600', marginLeft: '4px', color: '#4a5568' }}>
                                                                                    🧠 Learned Q&A
                                                                                </span>
                                                                            ) : (
                                                                                <>
                                                                                    📄 <a href={docUrl} onClick={(e) => { e.preventDefault(); openPdfViewer(docBaseUrl, firstPage, highlightTerm); }} style={{
                                                                                        color: '#628ec8',
                                                                                        textDecoration: 'none',
                                                                                        fontWeight: '600',
                                                                                        marginLeft: '4px',
                                                                                        cursor: 'pointer'
                                                                                    }} className="cg-source-link">
                                                                                        {refItem.file}
                                                                                    </a>
                                                                                </>
                                                                            )}
                                                                        </span>
                                                                        {refItem.pages && refItem.pages.length > 0 && refItem.file !== 'Learned satisfied Q&As' && (
                                                                            <span style={{ color: '#555', fontSize: '10px', display: 'flex', gap: '3px', marginLeft: '4px' }}>
                                                                                (p. {refItem.pages.map((p, pIdx) => (
                                                                                    <a key={pIdx} href={`${docBaseUrl}#page=${p}`} onClick={(e) => { e.preventDefault(); openPdfViewer(docBaseUrl, p, highlightTerm); }} className="cg-page-num-link" style={{
                                                                                        color: '#4a74aa',
                                                                                        textDecoration: 'underline',
                                                                                        fontWeight: 'bold',
                                                                                        marginRight: pIdx < refItem.pages.length - 1 ? '2px' : '0px',
                                                                                        cursor: 'pointer'
                                                                                    }}>
                                                                                        {p}
                                                                                    </a>
                                                                                ))})
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                );
                                                            })
                                                        ) : (
                                                            msg.sources.map((src, sIdx) => {
                                                                const isAdminOverride = src === 'Admin Override';
                                                                return (
                                                                    <span key={sIdx} style={{
                                                                        background: isAdminOverride ? '#fef3c7' : '#f1f1f1',
                                                                        border: isAdminOverride ? '1px solid #fde68a' : '1px solid #e0e0e0',
                                                                        borderRadius: '8px',
                                                                        padding: '4px 10px',
                                                                        fontSize: '11px',
                                                                        color: isAdminOverride ? '#b45309' : '#666',
                                                                        fontWeight: isAdminOverride ? '700' : 'normal'
                                                                    }}>
                                                                        {isAdminOverride ? '🎯 ' + src : src}
                                                                    </span>
                                                                );
                                                            })
                                                        )}
                                                    </div>
                                                </div>
                                            )}

                                            {msg.role === 'assistant' && msg.duration && (
                                                <div style={{ fontSize: '10px', color: '#aaa', marginTop: '5px', textAlign: 'right' }}>
                                                    Response: {msg.duration}s
                                                </div>
                                            )}

                                            {/* Feedback Actions */}
                                            {msg.role === 'assistant' && msg.logId && (
                                                <div className="cg-feedback-actions">
                                                    <button
                                                        className={`cg-feedback-btn ${msg.userFeedback === 'satisfied' ? 'selected' : ''}`}
                                                        style={msg.userFeedback && msg.userFeedback !== 'satisfied' ? { opacity: 0.15, pointerEvents: 'none' } : {}}
                                                        onClick={() => submitFeedback(msg.logId, 'satisfied', idx)}
                                                        title="Thumbs Up"
                                                    >
                                                        👍
                                                    </button>
                                                    <button
                                                        className={`cg-feedback-btn ${msg.userFeedback === 'unsatisfied' ? 'selected' : ''}`}
                                                        style={msg.userFeedback && msg.userFeedback !== 'unsatisfied' ? { opacity: 0.15, pointerEvents: 'none' } : {}}
                                                        onClick={() => submitFeedback(msg.logId, 'unsatisfied', idx)}
                                                        title="Thumbs Down"
                                                    >
                                                        👎
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                                {isLoading && (
                                    <div className="cg-message assistant">
                                        <div className="cg-typing-indicator">
                                            <span /><span /><span />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Suggestion Chips */}
                            {role && (
                                <div className="cg-chips-container">
                                    {(role === 'vendor' ? VENDOR_CHIPS : OFFICER_CHIPS).map((text, idx) => (
                                        <button
                                            key={idx}
                                            className="cg-chip-btn"
                                            onClick={() => sendMessage(text)}
                                            disabled={isLoading}
                                        >
                                            {text}
                                        </button>
                                    ))}
                                </div>
                            )}

                            {/* Input */}
                            <div className="cg-input-area">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={e => setInput(e.target.value)}
                                    onKeyPress={onKey}
                                    placeholder={detectedLang === 'hi' ? 'अपना प्रश्न लिखें...' : 'Type your question...'}
                                    disabled={isLoading}
                                />
                                <button onClick={sendMessage} disabled={isLoading || !input.trim()}>Send</button>
                            </div>

                            {/* Footer */}
                            <div className="cg-lang-footer" style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 12px', textAlign: 'left' }}>
                                <span>{detectedLang === 'hi' ? 'Hindi' : (detectedLang === 'hi-Latn' ? 'Hinglish' : 'English')}</span>
                                {responseTime && <span style={{ color: '#64748b', fontWeight: 'normal' }}>Response: {responseTime}s</span>}
                            </div>
                        </>
                    )}

                    {/* Admin Diagnostics Overlay Panel */}
                    {isAdminOpen && (
                        <div className="cg-admin-panel">
                            <div className="cg-admin-header">
                                <div className="cg-admin-title">📊 Admin Governance Cockpit</div>
                                <button className="cg-admin-close-btn" onClick={() => setIsAdminOpen(false)}>Close Panel</button>
                            </div>
                            
                            {/* Admin Tabs Nav */}
                            <div className="admin-tabs">
                                <button className={`admin-tab-btn ${adminTab === 'dashboard' ? 'active' : ''}`} onClick={() => switchAdminTab('dashboard')}>Dashboard</button>
                                <button className={`admin-tab-btn ${adminTab === 'sessions' ? 'active' : ''}`} onClick={() => switchAdminTab('sessions')}>Sessions Watcher</button>
                                <button className={`admin-tab-btn ${adminTab === 'engine' ? 'active' : ''}`} onClick={() => switchAdminTab('engine')}>Engine Params</button>
                                <button className={`admin-tab-btn ${adminTab === 'governance' ? 'active' : ''}`} onClick={() => switchAdminTab('governance')}>Doc Governance</button>
                                <button className={`admin-tab-btn ${adminTab === 'overrides' ? 'active' : ''}`} onClick={() => switchAdminTab('overrides')}>Rules & Overrides</button>
                                <button className={`admin-tab-btn ${adminTab === 'hallucination' ? 'active' : ''}`} onClick={() => switchAdminTab('hallucination')}>Hallucination Review</button>
                            </div>

                            {/* Tab 1: Dashboard */}
                            {adminTab === 'dashboard' && (
                                <div className="admin-tab-content active">
                                    <div className="cg-admin-kpi-grid">
                                        <div className="cg-admin-kpi-card">
                                            <div className="cg-admin-kpi-value">{adminAnalytics?.total_queries || 0}</div>
                                            <div className="cg-admin-kpi-label">Total Queries</div>
                                        </div>
                                        <div className="cg-admin-kpi-card">
                                            <div className="cg-admin-kpi-value">{(adminAnalytics?.avg_response_time || 0).toFixed(2)}s</div>
                                            <div className="cg-admin-kpi-label">Avg Speed</div>
                                        </div>
                                        <div className="cg-admin-kpi-card">
                                            <div className="cg-admin-kpi-value">{(adminAnalytics?.satisfaction_rate || 0).toFixed(1)}%</div>
                                            <div className="cg-admin-kpi-label">Satisfaction</div>
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexShrink: 0 }}>
                                        <span className="cg-admin-section-title" style={{ marginBottom: 0 }}>📋 Query Logs</span>
                                        <button className="admin-btn" onClick={exportPdf}>📥 Export PDF Report</button>
                                    </div>

                                    <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexShrink: 0 }}>
                                        <input
                                            type="text"
                                            value={adminSearch}
                                            onChange={e => setAdminSearch(e.target.value)}
                                            placeholder="Search queries..."
                                            style={{ flex: 1, padding: '6px 10px', border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 11, outline: 'none', boxSizing: 'border-box' }}
                                        />
                                        <select
                                            value={adminRoleFilter}
                                            onChange={e => setAdminRoleFilter(e.target.value)}
                                            style={{ padding: '6px 10px', border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 11, outline: 'none', background: 'white', boxSizing: 'border-box' }}
                                        >
                                            <option value="all">All Roles</option>
                                            <option value="vendor">Vendor</option>
                                            <option value="government_officer">Officer</option>
                                        </select>
                                        <select
                                            value={adminFeedbackFilter}
                                            onChange={e => setAdminFeedbackFilter(e.target.value)}
                                            style={{ padding: '6px 10px', border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 11, outline: 'none', background: 'white', boxSizing: 'border-box' }}
                                        >
                                            <option value="all">All Feedback</option>
                                            <option value="satisfied">Satisfied</option>
                                            <option value="unsatisfied">Unsatisfied</option>
                                            <option value="neutral">Neutral</option>
                                        </select>
                                    </div>

                                    <div style={{ fontSize: 10, color: '#64748b', marginBottom: 6, fontWeight: 600, flexShrink: 0 }}>
                                        Showing {filteredQueries.length} of {(adminAnalytics?.queries || []).length} loaded queries (Total stored: {adminAnalytics?.total_queries || 0})
                                    </div>

                                    <div className="cg-admin-table-container">
                                        <table className="cg-admin-table">
                                            <thead>
                                                <tr>
                                                    <th>Timestamp</th>
                                                    <th>Role</th>
                                                    <th>Query</th>
                                                    <th>Speed</th>
                                                    <th>Feedback</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {filteredQueries && filteredQueries.length > 0 ? (
                                                    filteredQueries.map((q, i) => {
                                                        const timeStr = q.timestamp ? new Date(q.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
                                                        return (
                                                            <tr key={i}>
                                                                <td>{timeStr}</td>
                                                                <td>{q.role === 'government_officer' ? 'Officer' : 'Vendor'}</td>
                                                                <td title={q.query}>{q.query}</td>
                                                                <td>{(q.response_time_seconds || 0).toFixed(2)}s</td>
                                                                <td>
                                                                    <span className={`cg-feedback-badge ${q.feedback}`}>
                                                                        {q.feedback}
                                                                    </span>
                                                                </td>
                                                            </tr>
                                                        );
                                                    })
                                                ) : (
                                                    <tr>
                                                        <td colSpan="5" style={{ textAlign: 'center', color: '#64748b' }}>
                                                            No matching query logs available.
                                                        </td>
                                                    </tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>

                                    <div className="cg-admin-section-title" style={{ marginTop: 10, marginBottom: 4 }}>🔥 Top Asked Terms</div>
                                    <div className="cg-admin-topic-tags" style={{ marginBottom: 0 }}>
                                        {adminAnalytics?.most_asked_topics && adminAnalytics.most_asked_topics.length > 0 ? (
                                            adminAnalytics.most_asked_topics.map((topic, i) => (
                                                <span key={i} className="cg-admin-topic-tag">{topic}</span>
                                            ))
                                        ) : (
                                            <span style={{ fontSize: 11, color: '#64748b' }}>No topics logged yet.</span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Tab 2: Sessions Watcher */}
                            {adminTab === 'sessions' && (
                                <div className="admin-tab-content active">
                                    <div className="cg-admin-section-title">👥 Active User Sessions</div>
                                    <div style={{ flexGrow: 1, overflowY: 'auto', marginBottom: 8 }}>
                                        {activeSessions && activeSessions.length > 0 ? (
                                            activeSessions.map((sess, i) => {
                                                const timeStr = sess.last_activity ? new Date(sess.last_activity).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
                                                return (
                                                    <div key={i} className="session-card">
                                                        <div className="session-card-header">
                                                            <span>Session: {sess.session_id.slice(0, 8)}... ({sess.role === 'government_officer' ? 'Officer' : 'Vendor'}) - Active: {timeStr}</span>
                                                            <button className="session-card-kill-btn" onClick={() => killSession(sess.session_id)}>Terminate</button>
                                                        </div>
                                                        <div style={{ maxHeight: 100, overflowY: 'auto' }}>
                                                            {sess.history && sess.history.length > 0 ? (
                                                                sess.history.map((h, j) => (
                                                                    <div key={j} className="session-history-item">
                                                                        <strong>Q:</strong> {h.query}<br/>
                                                                        <strong>A:</strong> {h.response.slice(0, 100)}{h.response.length > 100 ? '...' : ''}
                                                                    </div>
                                                                ))
                                                            ) : (
                                                                <div style={{ fontSize: 9, color: '#888', paddingLeft: 6 }}>No messages sent in this session yet.</div>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })
                                        ) : (
                                            <p style={{ fontSize: 11, color: '#64748b', textAlign: 'center' }}>No active sessions.</p>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Tab 3: Engine Params */}
                            {adminTab === 'engine' && (
                                <div className="admin-tab-content active">
                                    <div className="cg-admin-section-title">⚙️ Tuning Parameters</div>
                                    <div className="admin-form-group">
                                        <label>Retrieval Depth (k = {adminConfig?.engine_params?.k ?? 7})</label>
                                        <input
                                            type="range"
                                            min="1"
                                            max="15"
                                            step="1"
                                            value={adminConfig?.engine_params?.k ?? 7}
                                            onChange={e => updateConfigParam('engine_params', 'k', parseInt(e.target.value, 10))}
                                        />
                                    </div>
                                    <div className="admin-form-group">
                                        <label>Max Context Length ({adminConfig?.engine_params?.max_context_chars ?? 4000} chars)</label>
                                        <input
                                            type="range"
                                            min="1000"
                                            max="10000"
                                            step="500"
                                            value={adminConfig?.engine_params?.max_context_chars ?? 4000}
                                            onChange={e => updateConfigParam('engine_params', 'max_context_chars', parseInt(e.target.value, 10))}
                                        />
                                    </div>
                                    <div className="admin-form-group">
                                        <label>LLM Temperature (temp = {adminConfig?.engine_params?.temperature ?? 0.0})</label>
                                        <input
                                            type="range"
                                            min="0.0"
                                            max="1.0"
                                            step="0.1"
                                            value={adminConfig?.engine_params?.temperature ?? 0.0}
                                            onChange={e => updateConfigParam('engine_params', 'temperature', parseFloat(e.target.value))}
                                        />
                                    </div>
                                    <div className="admin-form-group" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <input
                                            type="checkbox"
                                            checked={!!adminConfig?.translation_enabled}
                                            onChange={e => updateConfigParam(null, 'translation_enabled', e.target.checked)}
                                            style={{ margin: 0, cursor: 'pointer', width: 'auto' }}
                                        />
                                        <label style={{ margin: 0, cursor: 'pointer', fontSize: 11 }}>Enable Hindi/English Translation Service</label>
                                    </div>

                                    <div className="cg-admin-section-title" style={{ marginTop: 12 }}>🎭 Persona Prompt Editor</div>
                                    <div className="admin-form-group">
                                        <label>Vendor Persona Prompt Template</label>
                                        <textarea
                                            value={adminConfig?.vendor_prompt ?? ''}
                                            onChange={e => updateConfigParam(null, 'vendor_prompt', e.target.value)}
                                            style={{ minHeight: 80 }}
                                        />
                                    </div>
                                    <div className="admin-form-group">
                                        <label>Government Officer Persona Prompt Template</label>
                                        <textarea
                                            value={adminConfig?.officer_prompt ?? ''}
                                            onChange={e => updateConfigParam(null, 'officer_prompt', e.target.value)}
                                            style={{ minHeight: 80 }}
                                        />
                                    </div>

                                    <button className="admin-btn" onClick={saveEngineSettings}>Save Engine Settings</button>
                                </div>
                            )}

                            {/* Tab 4: Doc Governance */}
                            {adminTab === 'governance' && (
                                <div className="admin-tab-content active">
                                    <div className="cg-admin-section-title">📚 Document Inventory Governance</div>
                                    <p style={{ fontSize: 10, color: '#64748b', marginTop: 0, marginBottom: 10 }}>Uncheck a document to temporarily exclude its chunks from vector search.</p>
                                    <div style={{ flexGrow: 1, overflowY: 'auto', marginBottom: 8 }}>
                                        {documents && documents.length > 0 ? (
                                            documents.map((docName, i) => (
                                                <div key={i} className="document-governance-item">
                                                    <input
                                                        type="checkbox"
                                                        id={`gov_doc_${i}`}
                                                        checked={!adminConfig?.deactivated_documents?.includes(docName)}
                                                        onChange={e => toggleDocumentActive(docName, e.target.checked)}
                                                        style={{ margin: 0, cursor: 'pointer', width: 'auto' }}
                                                    />
                                                    <label htmlFor={`gov_doc_${i}`} style={{ cursor: 'pointer', wordBreak: 'break-all' }}>{docName}</label>
                                                </div>
                                            ))
                                        ) : (
                                            <p style={{ fontSize: 11, color: '#64748b' }}>No documents found in database.</p>
                                        )}
                                    </div>
                                    <button className="admin-btn" onClick={saveDocumentSettings}>Save Document Settings</button>
                                </div>
                            )}

                            {/* Tab 5: Rules & Overrides */}
                            {adminTab === 'overrides' && (
                                <div className="admin-tab-content active">
                                    {/* FAQ Overrides */}
                                    <div className="cg-admin-section-title">🎯 FAQ Overrides (Bypass LLM)</div>
                                    <div className="admin-form-group" style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 8 }}>
                                         <div style={{ display: 'flex', gap: 6 }}>
                                             <input type="text" placeholder="User query pattern..." value={faqQuery} onChange={e => setFaqQuery(e.target.value)} style={{ flex: 1, padding: '6px 10px', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '11px', outline: 'none', boxSizing: 'border-box' }} />
                                             <button className="admin-btn" onClick={addFaqOverride} style={{ flexShrink: 0 }}>Add Override</button>
                                         </div>
                                         <textarea placeholder="Bypassed answer response (Markdown supported)..." value={faqAnswer} onChange={e => setFaqAnswer(e.target.value)} style={{ width: '100%', minHeight: '80px', padding: '6px 10px', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '11px', fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box', resize: 'vertical' }}></textarea>
                                     </div>
                                    <div style={{ maxHeight: 90, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: 6, marginBottom: 12, background: 'white' }}>
                                        <table className="rules-table" style={{ margin: 0 }}>
                                            <thead>
                                                <tr>
                                                    <th>Query</th>
                                                    <th>Override Answer</th>
                                                    <th style={{ width: 40, textAlign: 'center' }}>Act</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {adminConfig?.qa_overrides && adminConfig.qa_overrides.length > 0 ? (
                                                    adminConfig.qa_overrides.map((qa, i) => (
                                                        <tr key={i}>
                                                            <td>{qa.query}</td>
                                                            <td>{qa.answer}</td>
                                                            <td style={{ textAlign: 'center' }}>
                                                                <button className="admin-btn danger" style={{ padding: '2px 6px', fontSize: 9 }} onClick={() => deleteFaqOverride(i)}>Del</button>
                                                            </td>
                                                        </tr>
                                                    ))
                                                ) : (
                                                    <tr><td colSpan="3" style={{ textAlign: 'center', color: '#64748b' }}>No FAQ overrides.</td></tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>

                                    {/* Blacklist Rules */}
                                    <div className="cg-admin-section-title">🚫 Blacklist Rules (Block Queries)</div>
                                    <div className="admin-form-group" style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
                                        <input type="text" placeholder="Regex / Keyword..." value={blPattern} onChange={e => setBlPattern(e.target.value)} style={{ flex: 1 }} />
                                        <input type="text" placeholder="Canned response..." value={blResponse} onChange={e => setBlResponse(e.target.value)} style={{ flex: 1 }} />
                                        <button className="admin-btn" onClick={addBlacklistRule}>Add</button>
                                    </div>
                                    <div style={{ maxHeight: 90, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: 6, marginBottom: 12, background: 'white' }}>
                                        <table className="rules-table" style={{ margin: 0 }}>
                                            <thead>
                                                <tr>
                                                    <th>Blocked Pattern</th>
                                                    <th>Blocked Response</th>
                                                    <th style={{ width: 40, textAlign: 'center' }}>Act</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {adminConfig?.blacklist_rules && adminConfig.blacklist_rules.length > 0 ? (
                                                    adminConfig.blacklist_rules.map((rule, i) => (
                                                        <tr key={i}>
                                                            <td><code>{rule.pattern}</code></td>
                                                            <td>{rule.response}</td>
                                                            <td style={{ textAlign: 'center' }}>
                                                                <button className="admin-btn danger" style={{ padding: '2px 6px', fontSize: 9 }} onClick={() => deleteBlacklistRule(i)}>Del</button>
                                                            </td>
                                                        </tr>
                                                    ))
                                                ) : (
                                                    <tr><td colSpan="3" style={{ textAlign: 'center', color: '#64748b' }}>No blacklist rules.</td></tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>

                                    {/* Protected Terms Glossary */}
                                    <div className="cg-admin-section-title">🔤 Glossary Term Protection</div>
                                    <div className="admin-form-group" style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
                                        <input type="text" placeholder="Preserved term..." value={glossaryTerm} onChange={e => setGlossaryTerm(e.target.value)} style={{ flex: 1 }} />
                                        <button className="admin-btn" onClick={addGlossaryTerm}>Add</button>
                                    </div>
                                    <div style={{ maxHeight: 90, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: 6, marginBottom: 12, background: 'white' }}>
                                        <table className="rules-table" style={{ margin: 0 }}>
                                            <thead>
                                                <tr>
                                                    <th>Preserved Abbreviations / Terms</th>
                                                    <th style={{ width: 40, textAlign: 'center' }}>Act</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {adminConfig?.protected_terms && adminConfig.protected_terms.length > 0 ? (
                                                    adminConfig.protected_terms.map((term, i) => (
                                                        <tr key={i}>
                                                            <td>{term}</td>
                                                            <td style={{ textAlign: 'center' }}>
                                                                <button className="admin-btn danger" style={{ padding: '2px 6px', fontSize: 9 }} onClick={() => deleteGlossaryTerm(i)}>Del</button>
                                                            </td>
                                                        </tr>
                                                    ))
                                                ) : (
                                                    <tr><td colSpan="2" style={{ textAlign: 'center', color: '#64748b' }}>No glossary terms.</td></tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>

                                </div>
                            )}

                            {/* Tab 6: Hallucination Review Cockpit */}
                            {adminTab === 'hallucination' && (
                                <div className="admin-tab-content active">
                                    <div className="cg-admin-section-title">👎 Hallucination Review Cockpit</div>
                                    <p style={{ fontSize: 9, color: '#64748b', marginTop: 0, marginBottom: 8 }}>
                                        Review user queries flagged with unsatisfied (thumbs-down) feedback and submit corrected answers. Corrected answers are saved as instant FAQ overrides, ensuring the chatbot learns the right response immediately.
                                    </p>
                                    <div style={{ maxHeight: 320, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: 6, marginBottom: 8, background: 'white', padding: 10 }}>
                                        {unsatisfiedQueries && unsatisfiedQueries.length > 0 ? (
                                            unsatisfiedQueries.map((q, i) => {
                                                const existingCorrection = 
                                                    (adminConfig?.hallucination_corrections || []).find(hc => hc.query.toLowerCase() === q.query.toLowerCase())?.answer ||
                                                    (adminConfig?.qa_overrides || []).find(qa => qa.query.toLowerCase() === q.query.toLowerCase())?.answer;
                                                const isCorrected = !!existingCorrection;

                                                return (
                                                    <div key={i} style={{ borderBottom: '1px solid #f1f5f9', padding: '10px 0', marginBottom: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                            <span style={{ fontSize: 11, fontWeight: 700, color: '#1e293b' }}>Query: "{q.query}"</span>
                                                            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                                                                {isCorrected ? (
                                                                    <span style={{ fontSize: 9, background: '#dcfce7', color: '#166534', padding: '2px 6px', borderRadius: 4, fontWeight: 600 }}>✅ Corrected</span>
                                                                ) : (
                                                                    <span style={{ fontSize: 9, background: '#fee2e2', color: '#991b1b', padding: '2px 6px', borderRadius: 4, fontWeight: 600 }}>⚠️ Pending</span>
                                                                )}
                                                                <span style={{ fontSize: 9, color: '#64748b' }}>Logged: {q.timestamp ? new Date(q.timestamp).toLocaleString() : ''}</span>
                                                            </div>
                                                        </div>
                                                        <div style={{ fontSize: 10, background: '#f8f9fa', padding: '6px 8px', borderRadius: 4, color: '#475569', borderLeft: '3px solid #ef4444' }}>
                                                            <strong>Original Hallucinated Answer:</strong> {q.response || '(No response text logged)'}
                                                        </div>
                                                        {isCorrected && (
                                                            <div style={{ fontSize: 10, background: '#f0fdf4', padding: '6px 8px', borderRadius: 4, color: '#166534', borderLeft: '3px solid #22c55e' }}>
                                                                <strong>Current Corrected Answer (Active Override):</strong> {existingCorrection}
                                                            </div>
                                                        )}
                                                         <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4, width: '100%' }}>
                                                             <textarea
                                                                 value={corrections[q.query] || ''}
                                                                 onChange={e => {
                                                                     const val = e.target.value;
                                                                     setCorrections(prev => ({ ...prev, [q.query]: val }));
                                                                 }}
                                                                 placeholder={isCorrected ? "Update corrected answer..." : "Type correct verified answer here..."}
                                                                 style={{ width: '100%', minHeight: '60px', fontSize: '10px', padding: '6px 8px', border: '1px solid #cbd5e1', borderRadius: 4, fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box', outline: 'none' }}
                                                             ></textarea>
                                                             <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                                                                 {isCorrected && (
                                                                     <button className="admin-btn danger" style={{ padding: '6px 12px', fontSize: 10 }} onClick={() => deleteHallucinationCorrection(q.query)}>
                                                                         Delete Correction
                                                                     </button>
                                                                 )}
                                                                 <button className="admin-btn" style={{ padding: '6px 12px', fontSize: 10 }} onClick={() => applyHallucinationCorrection(q.query)}>
                                                                     {isCorrected ? "Update Correction" : "Submit Correction"}
                                                                 </button>
                                                             </div>
                                                         </div>
                                                    </div>
                                                );
                                            })
                                        ) : (
                                            <div style={{ fontSize: 11, color: '#64748b', textAlign: 'center', padding: '20px 0' }}>No unsatisfied queries found to review.</div>
                                        )}
                                    </div>
                                </div>
                            )}

                        </div>
                    )}
                    </div>{/* /cg-chat-main-panel */}

                    {showPdf && (
                        <div className="cg-pdf-viewer-panel" ref={pdfContainerRef}>
                            <div className="cg-pdf-header">
                                <span className="cg-pdf-title">{pdfTitle}</span>
                                <button className="cg-pdf-close-btn" onClick={closePdfViewer} title="Close Viewer">×</button>
                            </div>
                            <div className="cg-pdf-toolbar">
                                <div className="cg-pdf-tb-group">
                                    <button className="cg-pdf-btn" onClick={handlePrevPage} disabled={pdfPage <= 1} title="Previous Page">◀ Prev</button>
                                    <span style={{ fontSize: 11, color: '#475569', fontWeight: 500 }}>Page:</span>
                                    <input 
                                        type="number" 
                                        value={pdfPage} 
                                        min="1" 
                                        max={pdfPageCount}
                                        onChange={(e) => handleGoToPageFromInput(e.target.value)} 
                                        style={{ width: 45, textAlign: 'center', fontSize: 11, padding: '2px 4px', border: '1px solid #cbd5e1', borderRadius: 4 }}
                                    />
                                    <span style={{ fontSize: 11, color: '#64748b' }}>/ {pdfPageCount}</span>
                                    <button className="cg-pdf-btn" onClick={handleNextPage} disabled={pdfPage >= pdfPageCount} title="Next Page">Next ▶</button>
                                </div>
                                <div className="cg-pdf-tb-group">
                                    <button className="cg-pdf-btn" onClick={handleZoomOut} disabled={typeof pdfScale === 'number' && pdfScale <= 0.5} title="Zoom Out">➖</button>
                                    <span style={{ fontSize: 11, color: '#475569', fontWeight: 500 }}>
                                        {pdfScale === 'fit' ? 'Fit' : `${Math.round(pdfScale * 100)}%`}
                                    </span>
                                    <button className="cg-pdf-btn" onClick={handleZoomIn} disabled={typeof pdfScale === 'number' && pdfScale >= 3.0} title="Zoom In">➕</button>
                                    <button className="cg-pdf-btn" onClick={handleZoomFit} title="Fit Width">Fit Width</button>
                                </div>
                                <div className="cg-pdf-tb-group" style={{ flex: 1, minWidth: 140, display: 'flex', justifyContent: 'flex-end', gap: 4 }}>
                                    <input 
                                        type="text" 
                                        value={pdfSearchText} 
                                        onChange={(e) => handlePdfSearchChange(e.target.value)} 
                                        placeholder="Highlight rule/text..." 
                                        style={{ fontSize: 11, padding: '4px 8px', border: '1px solid #cbd5e1', borderRadius: 4, flexGrow: 1, maxWidth: 180 }}
                                    />
                                </div>
                            </div>
                            <div className="cg-pdf-canvas-container">
                                <canvas ref={pdfCanvasRef} className="cg-pdf-canvas"></canvas>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ChatWidget;