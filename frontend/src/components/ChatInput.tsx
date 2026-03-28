import { useState, useRef, useEffect, useMemo } from "react";
import { Send, FolderOpen, X } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

function detectFilter(text: string): string | null {
  const match = text.match(/"([^"]+)"/);
  return match ? match[1] : null;
}

const ChatInput = ({ onSend, disabled }: ChatInputProps) => {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const detectedFilter = useMemo(() => detectFilter(value), [value]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + "px";
    }
  }, [value]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const removeFilter = () => {
    setValue((prev) => prev.replace(/"[^"]*"/, "").trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-border bg-card/80 backdrop-blur-sm p-4">
      <div className="max-w-3xl mx-auto space-y-2">
        {detectedFilter && (
          <div className="flex items-center gap-1.5 px-1">
            <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg bg-primary/15 text-primary border border-primary/20">
              <FolderOpen className="w-3 h-3" />
              {detectedFilter}
              <button onClick={removeFilter} className="ml-0.5 hover:text-primary/70 transition-colors">
                <X className="w-3 h-3" />
              </button>
            </span>
            <span className="text-[11px] text-muted-foreground">Folder filter detected</span>
          </div>
        )}
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder='Ask a question... (e.g. What is leave policy? "hr_policy")'
              disabled={disabled}
              rows={1}
              className="w-full resize-none rounded-xl bg-secondary border border-border px-4 py-3 pr-12 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all disabled:opacity-50 scrollbar-thin"
            />
          </div>
          <button
            onClick={handleSubmit}
            disabled={disabled || !value.trim()}
            className="flex-shrink-0 w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
