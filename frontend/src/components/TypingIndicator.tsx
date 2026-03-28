import { motion } from "framer-motion";
import { Bot } from "lucide-react";

const TypingIndicator = () => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    className="flex gap-3 px-4 py-3"
  >
    <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
      <Bot className="w-4 h-4 text-primary" />
    </div>
    <div className="bg-chat-ai rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-1.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 rounded-full bg-muted-foreground animate-pulse-dot"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
      <span className="text-xs text-muted-foreground ml-2">Analyzing documents…</span>
    </div>
  </motion.div>
);

export default TypingIndicator;
