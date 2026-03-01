"use client";

import { useRef, useState } from "react";
import Button from "./Button";

interface FilePickerProps {
  onFileSelected: (file: File) => void;
  accept?: string;
  label?: string;
  uploading?: boolean;
}

export default function FilePicker({
  onFileSelected,
  accept,
  label = "Choisir un fichier",
  uploading = false,
}: FilePickerProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = (file: File) => {
    setFileName(file.name);
    onFileSelected(file);
  };

  return (
    <div className="space-y-2">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      <div
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
          dragOver
            ? "border-primary bg-primary-50"
            : "border-gray-300 hover:border-primary/50 hover:bg-gray-50"
        }`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
      >
        {uploading ? (
          <div className="flex flex-col items-center gap-2 text-primary">
            <span className="material-symbols-outlined animate-spin icon-lg">progress_activity</span>
            <span className="text-sm font-medium">Envoi en cours...</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-gray-400">
            <span className="material-symbols-outlined icon-lg">upload_file</span>
            <span className="text-sm font-medium">{label}</span>
            {fileName && <span className="text-xs text-gray-500">{fileName}</span>}
          </div>
        )}
      </div>
    </div>
  );
}
