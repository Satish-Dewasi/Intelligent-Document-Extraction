import { useEffect, useMemo, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

const DOCUMENT_TYPES = [
  { value: "invoice", label: "Invoice" },
  { value: "balance_sheet", label: "Balance Sheet" },
  { value: "profit_and_loss", label: "Profit & Loss" },
  { value: "cash_flow", label: "Cash Flow" },
];

function formatDocumentType(type) {
  return (
    DOCUMENT_TYPES.find((item) => item.value === type)?.label ||
    type?.replaceAll("_", " ") ||
    "Unknown"
  );
}

function formatDate(value) {
  if (!value) return "—";

  return new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  return String(value);
}

function StatusBadge({ status }) {
  const normalized = String(status || "").toUpperCase();

  const classes =
    normalized === "PASS"
      ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
      : normalized === "FAIL"
        ? "bg-red-50 text-red-700 ring-red-600/20"
        : normalized === "NOT_APPLICABLE"
          ? "bg-slate-100 text-slate-600 ring-slate-500/20"
          : "bg-amber-50 text-amber-700 ring-amber-600/20";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium capitalize ring-1 ring-inset ${classes}`}
    >
      {normalized.replaceAll("_", " ")}
    </span>
  );
}

function EmptyState({ title, description }) {
  return (
    <div className="flex min-h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
          <path
            d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
            stroke="currentColor"
            strokeWidth="1.7"
          />
          <path
            d="M14 3v6h6M9 13h6M9 17h6"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
          />
        </svg>
      </div>

      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>
    </div>
  );
}

function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);

  const [documentType, setDocumentType] = useState("invoice");
  const [file, setFile] = useState(null);

  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [processing, setProcessing] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [search, setSearch] = useState("");

  const fetchDocuments = async () => {
    try {
      setLoadingDocuments(true);
      setError("");

      const response = await fetch(`${API_BASE_URL}/documents`);

      if (!response.ok) {
        throw new Error("Unable to load processed documents.");
      }

      const data = await response.json();
      setDocuments(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Unable to load documents.");
    } finally {
      setLoadingDocuments(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileChange = (event) => {
    const selected = event.target.files?.[0] || null;

    setFile(selected);
    setError("");
    setSuccess("");
  };

  const handleProcess = async (event) => {
    event.preventDefault();

    if (!file) {
      setError("Please select a PDF, JPG, or PNG document.");
      return;
    }

    try {
      setProcessing(true);
      setError("");
      setSuccess("");

      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", documentType);

      const response = await fetch(`${API_BASE_URL}/documents/process`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        const detail =
          typeof data?.detail === "string"
            ? data.detail
            : data?.detail?.message || "Document processing failed.";

        throw new Error(detail);
      }

      setSuccess("Document processed successfully.");
      setFile(null);

      const fileInput = document.getElementById("document-file");
      if (fileInput) {
        fileInput.value = "";
      }

      await fetchDocuments();

      if (data?.structured_extraction) {
        setSelectedDocument({
          document_name: file.name,
          document_type: documentType,
          processing_status: data.financial_validation?.checks?.some(
            (check) => check.status === "FAIL",
          )
            ? "FAIL"
            : "PASS",
          processed_at: new Date().toISOString(),
          processing_time_ms: data.processing_time_ms,
          result: {
            extraction: data.structured_extraction,
            financial_validation: data.financial_validation,
          },
        });
      }
    } catch (err) {
      setError(err.message || "Document processing failed.");
    } finally {
      setProcessing(false);
    }
  };

  const filteredDocuments = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return documents;
    }

    return documents.filter((document) =>
      document.document_name?.toLowerCase().includes(query),
    );
  }, [documents, search]);

  const passedCount = documents.filter(
    (document) => document.processing_status === "PASS",
  ).length;

  const failedCount = documents.filter(
    (document) => document.processing_status === "FAIL",
  ).length;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-8">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-sm font-bold text-white">
                N
              </div>

              <div>
                <h1 className="text-lg font-semibold tracking-tight">
                  NeoStats
                </h1>
                <p className="text-xs text-slate-500">
                  Intelligent document analysis
                </p>
              </div>
            </div>
          </div>

          <a
            href={`${API_BASE_URL.replace("/api/v1", "")}/docs`}
            target="_blank"
            rel="noreferrer"
            className="hidden text-sm font-medium text-slate-500 transition hover:text-slate-900 sm:block"
          >
            API Docs →
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
          {/* Upload */}
          <section className="h-fit rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-6">
              <h2 className="text-base font-semibold">Process document</h2>
              <p className="mt-1 text-sm text-slate-500">
                Upload a financial document for extraction and validation.
              </p>
            </div>

            <form onSubmit={handleProcess} className="space-y-5">
              <div>
                <label
                  htmlFor="document-type"
                  className="mb-2 block text-sm font-medium text-slate-700"
                >
                  Document type
                </label>

                <select
                  id="document-type"
                  value={documentType}
                  onChange={(event) => setDocumentType(event.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                >
                  {DOCUMENT_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="document-file"
                  className="mb-2 block text-sm font-medium text-slate-700"
                >
                  Document
                </label>

                <label
                  htmlFor="document-file"
                  className="flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center transition hover:border-slate-400 hover:bg-slate-100"
                >
                  <svg
                    width="25"
                    height="25"
                    viewBox="0 0 24 24"
                    fill="none"
                    className="mb-3 text-slate-400"
                  >
                    <path
                      d="M12 16V4m0 0L8 8m4-4 4 4"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M5 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />
                  </svg>

                  <span className="text-sm font-medium text-slate-700">
                    {file ? file.name : "Choose a document"}
                  </span>

                  <span className="mt-1 text-xs text-slate-400">
                    PDF, JPG or PNG · Maximum 3 pages
                  </span>

                  <input
                    id="document-file"
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
              </div>

              {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              {success && (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                  {success}
                </div>
              )}

              <button
                type="submit"
                disabled={processing}
                className="w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {processing ? "Processing..." : "Process document"}
              </button>
            </form>
          </section>

          {/* Documents */}
          <section>
            <div className="mb-5 grid grid-cols-3 gap-3">
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Total
                </p>
                <p className="mt-1 text-2xl font-semibold">
                  {documents.length}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Passed
                </p>
                <p className="mt-1 text-2xl font-semibold text-emerald-600">
                  {passedCount}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Failed
                </p>
                <p className="mt-1 text-2xl font-semibold text-red-600">
                  {failedCount}
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
              <div className="flex flex-col gap-4 border-b border-slate-200 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="font-semibold">Processed documents</h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Select a document to inspect its results.
                  </p>
                </div>

                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search documents..."
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200 sm:w-56"
                />
              </div>

              {loadingDocuments ? (
                <div className="p-10 text-center text-sm text-slate-500">
                  Loading documents...
                </div>
              ) : filteredDocuments.length === 0 ? (
                <div className="p-5">
                  <EmptyState
                    title="No documents found"
                    description="Processed documents will appear here."
                  />
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {filteredDocuments.map((document) => (
                    <button
                      key={document.id}
                      type="button"
                      onClick={() => setSelectedDocument(document)}
                      className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition hover:bg-slate-50"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-slate-900">
                          {document.document_name}
                        </p>

                        <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                          <span>
                            {formatDocumentType(document.document_type)}
                          </span>
                          <span>·</span>
                          <span>{formatDate(document.processed_at)}</span>
                        </div>
                      </div>

                      <div className="flex shrink-0 items-center gap-3">
                        <StatusBadge status={document.processing_status} />

                        <svg
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="none"
                          className="text-slate-400"
                        >
                          <path
                            d="m9 18 6-6-6-6"
                            stroke="currentColor"
                            strokeWidth="1.8"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </section>
        </div>
      </main>

      {/* Detail modal */}
      {selectedDocument && (
        <DocumentDetails
          document={selectedDocument}
          onClose={() => setSelectedDocument(null)}
        />
      )}
    </div>
  );
}

function DocumentDetails({ document, onClose }) {
  const result = document.result || {};
  const extraction = result.extraction || {};
  const validation = result.financial_validation || {};

  const fields = extraction.fields || [];
  const tables = extraction.tables || [];
  const checks = validation.checks || [];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/40 p-4 backdrop-blur-sm sm:p-8">
      <div className="mx-auto max-w-5xl rounded-2xl bg-white shadow-2xl">
        <div className="sticky top-0 z-10 flex items-start justify-between gap-5 rounded-t-2xl border-b border-slate-200 bg-white px-6 py-5">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="truncate text-lg font-semibold">
                {document.document_name}
              </h2>

              <StatusBadge status={document.processing_status} />
            </div>

            <p className="mt-1 text-sm text-slate-500">
              {formatDocumentType(document.document_type)} ·{" "}
              {formatDate(document.processed_at)}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path
                d="M6 6l12 12M18 6 6 18"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        <div className="space-y-8 p-6">
          {/* Summary */}
          <section>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Document type
                </p>
                <p className="mt-1 text-sm font-semibold">
                  {formatDocumentType(document.document_type)}
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Processing status
                </p>
                <div className="mt-2">
                  <StatusBadge status={document.processing_status} />
                </div>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Processing time
                </p>
                <p className="mt-1 text-sm font-semibold">
                  {document.processing_time_ms != null
                    ? `${Number(document.processing_time_ms).toFixed(0)} ms`
                    : "—"}
                </p>
              </div>
            </div>
          </section>

          {/* Fields */}
          <section>
            <div className="mb-4">
              <h3 className="text-sm font-semibold">Extracted fields</h3>
              <p className="mt-1 text-xs text-slate-500">
                Values extracted from the document with supporting evidence.
              </p>
            </div>

            {fields.length === 0 ? (
              <EmptyState
                title="No fields extracted"
                description="No structured fields were returned for this document."
              />
            ) : (
              <div className="overflow-hidden rounded-xl border border-slate-200">
                <div className="grid grid-cols-[1fr_1fr_auto] gap-4 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-medium uppercase tracking-wide text-slate-500">
                  <span>Field</span>
                  <span>Value</span>
                  <span>Page</span>
                </div>

                <div className="divide-y divide-slate-100">
                  {fields.map((field, index) => {
                    const value = field.value || {};

                    const extractedValue =
                      value.text ?? value.number ?? value.boolean;

                    return (
                      <div
                        key={`${field.name}-${index}`}
                        className="grid gap-3 px-4 py-4 sm:grid-cols-[1fr_1fr_auto]"
                      >
                        <div>
                          <p className="text-sm font-medium text-slate-800">
                            {field.name?.replaceAll("_", " ")}
                          </p>

                          {field.evidence && (
                            <p className="mt-1 text-xs leading-5 text-slate-400">
                              “{field.evidence}”
                            </p>
                          )}
                        </div>

                        <div>
                          <p className="break-words text-sm text-slate-700">
                            {formatValue(extractedValue)}
                          </p>

                          {field.confidence != null && (
                            <p className="mt-1 text-xs text-slate-400">
                              Confidence: {(field.confidence * 100).toFixed(0)}%
                            </p>
                          )}
                        </div>

                        <div className="text-xs text-slate-500">
                          Page {field.page_number ?? "—"}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </section>

          {/* Tables */}
          <section>
            <div className="mb-4">
              <h3 className="text-sm font-semibold">Extracted tables</h3>
            </div>

            {tables.length === 0 ? (
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-500">
                No tables extracted.
              </div>
            ) : (
              <div className="space-y-5">
                {tables.map((table, tableIndex) => (
                  <div
                    key={`${table.name}-${tableIndex}`}
                    className="overflow-x-auto rounded-xl border border-slate-200"
                  >
                    <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
                      <div className="flex items-center justify-between gap-4">
                        <p className="text-sm font-semibold">{table.name}</p>
                        <p className="text-xs text-slate-400">
                          Page {table.page_number ?? "—"}
                        </p>
                      </div>
                    </div>

                    <table className="w-full min-w-max text-left text-sm">
                      <thead className="border-b border-slate-200">
                        <tr>
                          {(table.columns || []).map((column, index) => (
                            <th
                              key={`${column}-${index}`}
                              className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-slate-500"
                            >
                              {column}
                            </th>
                          ))}
                        </tr>
                      </thead>

                      <tbody className="divide-y divide-slate-100">
                        {(table.rows || []).map((row, rowIndex) => (
                          <tr key={rowIndex}>
                            {row.map((cell, cellIndex) => (
                              <td
                                key={cellIndex}
                                className="px-4 py-3 text-slate-700"
                              >
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Validation */}
          <section>
            <div className="mb-4">
              <h3 className="text-sm font-semibold">Financial validation</h3>
              <p className="mt-1 text-xs text-slate-500">
                Deterministic financial checks performed by NeoStats.
              </p>
            </div>

            {checks.length === 0 ? (
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-500">
                No financial checks were applicable.
              </div>
            ) : (
              <div className="space-y-3">
                {checks.map((check, index) => (
                  <div
                    key={`${check.name}-${index}`}
                    className="rounded-xl border border-slate-200 p-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-slate-800">
                          {check.name}
                        </p>

                        {check.formula && (
                          <code className="mt-1 block text-xs text-slate-500">
                            {check.formula}
                          </code>
                        )}
                      </div>

                      <StatusBadge status={check.status} />
                    </div>

                    <div className="mt-4 grid gap-3 sm:grid-cols-4">
                      <div>
                        <p className="text-xs text-slate-400">Calculated</p>
                        <p className="mt-1 text-sm font-medium">
                          {formatValue(check.calculated_value)}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-400">Reported</p>
                        <p className="mt-1 text-sm font-medium">
                          {formatValue(check.reported_value)}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-400">Variance</p>
                        <p className="mt-1 text-sm font-medium">
                          {formatValue(check.variance)}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-400">Operands</p>
                        <p className="mt-1 break-words text-xs text-slate-600">
                          {check.operands
                            ? Object.entries(check.operands)
                                .map(([key, value]) => `${key}: ${value}`)
                                .join(", ")
                            : "—"}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Raw JSON */}
          <section>
            <details className="group rounded-xl border border-slate-200">
              <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-slate-700">
                <span className="flex items-center justify-between">
                  Raw JSON
                  <span className="text-slate-400 transition group-open:rotate-180">
                    ↓
                  </span>
                </span>
              </summary>

              <pre className="max-h-96 overflow-auto border-t border-slate-200 bg-slate-950 p-4 text-xs leading-6 text-slate-200">
                {JSON.stringify(document, null, 2)}
              </pre>
            </details>
          </section>
        </div>
      </div>
    </div>
  );
}

export default App;
