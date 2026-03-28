import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { User, Bot, FolderOpen } from "lucide-react";

interface Source {
  name: string;
}

interface ChatMessageProps {
  role: "user" | "ai";
  content: string;
  sources?: Source[];
  filter?: string;
}

const ChatMessage = ({ role, content, sources, filter }: ChatMessageProps) => {
  const isUser = role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex gap-3 px-4 py-3 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center mt-1">
          <Bot className="w-4 h-4 text-primary" />
        </div>
      )}

      <div className={`max-w-[75%] space-y-2`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-chat-user text-chat-user-foreground rounded-br-md"
              : "bg-chat-ai text-chat-ai-foreground rounded-bl-md"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <div className="prose prose-sm prose-invert max-w-none [&_p]:mb-2 [&_ul]:mb-2 [&_li]:mb-0.5">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          )}
        </div>

        {filter && isUser && (
          <div className="flex justify-end">
            <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-secondary text-muted-foreground">
              <FolderOpen className="w-3 h-3" />
              {filter}
            </span>
          </div>
        )}

        {sources && sources.length > 0 && !isUser && (
          <div className="px-1">
            <p className="text-xs text-muted-foreground mb-1">Sources:</p>
            <div className="flex flex-wrap gap-1.5">
              {sources.map((s, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-1 rounded-md bg-secondary text-muted-foreground"
                >
                  📄 {s.name}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-chat-user/20 flex items-center justify-center mt-1">
          <User className="w-4 h-4 text-chat-user" />
        </div>
      )}
    </motion.div>
  );
};

export default ChatMessage;
